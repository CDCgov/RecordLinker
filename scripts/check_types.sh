#!/bin/sh
#
# Run mypy static typing checks on the codebase.
#
# Usage: scripts/check_types.sh <path> ...
#
# <path> is the path to run with mypy. If not specified, mypy with run
# against all the files in the "src" directory.
set -e

cd "$(dirname "$0")/.."

PATHS=("$@")
if [ -z "$PATHS" ]; then
  PATHS=("src/")
 fi
 
mypy ${PATHS[@]}
