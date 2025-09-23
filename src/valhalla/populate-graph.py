# Databricks notebook source
# MAGIC %md
# MAGIC # Process OSM PBF with Valhalla
# MAGIC
# MAGIC This notebook downloads and processes an OpenStreetMap `.pbf` extract using Valhalla build tools. It creates routing tiles, timezones, and administrative boundaries, and stores them in the specified volume path.
# MAGIC
# MAGIC ## Usage
# MAGIC This notebook is intended to be **run as a scheduled Databricks job** using two parameters:
# MAGIC - **`PBF_URL`**: URL of the OSM `.pbf` file (e.g. from [Geofabrik](https://download.geofabrik.de/))
# MAGIC - **`VOLUME_PATH`**: Path to the destination volume for tiles (e.g. `/Volumes/timo/geospatial/valhalla_spain`)
# MAGIC
# MAGIC The notebook also depends on `_Initial Setup`, which should install Valhalla and load it into the environment.

# COMMAND ----------

# DBTITLE 1,Set Parameters
dbutils.widgets.text("PBF_URL", "https://download.geofabrik.de/europe/spain-latest.osm.pbf", "PBF URL")
dbutils.widgets.text("VOLUME_PATH", "/Volumes/timo/geospatial/valhalla_spain", "Target Volume Path")

pbf_url = dbutils.widgets.get("PBF_URL")
volume_path = dbutils.widgets.get("VOLUME_PATH")

import os
os.environ["PBF_URL"] = pbf_url
os.environ["VALHALLA_VOLUME_PATH"] = volume_path

# COMMAND ----------

# DBTITLE 1,Download and Build Tiles
# MAGIC %sh
# MAGIC set -euxo pipefail
# MAGIC
# MAGIC # Inputs
# MAGIC PBF_FILE=$(basename "${PBF_URL}")
# MAGIC PBF_PATH="/local_disk0/${PBF_FILE}"
# MAGIC TILE_DIR="${VALHALLA_VOLUME_PATH}/tiles"
# MAGIC TEMP_DIR=$(mktemp -d -p /local_disk0 valhalla_tmp_XXXX)
# MAGIC
# MAGIC echo "📥 Downloading ${PBF_URL}"
# MAGIC wget -N -O "${PBF_PATH}" "${PBF_URL}"
# MAGIC
# MAGIC # Create temp build directory
# MAGIC mkdir -p "${TEMP_DIR}"
# MAGIC cd "${TEMP_DIR}"
# MAGIC
# MAGIC # Generate initial config file
# MAGIC valhalla_build_config \
# MAGIC   --mjolnir-tile-dir "${TEMP_DIR}" \
# MAGIC   --mjolnir-tile-extract "${TEMP_DIR}/tiles.tar" \
# MAGIC   --mjolnir-timezone "${TEMP_DIR}/timezones.sqlite" \
# MAGIC   --mjolnir-admin "${TEMP_DIR}/admins.sqlite" > "${TEMP_DIR}/valhalla.json"
# MAGIC
# MAGIC # Build supporting files
# MAGIC valhalla_build_timezones > "${TEMP_DIR}/timezones.sqlite"
# MAGIC valhalla_build_admins -c "${TEMP_DIR}/valhalla.json" "${PBF_PATH}"
# MAGIC valhalla_build_tiles -c "${TEMP_DIR}/valhalla.json" "${PBF_PATH}"
# MAGIC valhalla_build_extract -c "${TEMP_DIR}/valhalla.json" -v
# MAGIC
# MAGIC # Rewrite paths in config to final TILE_DIR
# MAGIC jq --arg from "${TEMP_DIR}" --arg to "${TILE_DIR}" '
# MAGIC   walk(
# MAGIC     if type == "string" and startswith($from) then
# MAGIC       $to + (.[($from | length):])
# MAGIC     else
# MAGIC       .
# MAGIC     end
# MAGIC   )
# MAGIC ' "${TEMP_DIR}/valhalla.json" > "${TEMP_DIR}/valhalla_fixed.json"
# MAGIC
# MAGIC echo "📦 Copying files to ${TILE_DIR}"
# MAGIC mkdir -p "${TILE_DIR}"
# MAGIC rsync -a "${TEMP_DIR}/" "${TILE_DIR}/"
# MAGIC mv "${TILE_DIR}/valhalla_fixed.json" "${TILE_DIR}/valhalla.json"
# MAGIC rm -rf "${TEMP_DIR}"

# COMMAND ----------

# DBTITLE 1,Test Configuration
import json
import warnings
import subprocess
from subprocess import PIPE, DEVNULL, CalledProcessError

config_path = f"{volume_path}/tiles/valhalla.json"
force_cli = False  # Set to True to force using CLI fallback

# Adjust these coordinates to match your actual tile coverage
query = {
    "locations": [
        {"lat": 41.3851, "lon": 2.1734, "type": "break", "city": "Barcelona"},
        {"lat": 40.4168, "lon": -3.7038, "type": "break", "city": "Madrid"}
    ],
    "costing": "auto",
    "directions_options": {"units": "kilometers"}
}

def run_cli_fallback():
    try:
        cli_command = [
            "/usr/local/bin/valhalla_service",
            config_path,
            "route",
            json.dumps(query)
        ]

        result = subprocess.run(
            cli_command,
            stdout=PIPE,
            stderr=PIPE,
            text=True
        )

        # Log warning logs only if needed
        stderr_filtered = "\n".join([
            line for line in result.stderr.strip().splitlines()
            if "No suitable edges" in line or "error" in line.lower()
        ])

        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError("Invalid JSON output from valhalla_service.")

        if "trip" not in parsed:
            print("❌ Routing failed — no trip returned.")
            return {
                "status": "error",
                "stderr": stderr_filtered,
                "stdout": result.stdout.strip()
            }

        summary = parsed["trip"].get("summary", {})
        distance = summary.get("length", "N/A")
        time = summary.get("time", "N/A")

        print("✅ Routing via valhalla_service succeeded.")
        print(f"   ➤ Distance: {distance} km")
        print(f"   ➤ Estimated Time: {round(time / 60, 1)} min" if isinstance(time, (int, float)) else f"   ➤ Time: {time}")

        return {"status": "success", "distance": distance, "time_min": round(time / 60, 1) if isinstance(time, (int, float)) else time}

    except Exception as e:
        print("❌ CLI fallback failed with exception:")
        print(str(e))
        return {
            "status": "exception",
            "message": str(e)
        }


# --- Main Routing ---
if force_cli:
    run_cli_fallback()
else:
    try:
        import valhalla
        from valhalla import Actor

        actor = Actor(config_path)
        result = actor.route(query)

        summary = result.get("trip", {}).get("summary", {})
        distance = summary.get("length", "N/A")
        time = summary.get("time", "N/A")

        print("✅ Routing via Python bindings succeeded.")
        print(f"   ➤ Distance: {distance} km")
        print(f"   ➤ Estimated Time: {round(time / 60, 1)} min" if isinstance(time, (int, float)) else f"   ➤ Time: {time}")

    except ImportError:
        warnings.warn(
            "⚠️ Valhalla Python bindings unavailable. Falling back to valhalla_service.",
            RuntimeWarning
        )
        run_cli_fallback()

# COMMAND ----------

