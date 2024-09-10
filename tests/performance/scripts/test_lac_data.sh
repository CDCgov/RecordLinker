#!/bin/bash
# test_lac_data.sh: Script to link LAC data using the linkage API
#
# Usage: link_lac_data.sh
set -e

cd "$(dirname "$0")/.."


# TRUNCATE THE DATABASE
scripts/reset_db.sh $DB_URL


# EXTRACT ECR DATA FROM LAC DATA
scripts/extract_lac_data.sh $LAC_DATA_ZIP $LAC_ECR_DATA


# SEND ECR DATA TO THE FHIR CONVERTER API
scripts/send_fhir_requests.sh $LAC_ECR_DATA $FHIR_API_URL $LAC_FHIR_DATA


# SEND ECR DATA TO THE LINKAGE API
scripts/send_linkage_requests.sh $LAC_FHIR_DATA $LINKAGE_API_URL $ITERATIONS


# HANG THE SCRIPT
# This will keep the script running indefinitely, allowing you to inspect the
# database and Jaeger UI for traces. Press CTRL+C to exit.
echo -e "\n\nFinished.  Click CTRL+C to exit."
while true; do sleep 1; done
