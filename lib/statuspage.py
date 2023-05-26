import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
    try:
        r = requests.post(target_url, headers=HEADERS, json=data)
        result = r.json()
        r.raise_for_status()
        message = f"Incident {result['id']}: {result['name']} is created. \nstatus: {result['status']}"
    except requests.exceptions.RequestException as err:
        message = f"Operation failed: {err}"
    return message

def get_unresolved_incidents():
    target_url = f"{URL}{PAGE_ID}/incidents/unresolved"
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        message = f"Total unresolved incidents: {len(result)}\n"
        if len(result) > 0:
            message += "\t-Incident name- \t-Status- \t-Last updated- \t-Channel ID- \n"
            for incident in result:
                message += f"\n\t{incident['name']} \t{incident['status']} \t{convert_utc_to_gmt8(incident['updated_at'])} \t{incident['id']}"
    except requests.exceptions.RequestException as err:
        message = f"Operation failed: {err}"
    return message

def get_incident(incident_id):
    target_url = f"{URL}{PAGE_ID}/incidents/{incident_id}"
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        message = ( f"Incident: {result['name']}"
                    f"\n\tstatus: {result['status']}"
                    f"\n\tcreated at: {convert_utc_to_gmt8(result['created_at'])}"
                    f"\n\tupdated at: {convert_utc_to_gmt8(result['updated_at'])}")
        components = result.get('components', [])
        for component in components:
            message += f"\n\t\tcomponent: {component['name']} -> {component['status']}"
    except requests.exceptions.RequestException as err:
        message = f"Operation failed: {err}"
    return message

def update_incident(incident_id, status, body):
    target_url = f"{URL}{PAGE_ID}/incidents/{incident_id}"
    data = {
        "incident": {
            "status": status,
            "body": body
        }  
    }
    try:
        r = requests.patch(target_url, headers=HEADERS, json=data)
        result = r.json()
        r.raise_for_status()
        message = ( f"Incident: {result['name']}"
                    f"\n\tstatus: {result['status']}")
    except requests.exceptions.RequestException as err:
        message = f"Operation failed: {err}"
    return message

def convert_utc_to_gmt8(utc_datetime):
    utc_time = datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%SZ")
    gmt_plus_8_time = utc_time + timedelta(hours=8)
    gmt_plus_8_time_str = gmt_plus_8_time.strftime("%Y-%m-%d %H:%M:%S")
    return gmt_plus_8_time_str