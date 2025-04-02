#!/bin/bash

# Use this script to initialize the development environment.
#
# Usage: source bootstrap.sh
# Requires: python3, npm

cd "$(dirname "$0")/.."

# Install the npm packages
echo "Installing the npm packages..."
npm install --legacy-peer-deps --prefix "src/ui" > /dev/null

# Create a default .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating a default .env file..."
    echo "DB_URI=sqlite:///db.sqlite3" > .env
else
    echo "Default .env file already exists."
fi

# Create a virtual environment if it doesn't exist
if [ ! -d .venv ]; then
    echo "Creating a virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source .venv/bin/activate
# Install the development requirements
echo "Installing the development requirements..."
pip install --upgrade pip > /dev/null
pip install '.[dev]' > /dev/null
