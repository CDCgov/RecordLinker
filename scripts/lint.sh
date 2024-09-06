#!/bin/sh
#
# Lint the project source code.
#
# Usage: scripts/lint.sh <src-dir>
#
# <src-dir> is the path to the source code to lint. If not specified, the entire
# project source code will be linted.
#
set -e

cd "$(dirname "$0")/.."

SRC=${1:-src/}

ruff check ${SRC}
