import requests


def add_configuration(algorithm_config, api_url):
    """Add configuration to the algorithm."""

    if algorithm_config is None:
        print("Failed to load configuration")
        return
    try:
        response = requests.post(f"{api_url}/algorithm", json=algorithm_config)
        response.raise_for_status()  # Raise an error for bad status codes
        print(f"Successfully added algorithm configuration {algorithm_config["label"]}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to add configuration: {e}")
