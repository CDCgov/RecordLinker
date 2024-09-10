#!/bin/sh
#
# Run the unit tests for the project.
#
# Usage: scripts/unit_test.sh <test-spec>
#
# <test-spec> is the path to the test file(s) to run. If not specified, all tests
# in the "test/unit/" directory will be run.
#
set -e

cd "$(dirname "$0")/.."

TESTS=${1:-tests/unit/}

DB_PID=$(docker run -d --rm -p 5432:5432 -e POSTGRES_PASSWORD=pw -e POSTGRES_DB=testdb postgres:13-alpine)

cleanup() {
    docker stop ${DB_PID} > /dev/null 2>&1
    docker rm ${DB_PID} > /dev/null 2>&1
}

# Wait for the database to start
while ! docker exec ${DB_PID} pg_isready -q -h localhost -U postgres; do
    sleep 1
done


trap cleanup EXIT

pytest ${TESTS}
