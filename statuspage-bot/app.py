import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')

app = App(token=SLACK_BOT_TOKEN)

incident_channel_first_name = 'incident'

@app.event("app_mention")
def handle_app_mention_events(body, say):
    message_arr = body['event']['text'].split()
    say(f"hi there: {message_arr[1]}")

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()