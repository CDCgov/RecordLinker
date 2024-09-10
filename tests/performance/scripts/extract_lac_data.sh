#!/bin/bash
# extract_lac_data.sh: Script to extract ECR from LAC data
#
# Arguments:
# $1: The LAC data zip file to extract
# $2: The output directory to save the extracted ECR data to
set -e

cd "$(dirname "$0")/.."

FILE=${1:-"LAC_DATA.zip"}
OUTPUT_DIR=${2:-"ECR_DATA"}


cleanup() {
    # Clean up the temporary directory
    rm -rf /tmp/LAC_DATA
}
trap cleanup EXIT

# Unzip the LAC data to a temporary directory
echo "Unzipping LAC data to /tmp/LAC_DATA"
unzip -q -o $FILE -d "/tmp/"

# Unzip zipped ECR data to a temporary directory using a
# directory structure with the same name as the zip file
# Then move the ECR data to the output directory.
for file in $(ls -1 /tmp/LAC_DATA/*.zip); do
    dir="${OUTPUT_DIR}/$(basename $file .zip)"
    if [ -d $dir ]; then continue; fi  # Skip if the dir already exists

    mkdir -p $dir
    unzip -o $file -d $dir
done
