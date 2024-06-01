#!/bin/bash
# Kill any current server
pkill -f server.py

# If venv does not exist, create it
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install the requirements
pip install -r requirements.txt

# Run the application
python server.py
