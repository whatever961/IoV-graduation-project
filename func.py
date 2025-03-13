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


#MQTT part
def on_connect(client, userdata, flags, rc, properties):
    print("Connected to the broker.")

def on_message(client, userdata, msg):
    payload_string=str(msg.payload, encoding='utf8')
    parse=payload_string.split()
    ###UNFINISH


