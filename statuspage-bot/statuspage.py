import requests
import os
from dotenv import load_dotenv

load_dotenv()
URL = 'https://api.statuspage.io/v1/pages/'
API_KEY = os.getenv('STATUSPAGE_API_KEY')
PAGE_ID = os.getenv('STATUSPAGE_PAGE_ID')
HEADERS = {'Authorization': f"OAuth {API_KEY}"}

def create_incident(name, status, body):
    target_url = f"{URL}{PAGE_ID}/incidents"
    data = {
        "incident": {
            "name": name,
            "status": status,
            "body": body
        }  
    }
    message = ""
    try:
        r = requests.post(target_url, headers=HEADERS, json=data)
        result = r.json()
        r.raise_for_status()
        message = f"Incident {result['name']} created"
    except requests.exceptions.HTTPError as err:
        message = f"Operation failed: {r.text}"
    except requests.exceptions.RequestException as err:
        message = f"Operation failed: {err}"
    return message
