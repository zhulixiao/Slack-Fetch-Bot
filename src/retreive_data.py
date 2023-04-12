# Description: This file contains the functions that get the weather data from OpenWeatherMap and the other data from other APIs

import requests
import datetime
import time
import os
from src.commons import send_to_slack

# read WEATHER_API_KEY from as environment variable
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

# Get the current weather data for a city
def get_current_weather_data(city):
    # Get the current weather data from OpenWeatherMap
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    current = ""
    # If the data is valid
    if data["cod"] == 200: # 200 is the code for valid data
        # main = data["weather"][0]["main"]
        description = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        # feels_like = data["main"]["feels_like"]
        # temp_min = data["main"]["temp_min"]
        # temp_max = data["main"]["temp_max"]
        # humidity = data["main"]["humidity"]
        current_time = datetime.datetime.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")

        city_name = data["name"]
        country = data["sys"]["country"]

        current = f"{current_time} {city_name}, {country} \n"
        current += f"Current Temperature: {temp}°C \n"
        current += f"Current Weather: {description} \n"
    else:
        current = f"I’m having trouble getting the current weather for {city}.\n"

    return current

# Get the forecast weather data for a city
def get_forecast_weather_data(city):
    # Get the forecast weather data from OpenWeatherMap
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    
    future = ""
    # If the data is valid
    if data["cod"] == "200":
        # main = data["list"][4]["weather"][0]["main"]
        description = data["list"][4]["weather"][0]["description"]
        temp_sum = 0
        temp_min = data["list"][0]["main"]["temp_min"]
        temp_max = data["list"][0]["main"]["temp_min"]
        feels_like_day_sum = 0

        # Get the average temperature, min temperature, max temperature, and feels like temperature for the day
        # The data is updated every 3 hours, so we get the average of the first 8 data points
        for i in range(0,8):
            temp_sum += data["list"][i]["main"]["temp"]
            if(temp_min > data["list"][i]["main"]["temp_min"]): 
                temp_min = data["list"][i]["main"]["temp_min"]
            
            if(temp_max < data["list"][i]["main"]["temp_max"]): 
                temp_max = data["list"][i]["main"]["temp_max"]

            feels_like_day_sum += data["list"][i]["main"]["feels_like"]

        temp_day = "{:.2f}".format(temp_sum / 8)
        feels_like_day = "{:.2f}".format(feels_like_day_sum / 8)
        future = f"Forecast: {description} \n"
        future += f"H: {temp_max}°C L: {temp_min}°C \n"
        future += f"Feels Like: {feels_like_day}°C \n"
        future += f"Average: {temp_day}°C \n"
    else: # If the data is not valid
        future = f"I’m having trouble getting the forecast for {city}.\n"

    return future


# Add a quote to the weather data
def add_quotes():
    message = "-------------------------\n"
    # Get a random quote from https://api.quotable.io/quotes/random
    url = "https://api.quotable.io/quotes/random"
    response = requests.get(url)
    data = response.json()
    quote = data[0]["content"]
    author = data[0]["author"]
    message += f"{quote} - {author} \n"
    return message

# Add a useless fact to the weather data
def add_useless_fact():
    message = "-------------------------\n"
    # Get a random quote from https://uselessfacts.jsph.pl/random.json?language=en
    url = "https://uselessfacts.jsph.pl/random.json?language=en"
    response = requests.get(url)
    data = response.json()
    fact = data["text"]
    message += f"{fact} \n"
    return message

# Add a shibe pic to the weather data
def add_shibe_pic():
    message = ""
    # Get a random shibe pic from https://shibe.online/api/shibes?count=1&urls=true&httpsUrls=true
    url = "https://shibe.online/api/shibes?count=1&urls=true&httpsUrls=true"
    response = requests.get(url)
    data = response.json()
    pic_url = data[0]
    # show the pic as an attachment
    message += f"{pic_url} \n"
    return message


# Send the weather data to Slack
# for predefined cities
def job_weather(client, channel_id, city):

    # Get the current weather data
    message = get_current_weather_data(city)
    # Get the forecast weather data
    message += get_forecast_weather_data(city)
    # Add a quote
    message += add_quotes()
    # Add a useless fact
    message += add_useless_fact()
    # Add a shibe pic
    message += add_shibe_pic()
    
    send_to_slack(client, channel_id, message)
