from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import os, pandas as pd
from io import BytesIO
from slack_sdk import WebClient
import requests
import logging
from bot import process_csv_from_df

app = App(token=os.environ["SLACK_BOT_TOKEN"], signing_secret=os.environ["SLACK_SIGNING_SECRET"])
handler = SlackRequestHandler(app)
flask_app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle Slash Command
@app.command("/uploadcsv")
def handle_upload_command(ack, body, client, respond):
    ack()
    user_id = body["user_id"]
    respond(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Hi <@{user_id}>! Please upload your CSV file below."}
            }
        ],
        response_type="ephemeral"
    )

# Monitor file uploads
@app.event("file_shared")
def handle_file_shared(event, client):
    logger.info(f"Received file_shared event: {event}")
    file_id = event["file_id"]
    user = event["user_id"]

    file_info = client.files_info(file=file_id)
    file = file_info["file"]
    file_name = file["name"]
    file_url = file["url_private_download"]

    if not file_name.endswith(".csv"):
        client.chat_postMessage(channel=user, text="❌ Please upload a valid `.csv` file.")
        return

    logger.info(f"Processing file: {file_name} from user: {user}")
    # Download CSV
    headers = {"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"}
    response = requests.get(file_url, headers=headers)
    
    try:
        logger.info("Reading CSV file from Slack")
        df = pd.read_csv(BytesIO(response.content), sep=';')  # Assumes header is present
        process_csv_from_df(df)
        client.chat_postMessage(channel=user, text="✅ CSV processed and channels handled!")
    except Exception as e:
        client.chat_postMessage(channel=user, text=f"❌ Failed to process CSV: {str(e)}. Please ensure that the CSV file has been separated by ';' and has valid headers 'channel_name' and 'slack_nick'")

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)
