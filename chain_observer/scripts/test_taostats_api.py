import requests
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

TAOSTATS_API_KEY = os.getenv('TAOSTATS_API_KEY')

def fetch_all_pages(url, headers):
    results = []
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
        data = response.json()
        results.extend(data['subnet_owners'])  
        url = data.get('next')  
    return results

def main():
    url = "https://api.taostats.io/api/v1/subnet/owners?latest=true"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TAOSTATS_API_KEY}"
    }

    try:
        results = fetch_all_pages(url, headers)
        logging.info(results)
    except requests.exceptions.HTTPError as e:
        logging.info(f"HTTPError: {e}")
    except Exception as e:
        logging.info(f"Exception: {e}")

if __name__ == "__main__":
    main()