# Lakehouse Emergency Responders Routing Engine

A real-time emergency responder dispatch and routing optimization system built on Databricks Lakehouse platform. This system continuously optimizes the assignment and routing of emergency vehicles to incidents using advanced routing algorithms and vehicle routing problem (VRP) solvers.

## 🏗️ Architecture Overview

This system implements a continuous optimization loop that:
1. **Fetches** current emergencies and vehicle locations from a PostgreSQL database
2. **Calculates** travel time/distance matrices using the Valhalla routing engine
3. **Optimizes** vehicle assignments using Google OR-Tools VRP solver
4. **Updates** vehicle positions and plans in real-time
5. **Repeats** the cycle based on configurable intervals

The system prioritizes emergencies by urgency level (high/medium/low) and ensures optimal response times while considering real-world routing constraints.

## 📁 Project Structure

```
├── databricks.yml              # Databricks Asset Bundle configuration
├── pyproject.toml              # Python project dependencies and metadata
├── resources/                  # Databricks job definitions
│   └── routing_engine_job.py   # Main workflow job definition
└── src/                        # Core application source code
    ├── main.py                 # Main simulation loop and entry point
    ├── data.py                 # Database operations and entity management
    ├── routing.py              # Valhalla routing service integration
    ├── optimizer.py            # OR-Tools VRP solver implementation
    ├── plan_processor.py       # Solution processing and plan generation
    ├── lakebase/               # Database setup and initialization
    │   ├── initialise.py       # PostgreSQL database and user setup
    │   └── populate.py         # Sample data population
    └── valhalla/               # Routing engine setup
        ├── install-valhalla.py # Valhalla installation and configuration
        └── populate-graph.py   # OSM data ingestion for routing graphs
```

## 🧩 Core Components

### Main Application (`src/main.py`)
The central simulation engine that orchestrates the entire optimization process:
- Runs continuous optimization ticks
- Coordinates between all system components
- Manages the main event loop with configurable intervals
- Handles error recovery and graceful shutdown

### Data Management (`src/data.py`)
Handles all database operations using SQLModel:
- **Entities**: Manages `Emergency`, `Vehicle`, and `Plan` objects
- **Transactions**: Atomic updates ensuring data consistency
- **State Management**: Real-time tracking of vehicle positions and emergency status

### Routing Service (`src/routing.py`)
Valhalla routing engine integration:
- **Matrix Calculations**: Efficient many-to-many distance/time matrices
- **Geographic Processing**: Handles lat/lon coordinate transformations
- **Urgency Annotation**: Enriches routing data with emergency priority levels

### Route Optimizer (`src/optimizer.py`)
Google OR-Tools Vehicle Routing Problem solver:
- **Multi-objective Optimization**: Balances time, distance, and urgency priorities
- **Constraint Handling**: Manages vehicle capacity and routing constraints
- **Priority Scheduling**: Implements urgency-based penalties for optimal dispatch ordering

### Plan Processor (`src/plan_processor.py`)
Converts optimization solutions into actionable plans:
- **Route Generation**: Creates detailed step-by-step vehicle routes
- **ETA Calculations**: Provides accurate arrival time estimates
- **State Updates**: Manages vehicle position updates and emergency completion

### Database Setup (`src/lakebase/`)
PostgreSQL database provisioning on Databricks:
- **`initialise.py`**: Creates database instances, users, and permissions
- **`populate.py`**: Seeds the system with sample emergencies and vehicles

### Valhalla Setup (`src/valhalla/`)
Routing engine configuration and data ingestion:
- **`install-valhalla.py`**: Installs and configures Valhalla routing engine
- **`populate-graph.py`**: Downloads and processes OpenStreetMap data for routing

## 🚀 Deployment as Databricks Asset Bundle

This project is configured as a Databricks Asset Bundle for streamlined deployment and management.

### Prerequisites
- Databricks CLI (>= 0.248.0)
- Access to a Databricks workspace
- Appropriate permissions for compute cluster creation

### Deployment Steps

1. **Install Dependencies**
   ```bash
   uv sync  # Install Python dependencies
   ```

