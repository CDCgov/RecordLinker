#!/bin/sh
#
# Run the API server locally.
#
# Usage: scripts/local_server.sh <port>
#
# <port> is the port on which to run the API server. If not specified, the server
# will run on port 8000.
#
cleanup() {
  echo "Cleaning up and exiting..."
  kill 0
  exit 0
}

trap cleanup EXIT INT TERM

set -e

cd "$(dirname "$0")/.."

PORT=${1:-8000}

# Start the API server, reloading the server with the source code changes.
# Also specify the app directory to run the server based off the source code
# and not whats been installed into the virtual environment.
UI_HOST="http://localhost:3000" uvicorn recordlinker.main:app --app-dir src/api --port ${PORT} &

cd "$(dirname "$0")/../src/ui"
npm run dev

wait
