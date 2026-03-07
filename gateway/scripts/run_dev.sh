#!/bin/bash
# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run uvicorn
uvicorn noogh.app.main:app --reload --host 0.0.0.0 --port 8000
