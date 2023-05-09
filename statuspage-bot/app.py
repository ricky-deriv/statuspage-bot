import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from statuspage import *

load_dotenv()
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')

app = App(token=SLACK_BOT_TOKEN)

@app.event("app_mention")
def handle_app_mention_events(body, say):
    message_arr = body['event']['text'].split()

    if f"{message_arr[1]} {message_arr[2]}" == 'create incident':
        global incident_id
        message = create_incident(message_arr[3], message_arr[4], message_arr[5])
        say(message)

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()