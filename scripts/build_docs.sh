#!/bin/sh

# This script builds the public documentation for this repository.
#
# Usage: build_docs.sh
# Requires: npx

set -e

cd "$(dirname "$0")/.."

OUT=${1:-_site}

mkdocs build --config-file docs/mkdocs.yml -d "../${OUT}"
python -m recordlinker.utils.openapi_schema > ${OUT}/openapi.json
npx  @redocly/cli build-docs -o "${OUT}/api-docs.html" "${OUT}/openapi.json"
