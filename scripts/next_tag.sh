#!/bin/sh


# Get the current two digit year
year=$(date +"%y")
# Get the latest tag
latest_tag=$(git describe --tags --match "v*" --abbrev=0 $(git rev-list --tags --max-count=1) 2>/dev/null || echo "")
# Count the number of commits on main since the last tag
commits=$(git rev-list --count $latest_tag..HEAD --)
# Get latest tag for the current year
latest_tag_for_year=$(git describe --tags --match "v${year}.*" --abbrev=0 $(git rev-list --tags --max-count=1) 2>/dev/null || echo "v0.0.0")
# Get the next feature version
next_feature_ver=$(($(echo $latest_tag_for_year | cut -d '.' -f 2) + 1))
# Pad the next feature version
next_feature_ver_padded=$(printf "%02d" "$next_feature_ver")
echo "v${year}.${next_feature_ver_padded}.00-rc.${commits}"
