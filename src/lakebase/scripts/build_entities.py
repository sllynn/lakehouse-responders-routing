# Databricks notebook source
# MAGIC %md
# MAGIC # Build Entities Package
# MAGIC 
# MAGIC This notebook builds the lakebase-responders-entities package from source and uploads it to the volume for use by other tasks.

# COMMAND ----------

# DBTITLE 1,Install Build Dependencies
# MAGIC %pip install build
# MAGIC %restart_python

# COMMAND ----------

# DBTITLE 1,Set Parameters
VOLUME_PATH = dbutils.widgets.get("VOLUME_PATH")

# COMMAND ----------

# DBTITLE 1,Build Entities Package
import subprocess
import shutil
from pathlib import Path
import os

# Change to entities directory
entities_dir = Path("/Workspace/Repos/*/routing_engine/src/lakebase/entities")
if not entities_dir.exists():
    # Fallback to local path structure
    entities_dir = Path("../entities")

os.chdir(str(entities_dir))
print(f"Building entities package in: {entities_dir.absolute()}")

# Clean previous build
if Path("build").exists():
    shutil.rmtree("build")
if Path("dist").exists():
    shutil.rmtree("dist")

# Build the package
result = subprocess.run(["python", "-m", "build"], capture_output=True, text=True)
print("Build output:", result.stdout)
if result.stderr:
    print("Build errors:", result.stderr)

if result.returncode != 0:
    raise Exception(f"Build failed with return code {result.returncode}")

# COMMAND ----------

# DBTITLE 1,Upload to Volume
import shutil
from pathlib import Path

# Create entities directory in volume
volume_entities_path = Path(f"{VOLUME_PATH}/entities")
volume_entities_path.mkdir(parents=True, exist_ok=True)

# Copy wheel files to volume
dist_path = Path("dist")
wheel_files = list(dist_path.glob("*.whl"))

if not wheel_files:
    raise Exception("No wheel files found after build")

for wheel_file in wheel_files:
    destination = volume_entities_path / wheel_file.name
    shutil.copy2(wheel_file, destination)
    print(f"Uploaded: {wheel_file.name} -> {destination}")

print("Entities package build and upload complete!")

# COMMAND ----------

dbutils.notebook.exit("0")
