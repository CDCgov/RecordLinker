#!/bin/sh
#
# Run smoke tests against the API server.
#
# Usage: scripts/smoke_tests.sh <server>
#
# <server> is the URL of the API server to test. If not specified, the tests will
# run against http://localhost:8000.
set -e

cd "$(dirname "$0")/.."

SERVER=${1:-http://localhost:8000}

# Run smoke tests and print the response
JSON_BODY_1='{"record": {"birth_date": "2053-11-07", "sex": "M", "identifiers":[{"value": "123456789", "type": "MR"}], "name":[{"family":"Shepard", "given":["John"]}]}}'
JSON_BODY_2='{"algorithm": "dibbs-enhanced", "record": {"birth_date": "2000-12-06", "sex": "M", "identifiers":[{"value": "9876543210", "type": "MR"}], "name":[{"family":"Smith", "given":["William"]}]}}'

#basic tests
RESPONSE_1=$(curl -s -X POST $SERVER/link \
-d "$JSON_BODY_1" \
-H "Content-Type: application/json")

echo "Response: $RESPONSE_1"
echo "$RESPONSE_1" | jq -e '.prediction == "no_match"' 

PERSON_REFERENCE_ID=$(echo "$RESPONSE_1" | jq -r '.person_reference_id')

RESPONSE_2=$(curl -s -X POST $SERVER/link \
-d "$JSON_BODY_1" \
-H "Content-Type: application/json")

echo "Response: $RESPONSE_2"
echo "$RESPONSE_2" | jq -e '.prediction == "match"'  
echo "$RESPONSE_2" | jq -e --arg id "$PERSON_REFERENCE_ID" '.person_reference_id == $id'

#enhanced tests
RESPONSE_3=$(curl -s -X POST $SERVER/link \
-d "$JSON_BODY_2" \
-H "Content-Type: application/json")

echo "Response: $RESPONSE_3"
echo "$RESPONSE_3" | jq -e '.prediction == "no_match"'  

PERSON_REFERENCE_ID=$(echo "$RESPONSE_3" | jq -r '.person_reference_id')

RESPONSE_4=$(curl -s -X POST $SERVER/link \
-d "$JSON_BODY_2" \
-H "Content-Type: application/json")

echo "Response: $RESPONSE_4"
echo "$RESPONSE_4" | jq -e '.prediction == "match"' 
echo "$RESPONSE_4" | jq -e --arg id "$PERSON_REFERENCE_ID" '.person_reference_id == $id'     

#invalid tests
RESPONSE_5=$(curl -s -X POST $SERVER/link \
-d '{"algorithm": "invalid", "record": {}}' \
-H "Content-Type: application/json")

echo "Response: $RESPONSE_5"
echo "$RESPONSE_5" | grep -q "No algorithm found" 
