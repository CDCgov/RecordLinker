#!/bin/bash
#
# Run an example of linkage tests against the API server.
#
# Usage: scripts/example_linkage_tests.sh <server>
# Requires: curl, python3
#
# <server> is the base url of the API server to test. If not specified, the tests will
# run against http://localhost:8080/api.
set -e

cd "$(dirname "$0")/.."

SERVER=${1:-http://localhost:8080/api}

# Algorithm
ALGORITHM=$(cat <<'EOF'
{
    "label": "linkage-test",
    "is_default": false,
    "algorithm_context": {
      "include_multiple_matches": true,
      "log_odds": [
        { "feature": "ADDRESS", "value": 8 },
        { "feature": "BIRTHDATE", "value": 10 },
        { "feature": "FIRST_NAME", "value": 7 },
        { "feature": "LAST_NAME", "value": 6 },
        { "feature": "IDENTIFIER", "value": 1 },
        { "feature": "SEX", "value": 1 },
        { "feature": "ZIP", "value": 5 }
      ],
      "skip_values": [
          {
              "feature": "FIRST_NAME",
              "values": [
                  "Anon",
                  "Anonymous"
              ]
          },
          {
              "feature": "LAST_NAME",
              "values": [
                  "Anon",
                  "Anonymous"
              ]
          },
          {
              "feature": "NAME",
              "values": [
                  "John Doe",
                  "Jane Doe",
                  "Baby Boy",
                  "Baby Girl"
              ]
          },
          {
              "feature": "*",
              "values": [
                  "Unk",
                  "Unknown"
              ]
          }
      ],
      "advanced": {
        "fuzzy_match_threshold": 0.9,
        "fuzzy_match_measure": "JaroWinkler",
        "max_missing_allowed_proportion": 0.5,
        "missing_field_points_proportion": 0.5
      }
    },
    "passes": [
        {
            "label": "BLOCK_birthdate_identifier_sex_MATCH_first_name_last_name",
            "blocking_keys": [
                "BIRTHDATE",
                "IDENTIFIER",
                "SEX"
            ],
            "evaluators": [
                {
                    "feature": "FIRST_NAME",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"
                },
                {
                    "feature": "LAST_NAME",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"
                }
            ],
            "possible_match_window": [
                0.8,
                0.95
            ]
        },
        {
            "label": "BLOCK_zip_first_name_last_name_sex_MATCH_address_birthdate",
            "blocking_keys": [
                "ZIP",
                "FIRST_NAME",
                "LAST_NAME"
            ],
            "evaluators": [
                {
                    "feature": "ADDRESS",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"
                },
                {
                    "feature": "BIRTHDATE",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                    "fuzzy_match_threshold": 0.95
                }
            ],
            "possible_match_window": [
                0.75,
                0.9
            ]
        }
    ]
}
EOF
)

# Initial data to seed
SEED=$(cat <<'EOF'
{
    "clusters": [
        {
            "records": [
                {
                    "external_id": "1",
                    "birth_date": "1967-06-06",
                    "sex": "F",
                    "address": [{"line": ["4268 Greenmeadow Lane"], "zip": "11749"}],
                    "name": [{"given": ["Patricia"], "family": "Hath"}],
                    "identifiers": [{"type": "SS", "value": "135798642"}]
                },
                {
                    "external_id": "4",
                    "birth_date": "1967-06-06",
                    "sex": "F",
                    "address": [{"zip": "11749"}],
                    "name": [{"given": ["Patricia"], "family": "Hathway"}],
                    "identifiers": [{"type": "SS", "value": "135798642"}]
                }
            ],
            "external_person_id": "A"
        },
        {
            "records": [
                {
                    "external_id": "2",
                    "birth_date": "1967-06-01",
                    "address": [{"line": ["4268 Greenmeadow Lane"], "zip": "11749"}],
                    "name": [{"given": ["Patrick"], "family": "Hathaway"}],
                    "identifiers": [{"type": "SS", "value": "567812340"}]
                },
                {
                    "external_id": "3",
                    "birth_date": "1967-06-01",
                    "sex": "M",
                    "address": [{"line": ["4268 Greenmeadow Lane"], "zip": "11749"}],
                    "name": [{"given": ["Pat"], "family": "Hathaway"}],
                    "identifiers": [{"type": "SS", "value": "567812340"}]
                }
            ],
            "external_person_id": "B"
        },
        {
            "records": [
                {
                    "external_id": "5",
                    "birth_date": "1967-06-06",
                    "sex": "F",
                    "address": [{"line": ["643 Mount Pleasant Ave."], "zip": "44389"}],
                    "name": [{"given": ["Patrice"], "family": "Hathwaite"}],
                    "identifiers": [{"type": "SS", "value": "449908642"}]
                }
            ],
            "external_person_id": "C"
        }
    ]
}
EOF
)

# Record to link
RECORD=$(cat <<'EOF'
{
    "record": {
        "birth_date": "1967-06-06",
        "sex": "F",
        "address": [{"zip": "11749"}],
        "name": [{"family": "Hathaway", "given": ["Patrice"]}],
        "identifiers": [{"type": "SS", "value": "135798642"}]
    },
    "algorithm": "linkage-test"
}
EOF
)

http_request() {
    URL=$1
    METHOD=$2
    DATA=$3

    # Prepare curl command
    if [ -n "$DATA" ]; then
        HTTP_RESPONSE=$(curl -s -X "$METHOD" -w "\n%{http_code}" -H "Content-Type: application/json" -d "$DATA" "$URL")
    else
        HTTP_RESPONSE=$(curl -s -X "$METHOD" -w "\n%{http_code}" -H "Content-Type: application/json" "$URL")
    fi

    # Separate response body and HTTP status code
    HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tail -n1)
    RESPONSE_BODY=$(echo "$HTTP_RESPONSE" | sed '$d')

    echo "$HTTP_STATUS" "$RESPONSE_BODY"
}

