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

app = App(token=SLACK_BOT_TOKEN)

@app.event("app_mention")
def handle_app_mention_events(body, say, client):
    message_arr = body['event']['text'].split()
    command = " ".join(message_arr[1:3])
    
    commands = {
        "get unresolved": get_unresolved_incidents,
        "get incident": lambda: get_incident(message_arr[3]),
        "update incident": lambda: update_incident(message_arr[3], message_arr[4], " ".join(message_arr[5:])),
    }

    if command in commands:
        message = commands[command]()
        say(message)

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
    incident_description = state_values["description_input"]["description_input"]["value"]
    channel_id = view["private_metadata"]
    
    message = create_incident(incident_name, incident_status, incident_description)
    say(message, channel=channel_id)

def check_allowed_trigger(incident_name, slack_user_id, message):
    """
     allow operation if 
        - channel name starts with incident
        - in the allowed user list
        - message contains the keywords
    """
    allowed_slack_users_id = {'U056F2PDN3G'}
    key_string = 'statuspage declare incident'
    
    return incident_name.startswith('incident') and slack_user_id in allowed_slack_users_id and message == key_string
    
    

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()