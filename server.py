from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import os, pandas as pd
from io import BytesIO
from slack_sdk import WebClient
import requests
from bot import process_excel_from_df

app = App(token=os.environ["SLACK_BOT_TOKEN"], signing_secret=os.environ["SLACK_SIGNING_SECRET"])
handler = SlackRequestHandler(app)
flask_app = Flask(__name__)

# Handle Slash Command
@app.command("/uploadexcel")
def handle_upload_command(ack, body, client, respond):
    ack()
    user_id = body["user_id"]
    respond(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Hi <@{user_id}>! Please upload your Excel file below."}
            }
        ],
        response_type="ephemeral"
    )

# Monitor file uploads
@app.event("file_shared")
def handle_file_shared(event, client, say):
    file_id = event["file_id"]
    file_info = client.files_info(file=file_id)
    file_url = file_info["file"]["url_private_download"]
    file_name = file_info["file"]["name"]
    user = event["user_id"]

    if not file_name.endswith(".xlsx"):
        client.chat_postMessage(channel=user, text="❌ Please upload a valid .xlsx Excel file.")
        return

    # Download file with auth
    headers = {"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"}
    response = requests.get(file_url, headers=headers)
    df = pd.read_excel(BytesIO(response.content))

    process_excel_from_df(df)

    client.chat_postMessage(channel=user, text="✅ Excel processed and channels handled!")

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)
