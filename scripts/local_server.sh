#!/bin/sh
#
# Run the API server locally.
#
# Usage: scripts/local_server.sh <port> <workers>
#
# <port> is the port on which to run the API server. If not specified, the server
# will run on port 8080.
# <workers> is the number of workers to use for the API server. If not specified,
# the server will use 1 worker.
#
set -e

cd "$(dirname "$0")/.." || exit

PORT=${1:-8080}
WORKERS=${2:-1}

# Specify the app directory to run the server based off the source code
# and not whats been installed into the virtual environment
PARAMS="--app-dir src/ --port ${PORT} --workers ${WORKERS}"

# if workers eq 1
if [ "$WORKERS" -eq 1 ]; then
    # When only 1 worker is used; enable hot reloading
    PARAMS="${PARAMS} --reload --reload-dir src/"
fi


set -- $PARAMS
# Start the API server
uvicorn recordlinker.main:app "$@"
