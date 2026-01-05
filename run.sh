#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start FastAPI server
echo "Starting FNOL Observability API..."
python -m app.main
