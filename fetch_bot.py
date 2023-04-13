# To run the app, run the following command in the terminal:
# python3 fetch_bot.py
# To stop the app, press Ctrl+C in the terminal.
# To run the app in the background, run the following command in the terminal:
# nohup python3 fetch_bot.py &
# To stop the app, run the following command in the terminal:
# ps -ef | grep fetch_bot.py
# kill -9 <process id>

from multiprocessing import Process
import os
from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import time
import schedule
from src.save_history import save_conversation_history
from src.retreive_data import job_weather
from src.commons import find_channel_id, send_to_slack


# read SLACK_BOT_TOKEN from as environment variable
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
# read SLACK_APP_TOKEN from as environment variable
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")


# Initialize the Slack client
client = WebClient(token=SLACK_BOT_TOKEN)
# Initialize the Slack
app = App(token=SLACK_BOT_TOKEN)

# Send the weather data to Slack
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
        message += "-s or -save_history <channel name> : Get the conversation history for the last 2 weeks\n"
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
    elif msg.startswith('-'):
        message = f"Invalid command {msg}"
        send_to_slack(client, channel_id, message)
        return
    else:
        # show usage
        message = "Invalid command. Use -h or -help to see all commands"
        send_to_slack(client, channel_id, message)
        return


# schedule to run job_weather() every day at a specific time
def run_schedule_weather(time_string, channel_name):
    channel_id = find_channel_id(client, channel_name)
    # every day at time_string
    schedule.every().day.at(time_string).do(job_weather, client, channel_id, "Mont-Royal")
    while True:
        schedule.run_pending()
        time.sleep(1)


# schedule to run save_conversation_history() every Monday at a specific time
def run_schedule_history(time_string, channel_name):
    channel_id = find_channel_id(client, channel_name)
    # every Monday at time_string
    schedule.every().monday.at(time_string).do(save_conversation_history, client, channel_id)

    while True:
        schedule.run_pending()
        time.sleep(1)

# Start your app
if __name__ == "__main__":
    # Create two processes for weather
    # to run the schedule at different times
    # p1 = Process(target=run_schedule_weather, args=("19:00","your_channel_name"))
    # p2 = Process(target=run_schedule_weather, args=("21:00","your_channel_name"))

    # Create one process for history
    # to run the schedule at a specific time
    # p3 = Process(target=run_schedule_history, args=("00:00","your_channel_name"))
    # p4 = Process(target=run_schedule_history, args=("00:00","your_channel_name"))

    # Start the processes
    # p1.start()
    # p2.start()
    # p3.start()
    # p4.start()
    
    # Start your app
    SocketModeHandler(app, SLACK_APP_TOKEN).start()




