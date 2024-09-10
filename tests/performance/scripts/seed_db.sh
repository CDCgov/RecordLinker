#!/bin/bash
# seed_db.sh: Script to seed the postgres database with data
#
# Arguments:
# $1: The database URI to connect to
# $2: The seed file to use
set -e

cd "$(dirname "$0")/.."

URI=${1}
SEED_FILE=${2}

# Test if the seed file is compressed
if [[ "${SEED_FILE}" == *.gz ]]; then
    GUNZIP="gunzip --stdout"
else
    GUNZIP="cat"
fi

echo "Seeding the database with ${SEED_FILE}"
# Load the seed file into the database
${GUNZIP} "${SEED_FILE}" | psql --quiet ${URI}
