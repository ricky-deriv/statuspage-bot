import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime

from utils import * 

load_dotenv()
URL = 'https://api.statuspage.io/v1/pages/'
API_KEY = os.getenv('STATUSPAGE_API_KEY')
PAGE_ID = os.getenv('STATUSPAGE_PAGE_ID')
HEADERS = {'Authorization': f"OAuth {API_KEY}"}

def create_incident(name, status, impact, channel_id, components_id, components, body):
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
            "components": components,
            "component_ids": components_id
        }  
    }
    try:
        r = requests.post(target_url, headers=HEADERS, json=data)
        result = r.json()
        r.raise_for_status()
        output['message'] = get_incident(result['id'])['message']
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
        
        # get description
        latest_update = {}
        for incident_update in result['incident_updates']:
            created_at = datetime.fromisoformat(incident_update['created_at'].replace("Z", "+00:00"))
            if not latest_update or created_at > datetime.fromisoformat(latest_update['created_at'].replace("Z", "+00:00")):
                latest_update = incident_update
        description = latest_update.get('body', '')
        message += f"\n\tdescription: {description}"

        for component in components:
            message += f"\n\t\tcomponent: {component['name']} -> {component['status']}"
        output['message'] = message
        output['data'] = result
    except requests.exceptions.RequestException as err:
        output['error'] = f"Operation failed: {err}"
    return output

def update_incident(incident_id, status, body):
    # resolve components too if incident is resolved
    output = {"error": "", "message": "", "data": ""}
    target_url = f"{URL}{PAGE_ID}/incidents/{incident_id}"
    components_to_update = {}

    # resolve components if resolving incident
    if status == "resolved":
        incident = get_incident(incident_id)['data']
        components = incident.get('components', [])
        component_ids = [component['id'] for component in components]
        for component_id in component_ids:
            components_to_update[component_id] = "operational"
    data = {
        "incident": {
            "status": status,
            "body": body,
            "components": components_to_update
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
    output = {"error": "", "message": "Components' status", "data": ""}
    target_url = f"{URL}{PAGE_ID}/components"
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        output['data'] = result
        for component in result:
            output['message'] += f"\n\t {component['name']} -> {component['status']}"
    except requests.exceptions.RequestException as err:
        output['error'] = f"Operation failed: {err}"
    return output

def get_component_by_name(component_name):
    component_name = component_name.lower()
    output = {"error": "", "message": "", "data": ""}
    components_result = get_components()
    if components_result['error']:
        output['error'] = components_result['error']
    else:
        components = components_result['data']
        # find component by name
        for component in components:
            if component['name'].lower() == component_name:
                output['data'] = component
                output['message'] = f"Component: {component['name']} -> {component['status']}"
                break
    return output


def update_component_by_name(component_name, status):
    output = {"error": "", "message": "", "data": ""}
    component_result = get_component_by_name(component_name)
    if component_result['data']:
        component_id = component_result['data']['id']
        target_url = f"{URL}{PAGE_ID}/components/{component_id}"
        data = {
            "component": {
                "status": status
            }  
        }
        try:
            r = requests.put(target_url, headers=HEADERS, json=data)
            result = r.json()
            r.raise_for_status()
            output['message'] = f"Component update: {result['name']} -> {result['status']}"
        except requests.exceptions.RequestException as err:
            output['error'] = f"Operation failed: {err}"
    else:
        output['error'] = component_result['error'] if component_result['error'] else f"Component {component_name} not found" 
    return output

# function to list available templates
# outputs a list of templates (template name)
def get_templates():
    output = {"error": "", "message": "", "data": ""}
    target_url = f"{URL}{PAGE_ID}/incident_templates"
    output['message'] = "Available templates:"
    try:
        r = requests.get(target_url, headers=HEADERS)
        result = r.json()
        r.raise_for_status()
        output['data'] = result
        for template in result:
            output['message'] += f"\n- {template['name']}"
            output['message'] += f"\n\ttitle: {template['title']}"
    except requests.exceptions.RequestException as err:
        output['error'] = f"Operation failed: {err}"
    return output

# function to get details of a template
# there's no api call to get a detail of a template
# basically, calling the same list of templates to get details of a template

# update create incident function
"""
    if there is a template-in-use,
    -> get the template
    -> custom the create incident request using the data from the template
"""

