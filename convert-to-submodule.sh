#!/bin/bash

# Script to convert entities directory to git submodule
# Run this from the lakehouse-responders-routing root directory

set -e

echo "🔄 Converting entities to git submodule..."

# Check we're in the right directory
if [ ! -f "databricks.yml" ]; then
    echo "❌ Error: Please run this script from the lakehouse-responders-routing root directory"
    exit 1
fi

# Check if entities directory exists
if [ ! -d "src/lakebase/entities" ]; then
    echo "❌ Error: src/lakebase/entities directory not found"
    exit 1
fi

echo "📁 Removing copied entities directory..."
rm -rf src/lakebase/entities

echo "📥 Adding entities as git submodule..."
git submodule add git@github.com:sllynn/lakehouse-responders-entities.git src/lakebase/entities

echo "💾 Committing submodule configuration..."
git add .gitmodules src/lakebase/entities
git commit -m "Convert entities to git submodule"

echo "✅ Conversion complete!"
echo ""
echo "📋 Next steps:"
echo "1. Push changes: git push"
echo "2. Team members should run: git submodule update --init --recursive"
echo "3. To update submodule later: git submodule update --remote src/lakebase/entities"
echo ""
echo "🔄 For future clones, use: git clone --recursive <repo-url>"
