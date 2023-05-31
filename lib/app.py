import os
import json
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
        "declare incident": enable_declare_incident,
        "get unresolved": get_unresolved_incidents,
        "get incident": lambda: get_incident(message_arr[3]) if len(message_arr) > 3 else get_incident_by_channel_id(channel_id),
        "update incident": lambda: update_incident_by_channel_id(channel_id, message_arr[3], " ".join(message_arr[4:])),
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

    if(check_allowed_trigger(shortcut['channel']['name'], shortcut['user']['id'], shortcut['message']['text'])):        
         # Update the dropbox for incident status
        for block in form_create_incident['blocks']:
            accessory = block.get('accessory')
            if accessory and accessory.get('action_id') == 'static_select_action':
                block['accessory']['options'].extend([
                    {
                        "text": {"type": "plain_text", "text": status},
                        "value": status
                    }
                    for status in INCIDENT_STATUSES
                ])
            elif accessory and accessory.get('action_id') == 'select_impact':
                block['accessory']['options'].extend([
                    {
                        "text": {"type": "plain_text", "text": impact},
                        "value": impact
                    }
                    for impact in IMPACTS
                ])
        # send the form
        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view=form_create_incident
        )
    else:
        with open('template/not-allowed.json') as file:
            not_allowed = json.load(file)
        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view=not_allowed
        )

@app.view("form_create_incident")
def post_incident(ack, body, client, view, say):
    ack()
    state_values = view["state"]["values"]
    
    incident_name = state_values["incident_name_input"]["incident_name_input"]["value"]
    incident_status = state_values["static_select_action"]["static_select_action"]["selected_option"]["text"]["text"]
    incident_impact = state_values["select_impact"]["select_impact"]["selected_option"]["text"]["text"]
    incident_description = state_values["description_input"]["description_input"]["value"]
    channel_id = view["private_metadata"]
    
    output = create_incident(incident_name, incident_status, incident_impact, channel_id, incident_description)
    say(output['error'] if len(output['error']) > 0 else output['message'], channel=channel_id)

def check_allowed_trigger(incident_name, slack_user_id, message):
    """
     allow operation if 
        - channel name starts with incident
        - in the allowed user list
        - message contains the keywords
    """
    allowed_slack_users_id = {'U056F2PDN3G', 'U05A1LL0BFY'}
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
        '\tupdate the status of or resolve an incident`'
    )

def enable_declare_incident():
    return 'Declaring incident enabled. Use `declare incident` shortcut on this message to declare on status page.'

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()