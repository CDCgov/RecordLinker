import pandas as pd
import requests
from helpers import dict_to_pii


def seed_database(csv_file, api_url):
    df = pd.read_csv(csv_file)
    df = df.where(pd.notnull(df), "")

    MAX_CLUSTERS = 100
    cluster_group = []

    print("Seeding the database...")
    
    for _, row in df.iterrows():
        # Convert the row to a dictionary
        record_data = row.to_dict()

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
