#!/bin/bash

# This script lists all open pull requests for this repository.
#
# Usage: open_pulls.sh
# Requires: curl, jq

set -e

cd "$(dirname "$0")/.."

# check if the GITHUB_TOKEN environment variable is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Missing environment variable: GITHUB_TOKEN"
    exit 1
fi
# set the URL to the GitHub API
REPO=$(git config --get remote.origin.url | sed -E 's#git@github.com:(.*)\.git#\1#')
URL="https://api.github.com/repos/$(echo $REPO | cut -d'/' -f1)/$(echo $REPO | cut -d'/' -f2)"

# create function to call GH API, the first argument is the endpoint
gh_api() {
    curl --silent -H "Authorization: token ${GITHUB_TOKEN}" -H "Accept: application/vnd.github.v3+json" ${URL}/$1
}

# List all open non-draft pull requests, and reduce to key fields
pr_list=$(gh_api pulls?state=open | jq -r 'map(select(.draft == false))' | jq '[.[] | {title, number, user: .user.login, html_url}]')

# For each PR, get the timestamp of the ready_for_review event using the timeline API
# create an array of JSON objects
results=""
while IFS= read -r pr; do
  number=$(echo "$pr" | jq -r '.number')
  # get the timestamp of the ready_for_review event
  ready_for_review=$(gh_api issues/${number}/timeline | jq -r 'map(select(.event == "ready_for_review")) | .[0].created_at')
  # calculate the number of days since the PR was ready for review
  time_since=$((($(date +%s) - $(date -d "$ready_for_review" +%s)) / 86400))
  # add the time_since field to the JSON object
  pr=$(echo "$pr" | jq ". + {time_since: $time_since}")
  if [ -z "$results" ]; then
    results="$pr"
  else
    results="$results, $pr"
  fi
done < <(echo "$pr_list" | jq -c '.[]')
# output the results as a JSON array
echo "[$results]" | jq .
