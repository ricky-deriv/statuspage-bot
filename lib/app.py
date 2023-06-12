import os
import json
import copy
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from statuspage import *

load_dotenv()
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')

# global arrays
INCIDENT_STATUSES = ['investigating', 'identified', 'monitoring', 'resolved', 'scheduled', 'in_progress', 'verifying', 'completed']
IMPACTS = ['none', 'maintenance', 'minor', 'major', 'critical']

app = App(token=SLACK_BOT_TOKEN)

@app.event("app_mention")
def handle_app_mention_events(body, say, client):
    message_arr = body['event']['text'].split()
    channel_id = body['event']['channel']
    command = " ".join(message_arr[1:3])
    
    commands = {
        "declare incident": lambda: enable_declare_incident(channel_id),
        "get unresolved": get_unresolved_incidents,
        "get incident": lambda: get_incident(message_arr[3]) if len(message_arr) > 3 else get_incident_by_channel_id(channel_id),
        "update incident": lambda: update_incident_by_channel_id(channel_id, message_arr[3], " ".join(message_arr[4:])),
        "get components": get_components,
        "update component": lambda: update_component_by_name(" ".join(message_arr[3:-1]), message_arr[-1]),
        "get templates": get_templates,
        "get template": lambda: get_template(" ".join(message_arr[3:])),
        "help": get_help,
    }

    if command == "help" or command == "declare incident":
        message = commands[command]()
        say(message)
    elif command in commands:
        output = commands[command]()
        say(f"```\n{output['error'] if len(output['error']) > 0 else output['message']}\n```")
    else:
        say(f"```command not found. use `help` to list commands.```")

@app.shortcut("declare_incident")
def declare_incident(ack, shortcut, client):
    ack()
    channel_id = shortcut['channel']['id']

    with open('template/incident-form.json') as file:
        form_create_incident = json.load(file)
    form_create_incident['private_metadata'] = channel_id

    if(check_allowed_trigger(shortcut['channel']['name'], shortcut['user']['id'], shortcut['message']['text']) and not check_channel_has_incident_attached(channel_id)):    
        form_create_incident = add_inputs_incident_form(form_create_incident)
        client.views_open(trigger_id=shortcut["trigger_id"], view=form_create_incident)
    else:
        with open('template/not-allowed.json') as file:
            not_allowed = json.load(file)
        if check_channel_has_incident_attached(channel_id):
            for block in not_allowed['blocks']:
                if block['block_id'] == 'text_message':
                    block['text']['text'] += '\nThis channel is attached to an unresolved incident.\nUse another channel to declare the incident or resolve the incident in this channel.'
        client.views_open(trigger_id=shortcut["trigger_id"], view=not_allowed)

@app.view("form_create_incident")
def post_incident(ack, body, client, view, say):
    ack()
    state_values = view["state"]["values"]
    affected_components = {}
    affected_components_id = []

    incident_name = state_values["incident_name_input"]["incident_name_input"]["value"]
    incident_status = state_values["select_status"]["select_status"]["selected_option"]
    incident_description = state_values["description_input"]["description_input"]["value"]

    if incident_status:
        incident_status = state_values["select_status"]["select_status"]["selected_option"]["text"]["text"]
    if not (incident_name and incident_status and incident_description):
        blocks = view['blocks']
        for block in blocks:
            if block['block_id'] == 'incident_name_input' and not incident_name:
                incident_name = block['element']['initial_value']
            elif block['block_id'] == 'select_status' and not incident_status:
                incident_status = block['element']['initial_option']['value']
            elif block['block_id'] == 'description_input' and not incident_description:
                incident_description = block['element']['initial_value']

    incident_impact = state_values["select_impact"]["select_impact"]["selected_option"]["text"]["text"]
    channel_id = view["private_metadata"]
    # get affected components
    for block_id in state_values:
        if block_id.startswith("select_status_component"):
            component_id = block_id.split("_")[-1]
            if state_values[block_id][block_id]["selected_option"]: 
                affected_components_id.append(component_id)
                affected_components[component_id] = state_values[block_id][block_id]["selected_option"]["text"]["text"]
    
    output = create_incident(incident_name, incident_status, incident_impact, channel_id, affected_components_id, affected_components,incident_description)
    say(f"```\n{output['error'] if len(output['error']) > 0 else output['message']}\n```", channel=channel_id)

