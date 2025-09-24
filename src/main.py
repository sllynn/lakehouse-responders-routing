# Databricks notebook source
# MAGIC %pip install --upgrade protobuf ortools sqlmodel==0.0.25 geopandas==1.1.1 numpy>=2
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

import warnings
warnings.filterwarnings("ignore")

# COMMAND ----------

volume_path = dbutils.widgets.get("VOLUME_PATH")

# COMMAND ----------

from pathlib import Path
whl_path = str(max(Path(f"{volume_path}/whl").glob("*.whl"), key=lambda f: f.stat().st_mtime))

# COMMAND ----------

# MAGIC %pip install {whl_path}

# COMMAND ----------

# MAGIC %pip install {volume_path}/entities/lakebase_responders_entities*.whl

# COMMAND ----------

import time
from data import DataManager
from routing import RoutingService
from optimizer import RouteOptimizer
from plan_processor import PlanProcessor

# COMMAND ----------

# --- Configuration ---
TICK_INTERVAL_SECONDS = 0  # How often to re-plan
DISTANCE_PER_TICK_M = 200
OPTIMIZATION_GOAL = "time"  # or "distance"
VRP_TIMEOUT_S = 5
VALHALLA_CONFIG_PATH = f"{volume_path}/tiles/valhalla.json"
DB_URL = dbutils.widgets.get("DB_URL")

# COMMAND ----------

def run_simulation_tick(data_manager, routing_service):
    """
    Executes a single iteration of the simulation.
    """
    print("\n--- Starting new simulation tick ---")
    
    # 1. Fetch current state from the database
    emergencies, vehicles = data_manager.get_entities()
    if not emergencies:
        print("No emergencies to plan for. Skipping tick.")
        return
    if not vehicles:
        print("No vehicles available. Skipping tick.")
        return

    # 2. Get the routing matrix from Valhalla
    matrix_result = routing_service.get_matrix(emergencies, vehicles)

    # 3. Solve the Vehicle Routing Problem
    optimizer = RouteOptimizer(matrix_result, len(vehicles), OPTIMIZATION_GOAL)
    solution = optimizer.solve(VRP_TIMEOUT_S)

    if "error" in solution:
        print(f"Optimization failed: {solution['error']}. Skipping this tick.")
        return

    # 4. Process the solution to generate plans and update vehicle states
    processor = PlanProcessor()
    plans_to_save, completed_ids, vehicle_updates = processor.process_solution(
        solution, vehicles, emergencies, matrix_result, DISTANCE_PER_TICK_M
    )

    # 5. COMMIT CHANGES TO DATABASE
    data_manager.update_state_in_transaction(
        plans_to_save, completed_ids, vehicle_updates
    )
        
    print("--- Simulation tick completed successfully ---")

# COMMAND ----------

data_manager = DataManager(DB_URL)
routing_service = RoutingService(VALHALLA_CONFIG_PATH)

try:
    while True:
        run_simulation_tick(data_manager, routing_service)
        print(f"\nSleeping for {TICK_INTERVAL_SECONDS} seconds...")
        time.sleep(TICK_INTERVAL_SECONDS)
# except KeyboardInterrupt:
#     print("\nSimulation stopped by user.")
# except Exception as e:
#     print(f"\nAn unexpected error occurred: {e}")
finally:
    data_manager.close()

# COMMAND ----------

dbutils.notebook.exit("0")

# COMMAND ----------

dbutils.widgets.text("CATALOG", "users")
dbutils.widgets.text("SCHEMA", "")
dbutils.widgets.text("VOLUME_PATH", "")
dbutils.widgets.text("DB_URL", "")

# COMMAND ----------