assert_status_code() {
    HTTP_STATUS=$1
    EXPECTED_STATUS=$2
    if [ "$HTTP_STATUS" -ne "$EXPECTED_STATUS" ]; then
        echo "Expected status code $EXPECTED_STATUS, but got $HTTP_STATUS"
        exit 1
    fi
}

echo "LIST THE ALGORITHMS..."
read -r HTTP_STATUS RESPONSE_BODY <<< "$(http_request "${SERVER}/algorithm" "GET")"
assert_status_code "$HTTP_STATUS" "200"

echo "OPTIONALLY DELETE LINKAGE-TEST ALGORITHM..."
http_request "${SERVER}/algorithm/linkage-test" "DELETE" > /dev/null

echo "CREATE LINKAGE-TEST ALGORITHM..."
read -r HTTP_STATUS RESPONSE_BODY <<< "$(http_request "${SERVER}/algorithm" "POST" "$ALGORITHM")"
assert_status_code "$HTTP_STATUS" "201"

echo "RESET THE DATABASE..."
read -r HTTP_STATUS RESPONSE_BODY <<< "$(http_request "${SERVER}/seed" "DELETE")"
assert_status_code "$HTTP_STATUS" "204"

echo "SEED THE DATABASE..."
read -r HTTP_STATUS RESPONSE_BODY <<< "$(http_request "${SERVER}/seed" "POST" "$SEED")"
assert_status_code "$HTTP_STATUS" "201"
echo "$RESPONSE_BODY" | python3 -c '
import sys, json
data = json.load(sys.stdin)
for p in data.get("persons", []): p.pop("patients", None)
json.dump(data, sys.stdout, indent=2)
'

echo "LINK RECORD..."
read -r HTTP_STATUS RESPONSE_BODY <<< "$(http_request "${SERVER}/link" "POST" "$RECORD")"
assert_status_code "$HTTP_STATUS" "200"
echo "$RESPONSE_BODY" | python3 -m json.tool

PATIENT_ID=$(echo "$RESPONSE_BODY" | python3 -c 'import sys, json; print(json.load(sys.stdin)["patient_reference_id"])')
PERSON_A_ID=$(echo "$RESPONSE_BODY" | python3 -c 'import sys, json; print(json.load(sys.stdin)["results"][0]["person_reference_id"])')

echo "ASSIGN RECORD TO CLUSTER..."
read -r HTTP_STATUS RESPONSE_BODY <<< "$(http_request "${SERVER}/person/${PERSON_A_ID}" "PATCH" "{\"patients\": [\"${PATIENT_ID}\"]}")"
assert_status_code "$HTTP_STATUS" "200"

echo "CREATE CALIBRATION JOB..."
read -r HTTP_STATUS RESPONSE_BODY <<< "$(http_request "${SERVER}/calibration/test" "POST" "{\"delay\": 120}")"
assert_status_code "$HTTP_STATUS" "202"
echo "$RESPONSE_BODY" | python3 -m json.tool
JOB_ID=$(echo "$RESPONSE_BODY" | python3 -c 'import sys, json; print(json.load(sys.stdin)["id"])')

echo "GET JOB STATUS..."
while true; do
    read -r HTTP_STATUS RESPONSE_BODY <<< "$(http_request "${SERVER}/calibration/test/${JOB_ID}" "GET")"
    assert_status_code "$HTTP_STATUS" "200"
    STATUS=$(echo "$RESPONSE_BODY" | python3 -c 'import sys, json; print(json.load(sys.stdin)["status"])')
    if [ "$STATUS" == "completed" ]; then
        echo "CALIBRATION JOB COMPLETED"
        echo "$RESPONSE_BODY" | python3 -m json.tool
        break
    fi
    sleep 1
done
