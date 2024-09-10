#!/bin/bash
# reset_db.sh: Script to reset the database to a clean state
#
# Arguments:
#  $1: The database URI to connect to
#
set -e

cd "$(dirname "$0")/.."

URI=${1:-"postgres://postgres@localhost:5432/postgres"}


TRUNCATE_STATEMENT="DO \$\$
DECLARE
    table_name TEXT;
BEGIN
    -- Suppress NOTICE messages by redirecting stderr to /dev/null
    SET client_min_messages TO 'ERROR';
    -- For every table in the public schema, truncate it with CASCADE
    FOR table_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(table_name) || ' CASCADE;';
    END LOOP;
END \$\$;"
psql ${URI} -c "${TRUNCATE_STATEMENT}"
echo "All tables truncated."
