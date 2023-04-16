# To run the app, run the following command in the terminal:
# python3 fetch_bot.py
# To stop the app, press Ctrl+C in the terminal.
# To run the app in the background, run the following command in the terminal:
# nohup python3 fetch_bot.py &
# To stop the app, run the following command in the terminal:
# ps -ef | grep fetch_bot.py
# kill -9 <process id>

import asyncio
from multiprocessing import Process
import os
from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import time
import schedule
from src.save_history import save_conversation_history
from src.retreive_data import job_weather
from src.commons import find_channel_id, send_to_slack, send_to_slack_thread, delete_message
from src.capture_reddit import job_reddit
from src.new_bing import request_bot

# read SLACK_BOT_TOKEN from as environment variable
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
# read SLACK_APP_TOKEN from as environment variable
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")


# Initialize the Slack client
client = WebClient(token=SLACK_BOT_TOKEN)
# Initialize the Slack
app = App(token=SLACK_BOT_TOKEN)

# Send the weather data to Slack
# also response to user's message from the subthread
@app.event("app_mention")
def message(body):
    
    # Get the message text
    msg = str(body["event"]["text"]).split(">")[1].strip()

    # Get the channel ID
    channel_id = body["event"]["channel"]
    
    # Get list of commands
    if msg == "-h" or msg == "-help":
        message = "All commands:\n" 
        message += "-h or -help : Helper flag to show all commands\n"
        # if weather, take city as argument
        message += "-w or -weather <city> : Get the current weather and forecast for the next 24 hours\n"
        # if history, take channel name as argument
        message += "-s or -save_history <channel name> : Get the conversation history for the last week\n"
        # if reddit, take subreddit name and a search limit as arguments
        message += "-r or -reddit <subreddit name> <limit> : Get the latest posts from a subreddit\n"
        # send the message to the channel
        send_to_slack(client, channel_id, message)
        return
    # if weather, take city as argument
    elif msg.startswith('-w') or msg.startswith('-weather'):
        # get the city name
        # keep everything after the first space
        city = msg.split(" ", 1)[1]
        job_weather(client, channel_id, city)
        return
    # if history, take channel name as argument
    elif msg.startswith('-s') or msg.startswith('-save_history'):
        # get the channel name
        channel_name = msg.split(" ")[1]
        # if channel name is not valid, return
        # else, save the channel_id
        # and call save_conversation_history()
        channel_id = find_channel_id(client, channel_name)
        if channel_id is None:
            message = f"Invalid channel name {channel_name}"
            send_to_slack(client, channel_id, message)
            return
        else:
            save_conversation_history(client, channel_id)
        return
    # if reddit, take subreddit name and a search limit as arguments
    elif msg.startswith('-r') or msg.startswith('-reddit'):
        # get the subreddit name
        subreddit = msg.split(" ")[1]
        # get the search limit
        limit = int(msg.split(" ")[2])
        # call job_reddit()
        job_reddit(client, channel_id, subreddit, limit, True)
        return
    elif msg.startswith('-'):
        message = f"Invalid command {msg}"
        send_to_slack(client, channel_id, message)
        return
    else:
        # show usage
        message = "Invalid command. Use -h or -help to see all commands"
        send_to_slack(client, channel_id, message)
        return



# the bot gets a message from a subthread
# and responds to the user
@app.event("message")
def chat(body):

    # if the message @bot, ignore
    if body["event"]["text"].startswith("<@"):
        return

    # Get the channel ID
    channel_id = body["event"]["channel"]

    global is_busy

    # a list to store all ts of the messages sent when the bot is busy
    global busy_ts

    # tell the user that the bot is busy due to a previous request
    if is_busy:
        message = "I am busy. Please wait for a few seconds."
        busy_ts.append(send_to_slack(client, channel_id, message))
        return
    
    is_busy = True

    # Get the message text
    prompt = str(body["event"]["text"]).split(">")[0].strip()

    # notify the user that the bot is thinking
    message = "I am thinking..."

    # send the message to the channel
    message_id = send_to_slack(client, channel_id, message)

    # get the response
    response = asyncio.run(request_bot(prompt))

    # busy_ts is not empty
    # delete all messages sent when the bot is busy
    if busy_ts:
        for ts in busy_ts:
            delete_message(client, channel_id, ts)
        busy_ts = []

    # if response is done, delete the last message
    # get message id of the last message
    # delete the last message
    delete_message(client, channel_id, message_id)

    # send the response to the user
    message = f"{response}\n"
    ts = send_to_slack(client, channel_id, message)
    
    global last_response_ts
    last_response_ts = time.time()
    is_busy = False

    # start a timer to monitor the bot status
    global p_timer

    if p_timer.is_alive():
        p_timer.terminate()
        p_timer = Process(target=monitor_bot_status, args=(channel_id, last_response_ts, 1800))
    else:
        p_timer = Process(target=monitor_bot_status, args=(channel_id, last_response_ts, 1800))
    
    p_timer.start()

    return

# monitor the bot status
def monitor_bot_status(channel_id, last_response_ts, timeout):
    if last_response_ts is not None:
        while last_response_ts is not None:
            # if the bot did not receive any message for timeout seconds
            if (time.time() - last_response_ts) > timeout:
                # send a message to the channel
                
                response = asyncio.run(request_bot("inactivity"))
                send_to_slack(client, channel_id, response)
                # terminate the process
                os._exit(0)
            else:
                time.sleep(59)
    else:
        os._exit(0)

# schedule to run job_weather() every day at a specific time
def run_schedule_weather(time_string, channel_name):
    channel_id = find_channel_id(client, channel_name)
    # every day at time_string
    schedule.every().day.at(time_string).do(job_weather, client, channel_id, "Mont-Royal")
    while True:
        schedule.run_pending()
        time.sleep(1)


# schedule to run save_conversation_history() every week at a specific time
def run_schedule_history(time_string, channel_name):
    channel_id = find_channel_id(client, channel_name)
    
    schedule.every().monday.at(time_string).do(save_conversation_history, client, channel_id)

    while True:
        schedule.run_pending()
        time.sleep(1)


# schedule to run job_reddit() every x hours
def run_schedule_reddit(num_hours, channel_name, subreddit, limit):
    channel_id = find_channel_id(client, channel_name)
    # every x hours
    schedule.every(num_hours).minutes.do(job_reddit, client, channel_id, subreddit, limit, False)
    while True:
        schedule.run_pending()
        time.sleep(1)


# Start your app
if __name__ == "__main__":

    # start a timer to monitor the bot status
    global p_timer
    p_timer = Process(target=monitor_bot_status, args=(None, None, None,))
    p_timer.start()

    # ensure only one user can use the bot at a time
    global is_busy
    is_busy = False
    global busy_ts
    busy_ts = []

    # Create two processes for weather
    # to run the schedule at different times
    # p1 = Process(target=run_schedule_weather, args=("09:00","your_channel_name"))
    # p2 = Process(target=run_schedule_weather, args=("21:00","your_channel_name"))

    # Create one process for history
    # to run the schedule at a specific time
    # p3 = Process(target=run_schedule_history, args=("00:00","your_channel_name"))
    # p4 = Process(target=run_schedule_history, args=("00:00","your_channel_name"))

    # Create one process for reddit
    # p5 = Process(target=run_schedule_reddit, args=(30,"your_channel_name","subreddit",10))

    # Start the processes
    # p1.start()
    # p2.start()
    # p3.start()
    # p4.start()
    # p5.start()

    # Start your app
    SocketModeHandler(app, SLACK_APP_TOKEN).start()




