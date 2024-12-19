import os

import requests


def reset_db(api_url):
    print("Resetting the database...")
    try:
        response = requests.delete(f"{api_url}/seed") 
        response.raise_for_status()  # Raise an error for bad status codes
        print("Database reset successfully")
    except requests.exceptions.RequestException as e:
        print(f"Failed to reset the database: {e}")


if __name__ == "__main__":
    api_url = os.getenv("API_URL")
    reset_db(api_url)
