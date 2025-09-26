from databricks.bundles.jobs import Job
import datetime

"""
The main job for routing_engine.
"""


routing_engine_job = Job.from_dict({
    'name': 'Routing engine',
    'permissions': [
      {
        'user_name': 'stuart.lynn@databricks.com',
        'level': 'CAN_MANAGE'
      },
      {
        'user_name': 'matt.slack@databricks.com',
        'level': 'CAN_MANAGE'
      },
      {
        'user_name': 'sahil.grover@databricks.com',
        'level': 'CAN_MANAGE'
      },
      {
        'user_name': 'timo.roest@databricks.com',
        'level': 'CAN_MANAGE'
      },
      {
        'user_name': 'rich.li@databricks.com',
        'level': 'CAN_MANAGE'
      },
    ],
    'tasks': [
     {'task_key': 'build_valhalla',
      'notebook_task': {'notebook_path': './src/valhalla/install-valhalla.py',
       'base_parameters': {'VOLUME_PATH': '/Volumes/{{job.parameters.CATALOG}}/{{job.parameters.SCHEMA}}/{{job.parameters.VOLUME}}'},
       'source': 'WORKSPACE'},
      'existing_cluster_id': '0905-131122-v6vl4ob1'},
     {'task_key': 'ingest_osm_pbf',
      'depends_on': [{'task_key': 'build_valhalla'}],
      'notebook_task': {'notebook_path': './src/valhalla/populate-graph.py',
       'base_parameters': {'VOLUME_PATH': '/Volumes/{{job.parameters.CATALOG}}//{{job.parameters.SCHEMA}}/{{job.parameters.VOLUME}}'},
       'source': 'WORKSPACE'},
      'existing_cluster_id': '0905-131122-v6vl4ob1'},
     {'task_key': 'build_entities',
       'notebook_task': {'notebook_path': './src/lakebase/scripts/build_entities.py',
       'base_parameters': {'VOLUME_PATH': '/Volumes/{{job.parameters.CATALOG}}/{{job.parameters.SCHEMA}}/{{job.parameters.VOLUME}}'},
        'source': 'WORKSPACE'}},
     {'task_key': 'initialise_db',
      'depends_on': [{'task_key': 'build_entities'}],
      'notebook_task': {'notebook_path': './src/lakebase/initialise.py',
       'source': 'WORKSPACE'}},
     {'task_key': 'populate_db',
      'depends_on': [{'task_key': 'initialise_db'}],
      'notebook_task': {'notebook_path': './src/lakebase/populate.py',
       'base_parameters': {'DB_HOST': '{{tasks.initialise_db.values.DB_HOST}}',
        'DB_NAME': '{{tasks.initialise_db.values.DB_NAME}}',
        'DB_USER': '{{tasks.initialise_db.values.DB_USER}}',
        'DB_PASSWORD': '{{tasks.initialise_db.values.DB_PASSWORD}}',
        'VOLUME_PATH': '/Volumes/{{job.parameters.CATALOG}}/{{job.parameters.SCHEMA}}/{{job.parameters.VOLUME}}'},
       'source': 'WORKSPACE'}},
     {'task_key': 'fat_controller',
      'depends_on': [{'task_key': 'populate_db'},
       {'task_key': 'ingest_osm_pbf'}],
      'notebook_task': {'notebook_path': './src/main.py',
       'base_parameters': {'DB_URL': '{{tasks.populate_db.values.DB_URL}}',
        'VOLUME_PATH': '/Volumes/{{job.parameters.CATALOG}}/{{job.parameters.SCHEMA}}/{{job.parameters.VOLUME}}'},
       'source': 'WORKSPACE'},
      'existing_cluster_id': '0905-131122-v6vl4ob1'}],
    'tags': {'removeAfter': datetime.date(2025, 10, 30)},
    'queue': {'enabled': True},
    'parameters': [{'name': 'CATALOG', 'default': 'users'},
     {'name': 'PBF_URL',
      'default': 'https://download.geofabrik.de/europe/germany/berlin-latest.osm.pbf'},
     {'name': 'SCHEMA', 'default': 'stuart_lynn'},
     {'name': 'VOLUME', 'default': 'valhalla_berlin'}],
    'performance_target': 'PERFORMANCE_OPTIMIZED'
})
