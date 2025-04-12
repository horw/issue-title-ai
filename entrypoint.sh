#!/bin/bash
set -e

# Echo environment variables for debugging
echo "Environment variables at container startup:"

# Install Python dependencies
pip install -r /requirements.txt

# Run the Python script
python /src/main.py
