# Databricks notebook source
# MAGIC %md
# MAGIC # Valhalla Build & Cache Script
# MAGIC
# MAGIC This notebook builds the Valhalla routing engine with Python bindings in a Databricks environment. It installs all dependencies, compiles the code, and caches the resulting binaries and wheel file to persistent storage. It also generates an init script for restoring these binaries on future cluster startups.
# MAGIC
# MAGIC **Important Notes:**
# MAGIC - You generally should **not run this notebook directly**.
# MAGIC - It is invoked internally by the process handling `.pbf` file inputs.
# MAGIC - The generated init script can be reused across clusters to avoid recompilation.

# COMMAND ----------

import os

dbutils.widgets.text("VOLUME_PATH", "/Volumes/timo/geospatial/valhalla_spain", "Target Volume Path")
vol_base = dbutils.widgets.get("VOLUME_PATH")

cache_bin_dir = f"{vol_base}/bin"
cache_whl_dir = f"{vol_base}/whl"
init_script_path = f"{vol_base}/init.sh"

os.environ["CACHE_BIN_DIR"] = cache_bin_dir
os.environ["CACHE_WHL_DIR"] = cache_whl_dir

# COMMAND ----------

# DBTITLE 1,Clone and Install Dependencies
# MAGIC %sh
# MAGIC set -euxo pipefail
# MAGIC
# MAGIC # Define base directory for build
# MAGIC cd /local_disk0/
# MAGIC rm -rf valhalla_build
# MAGIC mkdir -p valhalla_build && cd valhalla_build
# MAGIC
# MAGIC # Clone Valhalla with all submodules
# MAGIC git clone --recurse-submodules https://github.com/valhalla/valhalla.git
# MAGIC cd valhalla
# MAGIC
# MAGIC # Install required system packages and Valhalla-specific dependencies
# MAGIC sudo apt-get update -y
# MAGIC ./scripts/install-linux-deps.sh
# MAGIC
# MAGIC # Set up dynamic linker to find Valhalla libraries
# MAGIC export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}
# MAGIC echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/valhalla.conf
# MAGIC sudo ldconfig

# COMMAND ----------

# DBTITLE 1,Build Valhalla and Python Wheel
# MAGIC %sh
# MAGIC set -euxo pipefail
# MAGIC
# MAGIC cd /local_disk0/valhalla_build/valhalla/
# MAGIC
# MAGIC # Configure and build Valhalla with Python bindings
# MAGIC cmake -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_PYTHON_BINDINGS=ON
# MAGIC make -C build -j$(nproc)
# MAGIC sudo make -C build install
# MAGIC
# MAGIC # Build Python wheel for Valhalla bindings
# MAGIC python -m pip install -r src/bindings/python/requirements-build.txt
# MAGIC python setup.py bdist_wheel
# MAGIC
# MAGIC # Refresh dynamic linker
# MAGIC sudo ldconfig

# COMMAND ----------

# DBTITLE 1,Verify Import
import valhalla

# COMMAND ----------

# DBTITLE 1,Cache Built Artifacts
# MAGIC %sh
# MAGIC set -euxo pipefail
# MAGIC
# MAGIC CACHE_BIN_DIR="${CACHE_BIN_DIR:?}"
# MAGIC CACHE_WHL_DIR="${CACHE_WHL_DIR:?}"
# MAGIC LOCAL_BIN="/usr/local/bin"
# MAGIC LOCAL_LIB="/usr/local/lib"
# MAGIC VALHALLA_BUILD_DIR="/local_disk0/valhalla_build/valhalla"
# MAGIC
# MAGIC cd "$VALHALLA_BUILD_DIR"
# MAGIC
# MAGIC # Find the built wheel file
# MAGIC WHEEL_FILE=$(find dist -name "*.whl" | head -n1)
# MAGIC
# MAGIC echo "📦 Caching binaries to $CACHE_BIN_DIR"
# MAGIC mkdir -p "$CACHE_BIN_DIR" "$CACHE_WHL_DIR"
# MAGIC
# MAGIC # Copy compiled binaries and libraries
# MAGIC cp -f "$LOCAL_BIN"/valhalla* "$CACHE_BIN_DIR/" || true
# MAGIC cp -f "$LOCAL_LIB"/libvalhalla* "$CACHE_BIN_DIR/" || true
# MAGIC cp -f "$LOCAL_LIB"/libprime_server* "$CACHE_BIN_DIR/" || true
# MAGIC
# MAGIC echo "📦 Caching wheel to $CACHE_WHL_DIR"
# MAGIC cp -f "$WHEEL_FILE" "$CACHE_WHL_DIR/" || true
# MAGIC
# MAGIC echo "✅ Cache saved from $VALHALLA_BUILD_DIR"

