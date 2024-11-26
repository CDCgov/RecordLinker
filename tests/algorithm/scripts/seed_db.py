import csv

import requests
from helpers import dict_to_pii


def seed_database(csv_file, api_url):
    MAX_CLUSTERS = 100
    cluster_group = []

    print("Seeding the database...")

     # Read the CSV file using the csv module
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            record_data = {k: ("" if v in [None, "NaN"] else v) for k, v in row.items()}

            # convert dict to a pii_record
            pii_record = dict_to_pii(record_data)

            # nesting for the seeding api request
            cluster = {"records": [pii_record]}
            cluster_group.append(cluster)

            if len(cluster_group) == MAX_CLUSTERS:
                send_clusters_to_api(cluster_group, api_url)
                cluster_group = []

    if cluster_group:
        send_clusters_to_api(cluster_group, api_url)
    
    print("Finished seeding the database.")


def send_clusters_to_api(cluster_group, api_url):
    """Helper function to send a batch of clusters to the API."""
    try:
        response = requests.post(f"{api_url}/seed", json={"clusters": cluster_group})
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Failed to post batch: {e}")
