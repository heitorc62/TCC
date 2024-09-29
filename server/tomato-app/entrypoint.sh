#!/bin/bash
set -e

echo "Running Database Migrations..."

export PYTHONPATH=".:$PYTHONPATH"

# Check if the migrations directory exists and is not empty
if [ ! -d "migrations" ] || [ -z "$(ls -A migrations)" ]; then
    echo "Initializing Database Migrations..."
    flask db init
fi

echo "Generating migration scripts..."
flask db migrate || { echo "Migration failed"; exit 1; }

echo "Applying migrations..."
flask db upgrade || { echo "Upgrade failed"; exit 1; }

echo "Running Application..."

exec "$@"
