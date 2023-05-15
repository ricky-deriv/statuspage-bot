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
        message = f"Incident: {result['name']} is created. \nstatus: {result['status']}"
    except requests.exceptions.HTTPError as err:
        message = f"Operation failed: {r.text}"
    except requests.exceptions.RequestException as err:
        message = f"Operation failed: {err}"
    return message

def get_unresolved_incidents():
    target_url = f"{URL}{PAGE_ID}/incidents/unresolved"
    message = ""
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        message = f"Total unresolved incidents: {len(result)}\n"
        if (len(result) > 0): message += "\t-Incident name- \t-Status- \t-Last updated- \t-Channel ID- \n"
        for incident in result:
            message += f"\n\t{incident['name']} \t{incident['status']} \t{incident['updated_at']} \t{incident['id']}"
    except requests.exceptions.HTTPError as err:
        message = f"Operation failed: {r.text}"
    except requests.exceptions.RequestException as err:
        message = f"Operation failed: {err}"
    return message

def get_incident(incident_id):
    target_url = f"{URL}{PAGE_ID}/incidents/{incident_id}"
    message = ""
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        message = (f"Incident: {result['name']}"
            f"\n\tstatus: {result['status']}"
            f"\n\tcreated at: {result['created_at']}"
            f"\n\tupdated at: {result['updated_at']}")
        for component in result['components']:
            message += f"\n\t\tcomponent: {component['name']} -> {component['status']}"
    except requests.exceptions.HTTPError as err:
        message = f"Operation failed: {r.text}"
    except requests.exceptions.RequestException as err:
        message = f"Operation failed: {err}"
    return message
