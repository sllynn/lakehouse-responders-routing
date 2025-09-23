# Databricks notebook source
# MAGIC %pip install databricks-sdk==0.65.0 psycopg2 sqlmodel==0.0.25
# MAGIC %restart_python

# COMMAND ----------

import psycopg2
import uuid

from datetime import datetime
from enum import Enum

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.database import DatabaseInstance
from databricks.sdk.errors.platform import NotFound
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlmodel import Field, Session, SQLModel, create_engine, select, LargeBinary, Column, MetaData
import sqlalchemy as sa


w = WorkspaceClient()

# COMMAND ----------

instance_name = "lakehouse-first-responders"

instance = DatabaseInstance(
  name=instance_name,
  enable_pg_native_login=True,
  capacity="CU_2"
)

# COMMAND ----------

try:
  instance_details = w.database.get_database_instance(instance_name)
except NotFound:
  instance_details = w.database.create_database_instance_and_wait(instance)

# COMMAND ----------

cred = w.database.generate_database_credential(instance_names=[instance_details.name], request_id=uuid.uuid4().hex)

# COMMAND ----------

database_name = "responders"
new_user = f"user_{uuid.uuid4().hex[:8]}"
new_password = uuid.uuid4().hex

# COMMAND ----------

conn = psycopg2.connect(
    host=instance_details.read_write_dns,
    dbname="databricks_postgres",
    user=w.current_user.me().user_name,
    password=cred.token,
    sslmode="require",
)

conn.autocommit = True

# COMMAND ----------

with conn.cursor() as cur:
    create_role_sql = f"""DO $$
BEGIN
CREATE ROLE {new_user} WITH LOGIN CREATEDB PASSWORD '{new_password}';
EXCEPTION WHEN duplicate_object THEN RAISE NOTICE '%, skipping', SQLERRM USING ERRCODE = SQLSTATE;
END
$$;"""
    cur.execute(create_role_sql)
    conn.commit()

print(f"Created user: {new_user}\nPassword: {new_password}")

# COMMAND ----------

# conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

kick_them_out = """SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '{}'
  AND pid <> pg_backend_pid();"""

with conn.cursor() as cur:
    db_identifier = sql.Identifier(database_name)
    cur.execute(sql.SQL(kick_them_out.format(database_name)))
    cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(db_identifier))
    cur.execute(sql.SQL("CREATE DATABASE {}").format(db_identifier))

# COMMAND ----------

with conn.cursor() as cur:
    cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {database_name} TO {new_user};")

# COMMAND ----------

conn.close()

# COMMAND ----------

conn = psycopg2.connect(
    host=instance_details.read_write_dns,
    dbname=database_name,
    user=w.current_user.me().user_name,
    password=cred.token,
    sslmode="require",
)

conn.autocommit = True

# COMMAND ----------

with conn.cursor() as cur:
    cur.execute(f"GRANT ALL ON SCHEMA public TO {new_user};")

# COMMAND ----------

conn.close()

# COMMAND ----------

# dbutils.jobs.taskValues.set(key="DB_URL", value=engine.url)
dbutils.jobs.taskValues.set(key="DB_USER", value=new_user)
dbutils.jobs.taskValues.set(key="DB_PASSWORD", value=new_password)
dbutils.jobs.taskValues.set(key="DB_HOST", value=instance_details.read_write_dns)
dbutils.jobs.taskValues.set(key="DB_NAME", value=database_name)

# COMMAND ----------

dbutils.notebook.exit("0")