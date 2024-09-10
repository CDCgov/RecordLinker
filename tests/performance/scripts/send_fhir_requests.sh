#!/bin/bash
# send_fhir_requests.sh: Script to convert ECR to FHIR using the FHIR converter API
#
# Arguments:
# $1: The directory containing the ECR data
# $2: The URL of the FHIR converter API
# $3: The output directory to save the FHIR data to
set -e

cd "$(dirname "$0")/.."

DATA=${1:-"data/"}
API_URL=${2:-"http://localhost:8080"}
OUTPUT_DIR=${3:-"output/"}


cleanup() {
    # Clean up the temporary payload file
    rm -rf /tmp/payload.json
}
trap cleanup EXIT

mkdir -p $OUTPUT_DIR
for dir in "${DATA}"/*; do
    result="${OUTPUT_DIR}/$(basename $dir).json"
    if [ -f $result ]; then continue; fi  # Skip if the FHIR result already exists

    echo "Converting ECR to FHIR: ${result}"
    rr=$(sed -e 's/"/\\"/g; s=/=\\\/=g; $!s/$/\\n/' "${dir}/CDA_RR.xml" | tr -d '\n')
    eicr=$(sed 's/"/\\"/g; s=/=\\\/=g; $!s/$/\\n/; s/\t/ /g'  "${dir}/CDA_eICR.xml" | tr -d '\n')
    echo "{\"input_type\":\"ecr\", \"root_template\":\"EICR\", \"input_data\": \"$eicr\", \"rr_data\": \"$rr\"}" \
        > /tmp/payload.json
    resp=$(curl -s -X POST -l "${API_URL}/convert-to-fhir" --header "Content-Type: application/json" --data @/tmp/payload.json)
    echo $resp | jq ".response.FhirResource" > $result
done
