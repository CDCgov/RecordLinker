#!/bin/sh
#
# Run mypy on new files changed or added in git.
#
# Usage: scripts/check_types.sh <python-path> <python-path>
#
# <python-path> is the path to run with mypy. If not specified, mypy with run
# off of the files found in git status. You can run multiple paths with mypy
set -e

cd "$(dirname "$0")/.."

PATHS=${*:-$(git status -s | sed "s@^[^ ]* @$PWD/@")}

non_python_list=()
for p in ${PATHS}; do
  if [[ $p == *.py ]]; then
      mypy $p --ignore-missing-imports
  else
      non_python_list+=(1)
  fi
done


if [[ -n ${non_python_list[@]} ]]; then
    echo "Either no git changes or no python files"
fi