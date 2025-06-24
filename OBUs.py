import requests
import os
import csv
import json
import xml.etree.ElementTree as ET
import pandas as pd
from io import StringIO
import paho.mqtt.client as mqtt
import time
import random
import argparse
import Strategy
import func


def infer_local_congestion(vehicles):
    edge_speeds = {}
    edge_counts = {}
    edge_max_speeds = {}

    for v in vehicles:
        edge = v.get("road")
        speed = v.get("speed")
        allowed_speed = v.get("allowed_speed")

        if edge not in edge_speeds:
            edge_speeds[edge] = 0
            edge_counts[edge] = 0
            edge_max_speeds[edge] = allowed_speed

        edge_speeds[edge] += speed
        edge_counts[edge] += 1

    congested_edges = []
    for edge, count in edge_counts.items():
        avg_speed = edge_speeds[edge] / count
        allowed_speed = edge_max_speeds[edge]
        threshold = allowed_speed * 0.7

        if avg_speed < threshold and count > 2:
            congested_edges.append(edge)

    return congested_edges


# Callback when connected to the broker
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[{args.pc_topic_id}] Connected to MQTT with result code {rc}")
    client.subscribe(obu_topic)

# Callback when a message is received
def on_message(client, userdata, msg):
    print(f"Message from {msg.topic}: {msg.payload.decode('utf-8')}")
    # Parse incoming vehicle data
    try:
        assigned_vehicles = json.loads(msg.payload.decode())
    except Exception as e:
        print(f"Failed to parse message: {e}")
        return
    
    congested_edges = assigned_vehicles[0].get("congested_edge")
    current_time = assigned_vehicles[0].get("current_time")
    option = []
    weather_factor = None
    if current_time%1200.0==0.0:
        #cloud_data = fetchExternalData("https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWA-7B465ABE-F54D-4231-ABB4-D62EEFC1F684&format=JSON&StationId=466930,466910,466920,CAAH60,A0A460,AOA010,G2AI50&WeatherElement=Weather,VisibilityDescription,Now&GeoInfo=CountyName,TownName")
        #weather_factor = OBUProcessData(cloud_data)
        weather_factor = 0 # 晴天(0) 雨天(-0.15)
        option = Strategy.setOption(weather_factor, assigned_vehicles, congested_edges)
    elif current_time%3.0==0.0:
        weather_factor = 0 # for reroute
        option = Strategy.setOption(weather_factor, assigned_vehicles, congested_edges)
        
    ack_topic = f"controller/ack/pc{args.pc_topic_id}"
    client.publish(ack_topic, json.dumps({"option": option}, cls=func.AdvancedJSONEncoder))

parser = argparse.ArgumentParser()
parser.add_argument('--pc_topic_id', type=int, required=True, help="Topic for distributed OBUs' PC. Insert integer >= 0 (e.g. pc{0}, pc{1})")
args = parser.parse_args()
obu_topic = f"controller/send/pc{args.pc_topic_id}"

# Initialize the client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("rw", "readwrite")

# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
try:
    client.connect("127.0.0.1", 1883, 60)
    client.loop_forever()
except Exception as e:
    print(f"MQTT client failed to start: {e}")