# COMMAND ----------

# DBTITLE 1,Generate Init Script
init_script_content = f"""#!/bin/bash
set -euxo pipefail

# Define important paths
CACHE_BIN_DIR="{cache_bin_dir}"      # Where precompiled Valhalla binaries are stored
CACHE_WHL_DIR="{cache_whl_dir}"      # Where the Valhalla Python wheel is stored
LOCAL_BIN="/usr/local/bin"           # System path for executables
LOCAL_LIB="/usr/local/lib"           # System path for libraries
BUILD_DIR="/local_disk0/valhalla_build"  # Placeholder, not used here

# Install system-level dependencies required to run Valhalla (no build)
sudo apt-get update -y
env DEBIAN_FRONTEND=noninteractive sudo apt install --yes --quiet \\
  autoconf automake ccache clang clang-tidy coreutils curl cmake \\
  g++ gcc git jq lcov libboost-all-dev libcurl4-openssl-dev libczmq-dev \\
  libgdal-dev libgeos++-dev libgeos-dev libluajit-5.1-dev liblz4-dev \\
  libprotobuf-dev libspatialite-dev libsqlite3-dev libsqlite3-mod-spatialite \\
  libtool libzmq3-dev lld locales luajit make osmium-tool parallel pkgconf \\
  protobuf-compiler python3-all-dev python3-shapely python3-requests \\
  python3-pip spatialite-bin unzip zlib1g-dev

# Ensure system linker can locate Valhalla and Prime Server libraries
export LD_LIBRARY_PATH=/usr/local/lib:${{LD_LIBRARY_PATH:-}}
echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/valhalla.conf
sudo ldconfig

# Try to detect if prebuilt binaries and Python wheel are already cached
BIN_OK=false
WHL_OK=false

ROUTE_FILE=$(find "$CACHE_BIN_DIR" -maxdepth 1 -name "valhalla_*route" | head -n1)
[[ -f "$ROUTE_FILE" ]] && BIN_OK=true

WHEEL_FILE=$(find "$CACHE_WHL_DIR" -maxdepth 1 -name "*.whl" | head -n1)
[[ -n "$WHEEL_FILE" ]] && WHL_OK=true

# If both are found, restore them
if [[ "$BIN_OK" == "true" && "$WHL_OK" == "true" ]]; then
  sudo cp -f "$CACHE_BIN_DIR"/valhalla* "$LOCAL_BIN/" || true
  sudo cp -f "$CACHE_BIN_DIR"/libvalhalla* "$LOCAL_LIB/" || true
  sudo cp -f "$CACHE_BIN_DIR"/libprime_server* "$LOCAL_LIB/" || true
  sudo ldconfig
  python3 -m pip install "$WHEEL_FILE"
  echo "✅ Valhalla binaries and wheel restored from cache."
  exit 0
fi
"""

# Write script to Volumes
dbutils.fs.put(init_script_path, init_script_content, overwrite=True)
print(f"Init script written to: {init_script_path}")

# COMMAND ----------

# DBTITLE 1,Preview Init Script
print(dbutils.fs.head(init_script_path))