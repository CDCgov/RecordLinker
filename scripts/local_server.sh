#!/bin/sh
#
# Run the API server locally.
#
# Usage: scripts/local_server.sh <port>
#
# <port> is the port on which to run the API server. If not specified, the server
# will run on port 8000.
#
set -e

cd "$(dirname "$0")/.."

PORT=${1:-8000}

# Start the API server
uvicorn recordlinker.main:app --reload --port ${PORT}
