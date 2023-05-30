import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

from utils import * 

load_dotenv()
URL = 'https://api.statuspage.io/v1/pages/'
API_KEY = os.getenv('STATUSPAGE_API_KEY')
PAGE_ID = os.getenv('STATUSPAGE_PAGE_ID')
HEADERS = {'Authorization': f"OAuth {API_KEY}"}

# todo: add search incident id based on metadata.slack.channel_id
# allow update operation only if metadata channel id matches the slack request from channel_id
# this to remove using incident id as identifier

def create_incident(name, status, channel_id, body):
    target_url = f"{URL}{PAGE_ID}/incidents"
    metadata = {"slack": {"channel_id": channel_id}  }
    data = {
        "incident": {
            "name": name,
            "status": status,
            "body": body,
            "metadata": metadata
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
    table_data = []
    table_data.append(['Incident Name', 'Status', 'Last Updated', 'Channel ID', 'Slack channel id'])
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        message = f"Total unresolved incidents: {len(result)}\n"
        if len(result) > 0:
            for incident in result:
                table_data.append([incident['name'], incident['status'], convert_utc_to_gmt8(incident['updated_at']), incident['id'], incident['metadata']['slack']['channel_id']])
            message += create_table(table_data)
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