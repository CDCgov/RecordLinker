#!/bin/bash
# send_linkage_requests.sh: Script to send FHIR patient data to the linkage API
#
# Arguments:
# $1: The directory containing the FHIR patient data
# $2: The URL of the linkage API
# $3: The number of times to send the data to the API
set -e

cd "$(dirname "$0")/.."

DATA=${1:-"data/"}
API_URL=${2:-"http://localhost:8080"}
ITERATIONS=${3:-"1"}

# Loop over the synthetic patient data N times, this will help
# to simulate a real-world scenario where we see multiple encounters
# come in for the same patient.
for ((i=1; i<=ITERATIONS; i++)); do
    # Loop over every synthetic FHIR encounter created
    for file in "${DATA}"/*; do
        # check that the file is a JSON file
        if [[ -f "$file" && "$file" == *.json ]]; then
            if grep -qFx 'null' $file; then
                # skip the file if it contains 'null'
                echo "Skipping $file as it contains 'null'"
                continue
            fi
            # using jq, transform the FHIR resource to just the Patient bundle
            raw_bundle=$(jq '.entry |= map(select(.resource.resourceType == "Patient"))' "$file")
            # replace the patient ID with a new unique UUID, if we have ITERATIONS > 1
            # this is important as the linkage API assumes every patient payload will
            # have a unique patient ID.
            uuid=$(uuidgen)
            bundle=$(jq ".entry[0].resource.id = \"$uuid\"" <<< "$raw_bundle")
            # use the bundle to create a JSON payload for the linkage API
            payload="{\"bundle\": ${bundle}}"
            # record the response to response.txt and capture the status code from STDOUT
            response=$(curl -s -o response.txt -w "%{http_code}" \
                -X POST --header "Content-Type: application/json" \
                -d "$payload" "${API_URL}/link-record")
            status_code="${response: -3}"
            # parse the response to see if a MPI match was found
            match=$(jq '.found_match' response.txt)
            # print the status code, match and file name
            echo -e "STATUS:${status_code}\tMATCH:${match}\tFILE:${file}"
        fi
    done
done
