import traci
import requests
import os
import csv
import json
import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3
import psycopg2
import mysql.connector
from io import StringIO
import paho.mqtt.client as mqtt
import time

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
    def __init__(self, vehID, slowDownSpeed, slowDownDuration, safeDist,
                 accel, decel, speedMode, maxSpeed, response):
        self.vehID = vehID
        self.slowDown = [slowDownSpeed, slowDownDuration]
        self.safeDist = safeDist
        self.accel = accel
        self.decel = decel
        self.speedMode = speedMode
        self.maxSpeed = maxSpeed
        self.response = response



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
def adjustDrivingEnv(option):
	for i in option:
		slowDown(i.vehID, i.slowDownSpeed, i.slowDownDuration)
		setAccel(i.vehID, i.accel)
		setDecel(i.vehID, i.decel)
		setSpeedMode(i.vehID, i.speedMode)
		setMaxSpeed(i.vehID, i.maxSpeed)
		setMinGap(i.vehID, i.safeDist)
		setTau(i.vehID, i.response)


def writeLog(file, log_type):
    pass
    return
