#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies using binary wheels only (avoids Rust build errors)
pip install --upgrade pip
pip install --only-binary=:all: -r requirements.txt

# Start FastAPI server
echo "Starting FNOL Observability API..."
python -m app.main
