# Description: Common functions for the bot
from slack_sdk.errors import SlackApiError

# find channel id by channel name
def find_channel_id(client, channel_name):
    response = client.conversations_list()
    channels = response["channels"]
    for channel in channels:
        if channel["name"] == channel_name:
            return channel["id"]
    return None

# Send a message to Slack
# channel_id: the channel to send the message to
# message: the message to send
def send_to_slack(client, channel_id, message):
    try:
        response = client.chat_postMessage(channel=channel_id, text=message)
    except SlackApiError as e:
        print(f"Error sending message: {e}")