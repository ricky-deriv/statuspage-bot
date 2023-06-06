import requests
import os
import json
from dotenv import load_dotenv

from utils import * 

load_dotenv()
URL = 'https://api.statuspage.io/v1/pages/'
API_KEY = os.getenv('STATUSPAGE_API_KEY')
PAGE_ID = os.getenv('STATUSPAGE_PAGE_ID')
HEADERS = {'Authorization': f"OAuth {API_KEY}"}

def create_incident(name, status, impact, channel_id, components, body):
    output = {"error": "", "message": "", "data": ""}
    target_url = f"{URL}{PAGE_ID}/incidents"
    metadata = {"slack": {"channel_id": channel_id}  }
    data = {
        "incident": {
            "name": name,
            "status": status,
            "body": body,
            "metadata": metadata,
            "impact_override": impact,
            "components": components
        }  
    }
    try:
        r = requests.post(target_url, headers=HEADERS, json=data)
        result = r.json()
        r.raise_for_status()
        output['message'] = f"Incident `{result['name']}` is created. \nstatus: {result['status']} \nimpact: {result['impact']}"
    except requests.exceptions.RequestException as err:
        output['error'] = f"Operation failed: {err}"
    return output

def get_unresolved_incidents():
    output = {"error": "", "message": "", "data": ""}
    target_url = f"{URL}{PAGE_ID}/incidents/unresolved"
    table_data = []
    table_data.append(['Incident ID', 'Incident Name', 'Status', 'Last Updated'])
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        message = f"Total unresolved incidents: {len(result)}"
        if len(result) > 0:
            for incident in result:
                table_data.append([incident['id'], incident['name'], incident['status'], convert_utc_to_gmt8(incident['updated_at'])])
            message += create_table(table_data)
        output['message'] = message
        output['data'] = result
    except requests.exceptions.RequestException as err:
        output['error'] = f"Operation failed: {err}"
    return output

def get_incident(incident_id):
    output = {"error": "", "message": "", "data": ""}
    target_url = f"{URL}{PAGE_ID}/incidents/{incident_id}"
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        message = ( f"Incident: {result['name']}"
                    f"\n\tstatus: {result['status']}"
                    f"\n\timpact: {result['impact']}"
                    f"\n\tcreated at: {convert_utc_to_gmt8(result['created_at'])}"
                    f"\n\tupdated at: {convert_utc_to_gmt8(result['updated_at'])}" )
        components = result.get('components', [])
        for component in components:
            message += f"\n\t\tcomponent: {component['name']} -> {component['status']}"
        output['message'] = message
    except requests.exceptions.RequestException as err:
        output['error'] = f"Operation failed: {err}"
    return output

def update_incident(incident_id, status, body):
    # resolve components too if incident is resolved
    output = {"error": "", "message": "", "data": ""}
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
        output['message'] = message
    except requests.exceptions.RequestException as err:
        output['error'] = f"Operation failed: {err}"
    return output

def get_unresolved_incident_id_by_channel_id(channel_id):
    unresolved_incidents = get_unresolved_incidents()['data']
    
    for incident in unresolved_incidents:
        if incident['metadata'].get('slack', {}).get('channel_id') == channel_id:
            return incident['id']
    
    return "channel not linked to any incident"

def get_incident_by_channel_id(channel_id):
    incident_id = get_unresolved_incident_id_by_channel_id(channel_id)
    return get_incident(incident_id)

def update_incident_by_channel_id(channel_id, status, body):
    incident_id = get_unresolved_incident_id_by_channel_id(channel_id)
    return update_incident(incident_id, status, body)

def get_components():
    output = {"error": "", "message": "", "data": ""}
    target_url = f"{URL}{PAGE_ID}/components"
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        output['data'] = result
    except requests.exceptions.RequestException as err:
        output['error'] = f"Operation failed: {err}"
    return output