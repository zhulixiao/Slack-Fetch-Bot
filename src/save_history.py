import os
import datetime
import time
import json
from src.commons import send_to_slack


# Save the conversation history
# channel_id: the channel to save the conversation history from
def save_conversation_history(client, channel_id):
    # get the current time in unix time - x weeks in seconds
    # current_time - 2 weeks in seconds
    # 1 week in seconds = 604800
    # 2 weeks in seconds = 1209600
    # 1 month in seconds = 2592000
    x_weeks_ago = int(time.time()) - 604800
    # get the conversation history
    response = client.conversations_history(channel=channel_id, limit=1000, oldest=x_weeks_ago, inclusive="true")
    # get the messages
    messages = response["messages"]
    # get the current time
    current_time = datetime.datetime.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")
    
    # get channel name from channel id
    response_channel = client.conversations_info(channel=channel_id)

    channel_name = response_channel["channel"]["name"]
    
    # get the filename as the channel name + current time    
    filename = channel_name + "_" + str(current_time) + ".json"

    # store the file in a folder
    # if the folder does not exist
    if not os.path.exists("conversation_history"):
        # create the folder
        os.makedirs("conversation_history")

    # get the full path of the file
    filename = os.path.join("conversation_history", filename)

    # create a json contain "data"
    json_message = {"data": []}

    # create a new file
    with open(filename, 'w') as outfile:
        # for each message
        for message in messages:
            # get the ts
            ts = message["ts"]
            # convert the ts to a readable time format
            readable_time = datetime.datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')
            # get the user
            
            # if user is missing, skip the message
            if "user" not in message:
                continue

            user = message["user"]
            # get the user info
            user_info = client.users_info(user=user)
            # get the user name
            user_name = user_info["user"]["name"]
            message_text = ""
            # if the message contains a file
            # get the name + the url of the file
            # url_private_download
            if "files" in message:
                # get the files
                files = message["files"]
                # for each file
                for file in files:
                    # get the file name
                    file_name = file["name"]
                    # get the file url
                    file_url = file["url_private_download"]
                    # add the file name + the file url to the message
                    message_text += f"{file_name} : {file_url} \n"
            else: 
                # get the message text
                message_text = message["text"]

            # create a json object
            json_object = {
                "ts": str(readable_time),
                "user": user_name,
                "message": message_text
            }

            # add the json object to the json message
            json_message["data"].append(json_object)
            
        # write the json object to the file
        # keep the given format
        # keep the given language
        json.dump(json_message, outfile, indent=4, ensure_ascii=False)
    # close the file
    outfile.close()

    # send a message to the channel to notify that the conversation history has been saved
    # with timestamp
    send_to_slack(client, channel_id, f"Conversation history has been saved at {str(current_time)}")