#!/bin/bash

# Activate virtual environment and run Flask app in development mode
cd "$(dirname "$0")"
source .venv/bin/activate
python3 app.py