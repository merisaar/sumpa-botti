import os
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

client = WebClient(token=SLACK_BOT_TOKEN)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_id_by_name(name):
    logger.info(f"Looking for user ID for: {name}")
    name = name.lstrip("@")
    try:
        result = client.users_list()
        logger.info(f"Found {result['members']} in the workspace.")
        for member in result['members']:
            if member['name'] == name:
                return member['id']
    except SlackApiError as e:
        logger.error(f"Error getting user list: {e.response['error']}")
    return None

def get_or_create_channel(channel_name):
    logger.info(f"Checking for channel: {channel_name}")
    try:
        response = client.conversations_list(types="private_channel", limit=1000, exclude_archived=True)
        logger.info(f"Found {response['channels']} private channels.")
        for ch in response["channels"]:
            if ch["name"] == channel_name:
                return ch["id"]
        result = client.conversations_create(name=channel_name, is_private=True)
        return result["channel"]["id"]
    except SlackApiError as e:
        logger.error(f"Error with channel: {e.response['error']}")
        return None

def invite_users_to_channel(channel_id, user_ids):
    logger.info(f"Inviting users {user_ids} to channel {channel_id}")
    try:
        client.conversations_invite(channel=channel_id, users=",".join(user_ids))
    except SlackApiError as e:
        logger.error(f"Invite failed: {e.response['error']}")

def process_csv_from_df(df):
    grouped = df.groupby("channel_name")["slack_nick"].apply(list)

    logger.info("Starting to process CSV data to create channels and invite users.")
    for channel_name, nicknames in grouped.items():
        channel_id = get_or_create_channel(channel_name)
        if not channel_id:
            continue
        user_ids = []
        for nick in nicknames[:5]:
            uid = get_user_id_by_name(nick)
            if uid:
                user_ids.append(uid)
        if user_ids:
            invite_users_to_channel(channel_id, user_ids)
