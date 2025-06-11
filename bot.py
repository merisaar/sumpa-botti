import os
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

client = WebClient(token=SLACK_BOT_TOKEN)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_user_lookup():
    try:
        response = client.users_list()
        users = response["members"]
        lookup = {user["name"]: user["id"] for user in users if not user.get("deleted", False)}
        return lookup
    except SlackApiError as e:
        logger.error(f"Error building user lookup: {e.response['error']}")
        return {}
    
user_lookup = build_user_lookup()

def get_user_id_by_name(name):
    logger.info(f"Looking for user ID for: {name}")
    try:
        nick_clean = name.lstrip("@")
        user_id = user_lookup.get(nick_clean)
        logger.info(f"Lookup {user_lookup}")
        logger.info(f"User ID found: {user_id} for name: {nick_clean}")
        if(user_id is not None):
            return user_id
    except SlackApiError as e:
        logger.error(f"Error getting user list: {e.response['error']}")
    return None

def get_or_create_channel(channel_name):
    logger.info(f"Checking for channel: {channel_name}")
    try:
        response = client.users_conversations(types="private_channel", limit=1000, exclude_archived=True)
        for ch in response["channels"]:
            if ch["name"] == channel_name:
                return ch["id"]
        result = client.conversations_create(name=channel_name, is_private=True)
        return result["channel"]["id"]
    except SlackApiError as e:
        logger.error(f"Error with channel: {e.response}")
        return None

def invite_users_to_channel(channel_id, user_ids):
    logger.info(f"Inviting users {user_ids} to channel {channel_id}")
    try:
        client.conversations_invite(channel=channel_id, users=",".join(user_ids))
    except SlackApiError as e:
        logger.error(f"Invite failed: {e.response['error']}")

def process_csv_from_df(df, user_id):
    grouped = df.groupby("channel_name")["slack_nick"].apply(list)

    logger.info("Starting to process CSV data to create channels and invite users.")
    for channel_name, nicknames in grouped.items():
        channel_id = get_or_create_channel(channel_name)
        if not channel_id:
            continue
        user_ids = [user_id] # Start with the user who uploaded the CSV
        for nick in nicknames[:5]:
            uid = get_user_id_by_name(nick)
            if uid:
                user_ids.append(uid)
        if user_ids:
            invite_users_to_channel(channel_id, user_ids)
