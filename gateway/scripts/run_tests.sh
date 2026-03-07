#!/bin/bash
# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run pytest
pytest -q noogh/app/tests
