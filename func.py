import traci
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

# Define cloud weight mapping
cloud_mapping = {
    "晴": 1.0,
    "多雲": 1.5,
    "陰": 2.0
}

# Define weather condition weight mapping
weather_mapping = {
    "有霾": -0.02,
    "有靄": -0.02,
    "有閃電": -0.01,
    "有雷聲": -0.01,
    "有霧": -0.03,
    "有雨": -0.03,
    "有雨雪": -0.04,
    "有大雪": -0.07,
    "有雪珠": -0.05,
    "有冰珠": -0.05,
    "有陣雨": -0.01,
    "陣雨雪": -0.03,
    "有雹": -0.06,
    "有雷雨": -0.08,
    "有雷雪": -0.08,
    "有雷雹": -0.08,
    "大雷雨": -0.08,
    "大雷雹": -0.08,
    "有雷": -0.01,
}

#Use for option setting
class Vehicle:
    def __init__(self, vehID, safeDist, accel, decel, speedMode, maxSpeed, response, reroute):
        self.vehID = vehID
        self.safeDist = safeDist
        self.accel = accel
        self.decel = decel
        self.speedMode = speedMode
        self.maxSpeed = maxSpeed
        self.response = response
        self.reroute = reroute
    def __jsonencode__(self):
        return {'vehID': self.vehID, 'safeDist': self.safeDist, 'accel': self.accel, 'decel': self.decel, 'speedMode': self.speedMode, 'maxSpeed': self.maxSpeed, 'response': self.response, 'reroute': self.reroute}

class AdvancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__jsonencode__'):
            return obj.__jsonencode__()
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def is_xml(data):
    try:
        ET.fromstring(data)
        return True
    except ET.ParseError:
        return False
def is_csv(data):
    try:
        sample = StringIO(data)
        reader = csv.reader(sample)
        first_row = next(reader, None)
        return bool(first_row)  # If it has a first row, it's likely CSV
    except Exception:
        return False

#Use for fetchExternalData() to detect data format
def detectDataFormat(data):
    if isinstance(data, dict):
        return "json"
    elif is_xml(data):
        return "xml"
    elif is_csv(data):
        return "csv"
    return "text"

#Use for change Traci
"""
Use to adjust the sumo driving environment through traci.

option format: It's a class

class Vehicle:
    def __init__(self, vehID, slowDownSpeed, slowDownDuration, safeDist, accel, decel, speedMode, maxSpeed, response):
        self.vehID = vehID									: 車輛ID(string)
        self.slowDown = [slowDownSpeed, slowDownDuration]	: [減速到達的速度, 減速所需時間](double, double)
        self.safeDist = safeDist							: 重設安全距離(double)
        self.accel = accel									: 加速度(double)
        self.decel = decel									: 減速度(double)
        self.speedMode = speedMode							: 行車模式(integer)[]
        self.maxSpeed = maxSpeed							: 最大速度(double)
        self.response = response							: 反應時間(double)
"""

"""
Bits setting for speedMode from right to left.

bit0: Regard safe speed
bit1: Regard maximum acceleration
bit2: Regard maximum deceleration
bit3: Regard right of way at intersections (only applies to approaching foe vehicles outside the intersection)
bit4: Brake hard to avoid passing a red light
bit5: Disregard right of way within intersections (only applies to foe vehicles that have entered the intersection).
bit6: Disregard speed limit.
"""

# option 改用 class 的 list
def adjustDrivingEnv(option, end_data):
    veh_id = option.get("veh_id")
    target_speed = option.get("target_speed")
    duration = option.get("duration")

    if veh_id is None or target_speed is None or duration is None:
        print(f"[ERROR] Missing key in option: {option}")
        return

    try:
        traci.vehicle.slowDown(veh_id, target_speed, duration)
        traci.vehicle.setColor(veh_id, (114, 51, 4, 191))  # optional visual marker
    except Exception as e:
        print(f"[ERROR] Failed to apply driving env for {veh_id}: {e}")
        '''if i.get("reroute") != False:
            try:
                traci.vehicle.rerouteTraveltime(i.get("vehID"))  
                traci.vehicle.setColor(i.get("vehID"), (255, 128, 0, 255))  # mark rerouted cars
                end_data[i.get("vehID")]["num_of_reroutes"] += 1 # increment the num_of_reroutes data
                print(f"[Smart Reroute] {i.get('vehID')}")
            except Exception as e:
                print(f"Reroute failed for {i.get('vehID')}: {e}")
        '''

def split_vehicles(vehicle_ids, num_obus):
    return [vehicle_ids[i::num_obus] for i in range(num_obus)]

def should_reroute(current_edge, route, congested_edges):
    if not route:
        return False

    destination_edge = route[-1]

    # Do not reroute if already on a congested edge or the destination itself is congested
    if (current_edge in congested_edges) or (destination_edge in congested_edges):
        return False

    # Check if any intermediate edges are congested
    for edge in route[:-1]:
        if edge in congested_edges:
            return random.random() < 0.45  # Smart rerouting (45%)
    
    return False
