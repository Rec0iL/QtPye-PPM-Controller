#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate the virtual environment
source "$DIR/venv/bin/activate"

# Change to the script's directory and run the Python application
cd "$DIR"
python main.py
