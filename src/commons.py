# Description: Common functions for the bot
import os
import requests
from slack_sdk.errors import SlackApiError

# find channel id by channel name
# client: the Slack client
# channel_name: the name of the channel
# return: the channel id
def find_channel_id(client, channel_name):
    response = client.conversations_list()
    channels = response["channels"]
    for channel in channels:
        if channel["name"] == channel_name:
            return channel["id"]
    return None

# Send a message to Slack
# client: the Slack client
# channel_id: the channel to send the message to
# message: the message to send
def send_to_slack(client, channel_id, message):
    try:
        response = client.chat_postMessage(channel=channel_id, text=message)
        # return the timestamp of the message
        return response["ts"]
    except SlackApiError as e:
        print(f"Error sending message: {e}")


# Send a message to Slack in a thread
def send_to_slack_thread(client, channel_id, message, thread_ts):
    try:
        response = client.chat_postMessage(channel=channel_id, text=message, thread_ts=thread_ts)
        # return the timestamp of the message
        return response["ts"]
    except SlackApiError as e:
        print(f"Error sending message: {e}")

# delete a message sent by the bot
# client: the Slack client
# channel_id: the channel to delete the message from
# ts: the timestamp of the message
def delete_message(client, channel_id, ts):
    try:
        response = client.chat_delete(channel=channel_id, ts=ts)
    except SlackApiError as e:
        print(f"Error deleting message: {e}")



# download the file by url
# url: the url of the file
# filename: the name of the file
def download_file(url, filename):
    # add an auth token to the url
    # Authorization: Bearer xoxb-***
    headers = {"Authorization": "Bearer " + os.environ["SLACK_BOT_TOKEN"]}
    # get the file
    response = requests.get(url, headers=headers)

    # if response is not ok
    if not response.ok:
        # print the error
        print(response)
        # return
        return

    # if conversation history is not existed
    if not os.path.exists("conversation_history"):
        # create a new directory
        os.mkdir("conversation_history")
    
    # if downloaded_files is not existed
    if not os.path.exists("conversation_history/downloaded_files"):
        # create a new directory
        os.mkdir("conversation_history/downloaded_files")
    
    # get the full path of the file
    filename = os.path.join("conversation_history/downloaded_files", filename)
    
    # create a new file
    with open(filename, 'wb') as f:
        # write the file
        f.write(response.content)
