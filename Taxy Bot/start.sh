#!/bin/bash

# Exit if any command fails
set -e

# Optional: Print current working directory
echo "Running from $(pwd)"

# Optional: Install any extra things if needed
# pip install -r requirements.txt  # (Usually done by Render already during build)

# Launch the app
echo "Starting app..."
python app.py