@app.action("select_template")
def update_form_on_template(ack, body, client):
    ack()
    
    with open('template/incident-form.json') as file:
        form_create_incident = json.load(file)
    form_create_incident['blocks'] = body['view']['blocks']
    form_create_incident['private_metadata'] = body['view']['private_metadata']

    # update modal with data from template
    selected_template_name = body['actions'][0]['selected_option']['value']
    template = get_template(selected_template_name)
    if not template['error']:
        template = template['data']
        for block in form_create_incident['blocks']:
            # update incident name
            if block['block_id'] == 'incident_name_input':
                block['element']['initial_value'] = template['name']
            elif block['block_id'] == 'select_status':
                # update incident status
                # set default menu option
                for option in block['element']['options']:
                    if option['value'] == template['update_status']:
                        block['element']['initial_option'] = option
                        break
            elif block['block_id'] == 'description_input':
                # update incident description
                block['element']['initial_value'] = template['body']            
            elif block['block_id'].startswith('select_status_component'):
                # update affected components
                for component in template['components']:
                    if block['block_id'].split("_")[-1] == component['id']:
                        for option in block['element']['options']:
                            if option['value'] == component['status']:
                                block['element']['initial_option'] = option
                                break
    
    client.views_update(
        view_id=body['view']['id'],
        hash=body['view']['hash'],
        view=form_create_incident
    )

def check_allowed_trigger(incident_name, slack_user_id, message):
    """
     allow operation if 
        - channel name starts with incident
        - in the allowed user list
        - message contains the keywords
    """
    with open('lib/.allowed_ids.json') as file:
        allowed_slack_users = json.load(file)
    allowed_slack_users_id = set(allowed_slack_users.values())
    key_string = 'Declaring incident enabled. Use `declare incident` shortcut on this message to declare on status page.'
    
    return incident_name.startswith('incident') and slack_user_id in allowed_slack_users_id and message == key_string
    
def get_help():
    return (
        'Message shortcut:\n'
        '`statuspage declare incident`:\n'
        '\tenable `declare incident` shortcut on the message\n\n'
        'Commands `@test-statuspage-bot <commands>`:\n'
        '`get unresolved`:\n'
        '\tget unresolved incidents\n'
        '`get incident`:\n'
        '\tget info of an incident\n'
        '`update incident <status> [description]`:\n'
        '\tupdate the status of or resolve an incident. Resolving an incident resolves the affected components too.\n'
        '`get components`:\n'
        '\tget status of all components\n'
        '`update component <name> <status>`:\n'
        '\tupdate the status of a component. status can be `operational`, `degraded_performance`, `partial_outage`, `major_outage`, `under_maintenance`. the name of component is not case sensitive.\n'
        '`get templates`:\n'
        '\tget all incident templates\' name and title\n'
        '`get template <name>`:\n'
        '\tget the details of the incident template. The name of template is not case sensitive.\n'
    )

def enable_declare_incident(channel_id):
    # check if an unresolved incident is attached to this channel
    if check_channel_has_incident_attached(channel_id):
        return 'Declaring incident `rejected`. This channel is attached to an unresolved incident.\nUse another channel to declare the incident or resolve the incident in this channel.'
    return 'Declaring incident enabled. Use `declare incident` shortcut on this message to declare on status page.'

def check_channel_has_incident_attached(channel_id):
    unresolved_incidents = get_unresolved_incidents()
    return any(incident['metadata'].get('slack', {}).get('channel_id', "") == channel_id for incident in unresolved_incidents.get('data', []))


def add_inputs_incident_form(form_create_incident):
    for block in form_create_incident['blocks']:
        # add status options
        if block.get('block_id') == 'select_status':
            block['element']['options'].extend([
                {
                    "text": {"type": "plain_text", "text": status},
                    "value": status
                }
                for status in INCIDENT_STATUSES
            ])
        # add impact options
        elif block.get('block_id') == 'select_impact':
            block['element']['options'].extend([
                {
                    "text": {"type": "plain_text", "text": impact},
                    "value": impact
                }
                for impact in IMPACTS
            ])
        # add template options
        elif block.get('block_id') == 'select_template':
            templates_result = get_templates()
            if templates_result['error'] == '':
                templates = templates_result['data']
                block['accessory']['options'].extend([
                    {
                        "text": {"type": "plain_text", "text": template['name']},
                        "value": template['name']
                    }
                    for template in templates
                ])

    # add components options
    components_result = get_components()
    if components_result['error'] == '':
        with open('template/component-status-select.json') as file:
            component_status_select_template = json.load(file)
        components = components_result['data']
        for component in components:
            identifier = component['id']
            component_status_select = copy.deepcopy(component_status_select_template)
            component_status_select['block_id'] += f"_{identifier}"
            component_status_select['element']['action_id'] += f"_{identifier}"
            component_status_select['label']['text'] = component['name']
            form_create_incident['blocks'].append(component_status_select) 
        
    return form_create_incident

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()