2. **Configure Bundle**
   Edit `databricks.yml` to set your workspace URL and target environment:
   ```yaml
   targets:
     dev:
       workspace:
         host: https://your-workspace.cloud.databricks.com
   ```

3. **Deploy to Development**
   ```bash
   databricks bundle deploy --target dev
   ```

4. **Run the Job**
   ```bash
   databricks bundle run routing_engine_job --target dev
   ```

### Bundle Configuration

The bundle defines a multi-task workflow:
1. **`build_valhalla`**: Sets up Valhalla routing engine
2. **`ingest_osm_pbf`**: Downloads and processes OpenStreetMap data
3. **`initialise_db`**: Creates PostgreSQL database and users
4. **`populate_db`**: Seeds database with sample data
5. **`fat_controller`**: Runs the main optimization loop

### Job Parameters

Configure the job with these parameters:
- **`CATALOG`**: Unity Catalog name (default: `users`)
- **`SCHEMA`**: Database schema (default: `stuart_lynn`)
- **`VOLUME`**: Unity Catalog volume for data storage (default: `valhalla_berlin`)
- **`PBF_URL`**: OpenStreetMap data source URL

### Production Deployment

For production deployment:
```bash
databricks bundle deploy --target prod
```

Production target includes:
- Proper user permissions and access controls
- Performance-optimized compute settings
- Centralized workspace paths

## ⚙️ Configuration

### Environment Variables
- **`DB_URL`**: PostgreSQL connection string
- **`VOLUME_PATH`**: Path to Unity Catalog volume containing routing data
- **`VALHALLA_CONFIG_PATH`**: Path to Valhalla configuration file

### Optimization Parameters
Configurable in `src/main.py`:
- **`TICK_INTERVAL_SECONDS`**: Optimization cycle frequency
- **`DISTANCE_PER_TICK_M`**: Vehicle movement simulation distance
- **`OPTIMIZATION_GOAL`**: Objective function ("time" or "distance")
- **`VRP_TIMEOUT_S`**: Maximum solver runtime per iteration

## 🏃 Usage

### Running Locally (Development)
```bash
# Ensure you have the required dependencies
uv sync

# Set up your environment variables
export DB_URL="your-postgresql-connection-string"
export VOLUME_PATH="/path/to/your/volume"

# Run the main simulation
python src/main.py
```

### Running on Databricks
The system is designed to run as a Databricks job. Deploy the bundle and execute the workflow through the Databricks UI or CLI.

### Monitoring
Monitor the system through:
- Databricks job logs for real-time optimization status
- Database queries to track emergency response metrics
- Valhalla routing performance statistics

## 📊 Dependencies

### Core Dependencies
- **`valhalla`**: High-performance routing engine
- **`ortools`**: Google's optimization tools for VRP solving
- **`sqlmodel`**: Type-safe database operations
- **`geopandas`**: Geospatial data processing
- **`psycopg2`**: PostgreSQL database adapter

### Databricks Dependencies
- **`databricks-bundles`**: Asset bundle management
- **`databricks-sdk`**: Workspace and compute management
- **`lakebase_responders_entities`**: Custom entity definitions

## 🔧 Development

### Project Setup
```bash
# Clone the repository
git clone <repository-url>
cd lakehouse-responders-routing

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Testing
Run tests locally before deployment:
```bash
# Run unit tests (when available)
pytest

# Validate bundle configuration
databricks bundle validate
```

## 📈 Performance

The system is optimized for:
- **Real-time Processing**: Sub-second optimization cycles
- **Scalability**: Handles hundreds of vehicles and emergencies
- **Reliability**: Atomic database transactions and error recovery
- **Efficiency**: Leverages Valhalla's high-performance routing

## 🚨 Emergency Priority Levels

The system handles three urgency levels:
- **High**: Life-threatening emergencies (immediate dispatch priority)
- **Medium**: Urgent situations requiring prompt response
- **Low**: Non-critical incidents with flexible timing

Priority is enforced through the OR-Tools solver using position-based penalties.

---

For questions or issues, please refer to the Databricks documentation or contact the development team.