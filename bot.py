import os
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
EXCEL_FILE = os.getenv("EXCEL_FILE", "channels.xlsx")

client = WebClient(token=SLACK_BOT_TOKEN)

def get_user_id_by_name(name):
    name = name.lstrip("@")
    try:
        result = client.users_list()
        for member in result['members']:
            if member['name'] == name:
                return member['id']
    except SlackApiError as e:
        print(f"Error getting user list: {e.response['error']}")
    return None

def get_or_create_channel(channel_name):
    try:
        response = client.conversations_list(types="private_channel")
        for ch in response["channels"]:
            if ch["name"] == channel_name:
                return ch["id"]
        result = client.conversations_create(name=channel_name, is_private=True)
        return result["channel"]["id"]
    except SlackApiError as e:
        print(f"Error with channel: {e.response['error']}")
        return None

def invite_users_to_channel(channel_id, user_ids):
    try:
        client.conversations_invite(channel=channel_id, users=",".join(user_ids))
    except SlackApiError as e:
        print(f"Invite failed: {e.response['error']}")

def process_csv_from_df(df):
    grouped = df.groupby("channel_name")["slack_nick"].apply(list)

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
