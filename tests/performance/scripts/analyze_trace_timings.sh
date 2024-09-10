#!/bin/bash
# analyze_trace_timings.sh: Script to analyze the timings of the trace logs
#
# Arguments:
# $1: The trace log to analyze
set -e

cd "$(dirname "$0")/.."

TRACE_LOG=${1:-"trace.log"}

# Extract the timings from the trace log
durations=$(jq '.data[].spans[] | select(.operationName == "POST /link-record") | .duration' $TRACE_LOG)

# For each duration, calculate the average, min, and max
for duration in $durations; do
    total=$((total + duration))
    if [[ -z $min || $duration -lt $min ]]; then
        min=$duration
    fi
    if [[ -z $max || $duration -gt $max ]]; then
        max=$duration
    fi
done
# Calculate the average duration and convert values to milliseconds
average=$(bc <<< "scale=2; $total / $(wc -w <<< $durations) / 1000")
min=$(bc <<< "scale=2; $min / 1000")
max=$(bc <<< "scale=2; $max / 1000")

echo "Count: $(wc -w <<< $durations)"
echo "Average duration: $average"
echo "Min duration: $min"
echo "Max duration: $max"
