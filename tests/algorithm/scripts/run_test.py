import os

from set_configuration import add_configuration
from set_configuration import update_configuration
from set_configuration import check_if_config_already_exists
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
    if check_if_config_already_exists(algorithm_config, api_url):
        update_configuration(algorithm_config, api_url)
    else:
        add_configuration(algorithm_config, api_url)

    # Seed the database
    seed_database(seed_csv, api_url)

    # Send the test records
    send_test_records(test_csv, algorithm_name, api_url)

if __name__ == "__main__":
    main()
