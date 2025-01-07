#!/bin/sh
#
# Get the name of the version if the commit is tagged, else
# calculate the next feature version name for the project.
#
# Usage: scripts/version_name.sh
#
# The format of the tag is vYY.X.0-rc.Z, where:
# - YY is the current two digit year
# - X is the next feature version this year
# - Z is the number of commits on main since the last tag

# Check if the HEAD commit is tagged like '^v[0-9]+\.[0-9]+\.[0-9]+$'
if git describe --tags --exact-match HEAD 2>/dev/null | grep -q "^v[0-9]\+\.[0-9]\+\.[0-9]\+$"; then
  # Get the latest tag
  echo $(git describe --tags --match "v*" --abbrev=0 $(git rev-list --tags --max-count=1) 2>/dev/null || echo "")
else
    # Get the current two digit year
    year=$(date +"%y")
    # Get the latest tag
    latest_tag=$(git describe --tags --match "v*" --abbrev=0 $(git rev-list --tags --max-count=1) 2>/dev/null || echo "")
    # Count the number of commits between the latest tag and HEAD
    commits=$(git rev-list --count $latest_tag..HEAD --)
    # Get latest tag for the current year, or default to v0.0.0
    latest_tag_for_year=$(git describe --tags --match "v${year}.*" --abbrev=0 $(git rev-list --tags --max-count=1) 2>/dev/null || echo "v0.0.0")
    # Get the next feature version
    next_feature_ver=$(($(echo $latest_tag_for_year | cut -d '.' -f 2) + 1))
    echo "v${year}.${next_feature_ver}.0-rc.${commits}"
fi

