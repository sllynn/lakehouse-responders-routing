# Integrating lakebase-responders-entities

This document explains how to integrate the `lakebase-responders-entities` repository into your `lakehouse-responders-routing` project.

## Current Integration Status

The entities code has been integrated into `src/lakebase/entities/` and is ready to be converted to a git submodule for proper version control. A conversion script is provided for easy migration.

### What's included:
- `src/lakebase/entities/src/lakebase_responders_entities/entities.py` - SQLModel entity definitions
- `src/lakebase/entities/pyproject.toml` - Package configuration  
- `src/lakebase/scripts/build_entities.py` - Databricks notebook to build the entities package
- Updated job workflow to build entities before other tasks

## Integration Options

### Option 1: Git Submodule (Recommended - Ready to Use!)

**Pros:**
- Maintains separate version control for entities
- Easy to update and contribute back to entities repo
- Other projects can also use the entities library
- Clean separation of concerns

**Quick Conversion:**
The entities repository is already pushed to `git@github.com:sllynn/lakehouse-responders-entities.git`. Simply run:

```bash
cd /Users/stuart.lynn/Projects/lakehouse-responders-routing
./convert-to-submodule.sh
```

**Manual Steps (if you prefer):**
```bash
# Remove copied directory
rm -rf src/lakebase/entities/

# Add as submodule
git submodule add git@github.com:sllynn/lakehouse-responders-entities.git src/lakebase/entities

# Commit the change
git add .gitmodules src/lakebase/entities
git commit -m "Convert entities to git submodule"
```

**For team members:**
```bash
# When cloning
git clone --recursive <repo-url>

# Or initialize submodules after cloning
git submodule update --init --recursive

# To update submodule later
git submodule update --remote src/lakebase/entities
```

### Option 2: Git Subtree (Simpler Alternative)

**Pros:**
- Simpler for contributors (no submodule complexity)
- Entities code is directly part of the main repo

**Cons:**
- Harder to contribute changes back to entities repo
- More complex merge history

**Steps:**
```bash
# Remove copied directory first
rm -rf src/lakebase/entities/
git subtree add --prefix=src/lakebase/entities https://github.com/yourusername/lakebase-responders-entities.git main --squash

# To update later:
git subtree pull --prefix=src/lakebase/entities https://github.com/yourusername/lakebase-responders-entities.git main --squash
```

### Option 3: Keep as Separate Package (Current Approach)

**Pros:**
- Clean package separation
- Can version entities independently
- Easy to publish entities to PyPI later

**Cons:**
- Need to manage package building and distribution
- More complex build pipeline

## Current Build Pipeline

The integrated build pipeline now includes:

1. **`build_entities`** - Builds the entities wheel package
2. **`build_valhalla`** - Sets up Valhalla (depends on entities)  
3. **`ingest_osm_pbf`** - Processes map data
4. **`initialise_db`** - Sets up PostgreSQL
5. **`populate_db`** - Seeds database with sample data
6. **`fat_controller`** - Runs the main optimization loop

## Recommendation

For production use, I recommend **Option 1 (Git Submodule)** because:

1. **Clean Architecture**: Maintains proper separation between the entity definitions and routing logic
2. **Reusability**: Other projects can easily use the entities library
3. **Version Control**: You can pin to specific versions of entities for stability
4. **Collaboration**: Easy to contribute improvements back to the entities library
5. **Standard Practice**: Submodules are the standard way to include external repositories

The current copied approach works for immediate development, but submodules provide better long-term maintainability.

## Current Structure

The entities and build scripts are now organized under `src/lakebase/`:

```
src/lakebase/
├── entities/              # Entities package (moved from root)
│   ├── src/
│   │   └── lakebase_responders_entities/
│   │       └── entities.py
│   ├── pyproject.toml
│   ├── build/
│   └── dist/
├── scripts/               # Build scripts (moved from root)  
│   └── build_entities.py
├── initialise.py         # Database setup
└── populate.py          # Database population
```

## Migration Path

1. **Phase 1** (Current): Use copied entities in `src/lakebase/entities/` for immediate development
2. **Phase 2**: Push entities to remote repository and convert to git submodule
3. **Phase 3**: Consider publishing entities to PyPI for broader reuse

This consolidation provides better organization while maintaining the same functionality.
