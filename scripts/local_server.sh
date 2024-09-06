#!/bin/sh
#
# Run the API server locally.
#
# Usage: scripts/local_service.sh <port>
#
# <port> is the port on which to run the API server. If not specified, the server
# will run on port 8000.
#
set -e

cd "$(dirname "$0")/.."

PORT=${1:-8000}

DB_PID=$(docker run -d --rm -p 5432:5432 -e POSTGRES_PASSWORD=pw -e POSTGRES_DB=testdb postgres:13-alpine)

cleanup() {
    docker stop ${DB_PID} > /dev/null 2>&1
    docker rm ${DB_PID} > /dev/null 2>&1
}

trap cleanup EXIT

# Read in environment variables defined in .env
export $(grep -v '^#' .env | xargs)
# Start the API server
python -m uvicorn recordlinker.main:app --app-dir src --reload --host 0 --port ${PORT} --log-config src/recordlinker/log_config.yml
