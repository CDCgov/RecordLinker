import requests


def add_configuration(algorithm_config, api_url):
    """Add configuration to the algorithm."""

    if algorithm_config is None:
        print("Failed to load configuration")
        return
    try:
        response = requests.post(f"{api_url}/algorithm", json=algorithm_config)
        response.raise_for_status()  # Raise an error for bad status codes
        print(f"Successfully added algorithm configuration {algorithm_config["label"]}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to add configuration: {e}")

def update_configuration(algorithm_config, api_url):
    """Update an algorithm configuration."""

    if algorithm_config is None:
        print("Failed to load configuration")
        return
    try:
        response = requests.put(f"{api_url}/algorithm/{algorithm_config["label"]}", json=algorithm_config)
        response.raise_for_status()  # Raise an error for bad status codes
        print(f"Successfully updated algorithm configuration {algorithm_config["label"]}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to update algorithm configuration: {e}")

def check_if_config_already_exists(algorithm_config, api_url):
    """Check if the configuration already exists in the algorithm."""
    try:
        response = requests.get(f"{api_url}/algorithm/{algorithm_config["label"]}")
        response.raise_for_status()  # Raise an error for bad status codes
        return True
    except requests.exceptions.RequestException:
        return False
