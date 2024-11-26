import csv

import requests
from helpers import dict_to_pii


def send_test_records(test_csv, algorithm_name, api_url):
    output_data = []

    print("Sending test records to the API...")

    # Read the CSV file using the csv module
    with open(test_csv, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            # Replace None and "NaN" values with an empty string
            record_data = {k: ("" if v in [None, "NaN"] else v) for k, v in row.items()}

            # Get info from row
            match_info = {
                "test_case_number": record_data['Test Case #'],
                "match_id": record_data['Match Id'],
                "should_match": record_data['Expected Result'],
            }

            pii_record = dict_to_pii(record_data)
            
            response = send_record(pii_record, algorithm_name, api_url)

            if response:
                output_row = {
                    "Test Case #": match_info['test_case_number'],
                    "Expected Result": match_info['should_match'],
                    "Match Result": response['prediction'],
                    "Error": ""
                }
            else:
                output_row = {
                    "Test Case #": match_info['test_case_number'],
                    "Expected Result": match_info['should_match'],
                    "Match Result": "Failed",
                    "Error": "Failed to link record"
                }
            output_data.append(output_row)
    
    # Save output data to the output file
    with open("results/output.csv", mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["Test Case #", "Expected Result", "Match Result", "Error"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(output_data)

    print("Results saved to results/output.csv")

def send_record(pii_record, algorithm_name, api_url):
    """Helper function to send record to the API to be linked."""

    try:
        response = requests.post(f"{api_url}/link", json={"record": pii_record, "algorithm": algorithm_name}) 
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to link record: {e}")
        return None