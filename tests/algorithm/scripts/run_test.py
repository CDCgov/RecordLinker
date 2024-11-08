import os

from add_configuration import add_configuration
from helpers import load_json
from seed_db import seed_database
from send_test_records import send_test_records


def main():  
    # Get the environment variables
    api_url = os.getenv("API_URL")
    algorithm_name = os.getenv("ALGORITHM_NAME")
    algorithm_config_file = os.getenv("ALGORITHM_CONFIGURATION")
    seed_csv = os.getenv("SEED_FILE")
    test_csv = os.getenv("TEST_FILE")


    # Load the JSON for the algorithm configuration
    algorithm_config = load_json(algorithm_config_file)

    if algorithm_config:
        add_configuration(algorithm_config, api_url)

    # Seed the database
    seed_database(seed_csv, api_url)

    # Send the test records
    send_test_records(test_csv, algorithm_name, api_url)

if __name__ == "__main__":
    main()
