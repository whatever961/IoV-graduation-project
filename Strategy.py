import requests
import os
import csv
import json
import xml.etree.ElementTree as ET
import pandas as pd
from io import StringIO
import time
import func

vehicle_base_state = {}
vehicle_last_factor = {}
def cache_base_state(veh):
    vid = veh["id"]
    if vid not in vehicle_base_state:
        vehicle_base_state[vid] = {
            "accel": veh["accel"],
            "decel": veh["decel"],
            "max_speed": veh["max_speed"],
            "tau": veh["tau"],
            "min_gap": veh["min_gap"],
            "speed_mode": veh["speed_mode"],
            "vtype": veh["vtype"]
        }
        
"""
Used for connecting database,
now only support mysql and postgresql
def connectDB(db_type = "mysql", db_name, user, password, host, port):
    match db_type:
        case "mysql":
            if host is None:
                print("host is not specified")
            if user is None:
                print("user is not specified")
            if db_name is None:
                print("database name is not specified")
            conn=mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
            )
            cursor=conn.cursor()

            cursor.close()
            conn.close()
        case "postgresql":
            if host is None:
                print("host is not specified")
            if user is None:
                print("user is not specified")
            if db_name is None:
                print("database name is not specified")
            conn = psycopg2.connect(
            dbname = db_name,
            user = user,
            password = password,
            host = host,
            port = port
            )
            cursor = conn.cursor()

            cursor.close()
            conn.close()
        case _:
            print("Database not support")
    return
"""


"""
To get external data from open data site
Mostly we get weather data
But it may get various data as long as the URL is valid
""" 
def fetchExternalData(url, headers=None, params=None, timeout=10):
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)

        data_format = detectDataFormat(response)
        match data_format:
            case "json":
                return response.json()
            case "xml":
                return ET.fromstring(response.text)
            case "csv":
                return list(csv.reader(StringIO(response.text)))
            case "text":
                return response.text
            case _:
                print("Unknown data format")
                return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def parseWeather(weather_str):
    cloud_weight = 1.0  #Default
    weather_weight = 1.0  #Default
    
    # Determine cloud weight
    for cloud in func.cloud_mapping.keys():
        if weather_str.startswith(cloud):
            cloud_weight = cloud_mapping[cloud]
            weather_str = weather_str[len(cloud):]  #Remove cloud part
            break #Take first matched condition
    
    # Determine weather weight
    for condition in func.weather_mapping.keys():
        if condition in weather_str:
            weather_weight = weather_mapping[condition]
            break #Take first matched condition

    return cloud_weight, weather_weight

def averageWeightedWeather(weather_list):
    weighted_weather = 0
    count = 0

    for weather in weather_list:
        cloud_weight, weather_weight = parseWeather(weather)
        weighted_weather += (cloud_weight * weather_weight)
        count += 1
    
    #Avoid division by zero
    return weighted_weather / count if count>0 else 1

def OBUProcessData(cloud_data):
    if cloud_data is None or "records" not in cloud_data or "Station" not in cloud_data["records"]:
        print("Invalid data format or missing records.")
        return
    
    weather_string = []
    
    # Process each station's data
    for station in cloud_data["records"]["Station"]:
        #station_name = station.get("StationName", "Unknown")
        #datetime = station.get("ObsTime", {}).get("DateTime", "Unknown")
        #county_name = station.get("GeoInfo", {}).get("CountyName", "Unknown")
        weather = station.get("WeatherElement", {}).get("Weather", "Unknown")
        visibility = station.get("WeatherElement", {}).get("VisibilityDescription", "Unknown") #idk where to use this, but I'll leave it here just in case
        weather_string.append(weather)
        
        if visibility == "-99":
            visibility = "Unknown"
    weighted_weather = averageWeightedWeather(weather_string)

    """
    total_10min = 0
    total_1hr = 0
    count = 0
    for station in rain_data["records"]["Station"]:
        past_10 = station.get("RainfallElement", {}).("Past10Min", {}).get("Precipitation", 0)
        past_1h = station.get("RainfallElement", {}).get("Past1hr", {}).get("Precipitation", 0)
        total_10min += past_10
        total_1hr += past_1h
        count += 1
    avg_10min = total_10min / count if count > 0 else 0
    avg_1hr = total_1hr / count if count > 0 else 0
    """
    return weighted_weather


def setOption(data, weather_factor, vehicles): 
    #IMPORTANT!!! weather_factor is a NEGATIVE DOUBLE. represent how many % should a variable reduce
    my_speed = data["speed"]
    lane_id = data["lane_id"]
    leader = data["leader"]
    leader_speed = data["leader_speed"]
    road_limit = data["speed_limit"]

    safe_gap = 8.0  # meters
    boost = 2.0  # m/s
    min_follow_speed = 5.5  # don't slow too much

    target_speed = my_speed

    if leader["id"]:
        gap = leader["gap"]

        if gap < safe_gap:
            # Need to slow down gently
            target_speed = leader_speed * 0.9
        elif gap > safe_gap + 10:
            # Can boost slightly, but not over limit
            target_speed = min(my_speed + boost, road_limit)
    elif my_speed < road_limit:
        # No leader — cruise or speed up slightly if under limit
        target_speed = min(road_limit, my_speed + 1.5)

    # Smooth adjustment
    duration = max(1.0, abs(my_speed - target_speed) / 2.5)  # ~2.5 m/s² comfortable acceleration

    return {
        "target_speed": target_speed,
        "duration": duration
    }
