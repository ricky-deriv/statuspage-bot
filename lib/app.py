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
    print('new request...')

    if f"{message_arr[1]} {message_arr[2]}" == "get unresolved":
        message = get_unresolved_incidents()
        say(message)
    elif f"{message_arr[1]} {message_arr[2]}" == "get incident":
        message = get_incident(message_arr[3])
        say(message)
    elif f"{message_arr[1]} {message_arr[2]}" == "update incident":
        body = ' '.join(message_arr[5:])
        message = update_incident(message_arr[3], message_arr[4], body)
        say(message)

@app.shortcut("declare_incident")
def declare_incident(ack, shortcut, client):
    ack()
    channel_id = shortcut['channel']['id']
    with open('template/incident-form.json') as file:
        form_create_incident = json.load(file)
    form_create_incident['private_metadata'] = channel_id

    if(check_allowed_trigger(shortcut['channel']['name'], shortcut['user']['id'], shortcut['message']['text'])):
        print('yes, youre allwoed')
        # access the view object and update the dropbox for incident status
        index = 0
        for block in form_create_incident['blocks']:
            if ('accessory' in block):
                if (block['accessory']['action_id'] == 'static_select_action'):
                    for status in INCIDENT_STATUSES:
                        form_create_incident['blocks'][index]['accessory']['options'].append({
                            "text": {"type": "plain_text", "text": status},
                            "value": status
                        })
            index += 1
        # send the form
        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view=form_create_incident
        )
    else:
        print('nope, not allowed')
        with open('template/not-allowed.json') as file:
            not_allowed = json.load(file)
        client.views_open(
        trigger_id=shortcut["trigger_id"],
        view=not_allowed
    )

@app.view("form_create_incident")
def post_incident(ack, body, client, view, say):
    ack()
    incident_name = view["state"]["values"]["incident_name_input"]["incident_name_input"]['value']
    incident_status = view['state']['values']['static_select_action']['static_select_action']['selected_option']['text']['text']
    incident_description = view['state']['values']['description_input']['description_input']['value']
    channel_id = view["private_metadata"]
    message = create_incident(incident_name, incident_status, incident_description)
    say(f"{message}", channel = channel_id)

def check_allowed_trigger(incident_name, slack_user_id, message):
    # allow operation if 
    #   channel name starts with incident
    #   in the allowed user list
    #   message contains the keywords
    allowed_slack_users_id = ['U056F2PDN3G']
    key_string = 'statuspage declare incident'
    return True if (incident_name.startswith('incident') and slack_user_id in allowed_slack_users_id and message == key_string) else False
    
    

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()