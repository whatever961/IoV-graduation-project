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
import func
import argparse
from monitor import Monitor

NUM_OBUS = 16  # Number of PC to be distributed (default)
ACK_TIMEOUT = 2  # seconds
acks_received = set()
vehicle_end_data = {}
congested_edge = None
mqtt_sent_now = 0
mqtt_recv_now = 0
step_counter = 5 # Log to monitor csv once a while, if change this then remember change the reset value at the end

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--obus", type=int, default=16, help="Number of OBUs (PCs, datatype=int)")
    parser.add_argument("--reroute_period", type=float, default=10.0, help="Time interval between reroutes (seconds, datatype=float)")
    parser.add_argument("--nogui", action="store_true", help="Run SUMO without GUI")
    return parser.parse_args()

def lanes_to_edges(lanes):
    return list({traci.lane.getEdgeID(lane_id) for lane_id in lanes})

def detect_congested_edges(threshold_ratio=0.7, min_vehicle_count=4, min_occupancy=0.25):
    congested_lanes = []
    for lane_id in traci.lane.getIDList():
        if lane_id.startswith(":"):
            continue
        speed = traci.lane.getLastStepMeanSpeed(lane_id)
        max_speed = traci.lane.getMaxSpeed(lane_id)
        count = traci.lane.getLastStepVehicleNumber(lane_id)
        occupancy = traci.lane.getLastStepOccupancy(lane_id)
        length = traci.lane.getLength(lane_id)

        if (count >= min_vehicle_count and
            speed < max_speed * threshold_ratio and
            occupancy > min_occupancy):
            congested_lanes.append(lane_id)
            print(f"[CONGESTED] {lane_id}: mean speed={speed:.2f}, occ={occupancy:.2f}")

    return lanes_to_edges(congested_lanes)

def write_vehicle_end_data_to_csv(stats_dict, filename="vehicle_log.csv"):
    with open(filename, "w", newline='') as csvfile:
        fieldnames = ["veh_id", "vtype", "start_time", "reach_time", "num_of_stops", "num_of_reroutes"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for veh_id, stats in stats_dict.items():
            writer.writerow({
                "veh_id": veh_id,
                "vtype": stats.get("vtype"),
                "start_time": stats.get("start_time"),
                "reach_time": stats.get("reach_time"),
                "num_of_stops": stats.get("num_of_stops", 0),
                "num_of_reroutes": stats.get("num_of_reroutes", 0)
            })


def on_ack(client, userdata, msg):
    group_id = msg.topic.split("/")[-1]  # e.g. controller/ack/pc2
    acks_received.add(group_id)
    global mqtt_recv_now
    mqtt_recv_now += monitor.estimate_mqtt_packet(msg.topic, msg.payload.decode())
    try:
        ack = json.loads(msg.payload.decode())
    except Exception as e:
        print(f"Failed to parse ACK message: {e}")
        return
    # Extract data from the ACK payload
    option = ack.get("option", None)
    if option is not None :
        func.adjustDrivingEnv(option, userdata)

def vehicle_sense_env(veh_id):
    pos = traci.vehicle.getPosition(veh_id)
    speed = traci.vehicle.getSpeed(veh_id)
    leader = traci.vehicle.getLeader(veh_id, 100) # Detect leader 100m ahead
    angle = traci.vehicle.getAngle(veh_id)
    lane_id = traci.vehicle.getLaneID(veh_id)
    speed_limit = traci.lane.getMaxSpeed(lane_id)
    current_time = traci.simulation.getTime()
    
    # Default fallback speed in case no leader exists
    leader_id = leader[0] if leader else None
    leader_gap = leader[1] if leader else None
    leader_speed = traci.vehicle.getSpeed(leader_id) if leader_id else None
    
    return {
        "veh_id": veh_id,
        "position": pos,
        "speed": speed,
        "speed_limit": speed_limit,
        "angle": angle,
        "lane_id": lane_id,
        "current_time": current_time,
        "leader": {
            "id": leader_id,
            "gap": leader_gap
        },
        "leader_speed": leader_speed
    }

"""
def get_vehicle_state(veh_id, congested_edge):
    return {
        "id": veh_id,
        "vtype": traci.vehicle.getTypeID(veh_id),
        "pos": traci.vehicle.getPosition(veh_id),
        "speed": traci.vehicle.getSpeed(veh_id),
        "max_speed": traci.vehicle.getMaxSpeed(veh_id),
        "allowed_speed": traci.vehicle.getAllowedSpeed(veh_id),
        "angle": traci.vehicle.getAngle(veh_id),
        "road": traci.vehicle.getRoadID(veh_id),
        "accel": traci.vehicle.getAccel(veh_id),
        "decel": traci.vehicle.getDecel(veh_id),
        "speed_mode": traci.vehicle.getSpeedMode(veh_id),
        "tau": traci.vehicle.getTau(veh_id),
        "min_gap": traci.vehicle.getMinGap(veh_id),
        "current_time": traci.simulation.getTime(),
        "current_road": traci.vehicle.getRoadID(veh_id),
        "route": traci.vehicle.getRoute(veh_id),
        "congested_edge": congested_edge
    }
"""
# Initialize the client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("rw", "readwrite")
client.user_data_set(vehicle_end_data)
client.on_message = on_ack
# Connect to the server(local)
client.connect("127.0.0.1", 1883, 60)
client.subscribe("controller/ack/#")
client.loop_start()

if __name__ == "__main__":
    is_timeout = False
    active_acks = set()
    args = parse_args()
    NUM_OBUS = args.obus
    reroute_period = args.reroute_period

    #Start simulation
    sumo_binary = "sumo" if args.nogui else "sumo-gui"
    traci.start([sumo_binary, "-c", "map.sumo.cfg"])    # change "map.sumo.cfg" to "test_route.sumocfg" and can use test route
    monitor = Monitor(interval=1.0, logfile="monitor_log.csv")
    while traci.simulation.getMinExpectedNumber()>0:
        #Split and distribute simulation data
        vehicle_ids = traci.vehicle.getIDList()
        vehicle_groups = func.split_vehicles(vehicle_ids, NUM_OBUS)

        for i, group in enumerate(vehicle_groups):
            if not group:
                continue
            group_data = [vehicle_sense_env(vid) for vid in group]
            topic = f"controller/send/pc{i}"
            payload = json.dumps(group_data)
            client.publish(topic, payload)
            mqtt_sent_now += monitor.estimate_mqtt_packet(topic, payload)
            active_acks.add(f"pc{i}")
            
        # Wait for ACKs from all vehicles or timeout
        start_time = time.time()
        while time.time() - start_time < ACK_TIMEOUT:
            if acks_received == active_acks:
                is_timeout = False
                break
            time.sleep(0.01)
            is_timeout = True

        if is_timeout:
            print("WARNING: Some OBUs did not respond in time!")

        #Continue simulation
        acks_received.clear()
        active_acks.clear()
        is_timeout = False
        traci.simulation.step()

        #tracking data after we moved
        current_time = traci.simulation.getTime()
        for veh_id in traci.vehicle.getIDList():
            # Initialize tracking entry if new
            if veh_id not in vehicle_end_data:
                vehicle_end_data[veh_id] = {
                    "vtype": traci.vehicle.getTypeID(veh_id),
                    "start_time": current_time,
                    "reach_time": None,
                    "num_of_stops": 0,
                    "num_of_reroutes": 0,
                    "last_speed": -1
                }
            speed = traci.vehicle.getSpeed(veh_id)
            # Count stop events (speed goes from > 0 to 0)
            if speed < 0.1 and vehicle_end_data[veh_id]["last_speed"] >= 0.1:
                vehicle_end_data[veh_id]["num_of_stops"] += 1
            vehicle_end_data[veh_id]["last_speed"] = speed
            
        for veh_id in traci.simulation.getArrivedIDList():
            if veh_id in vehicle_end_data:
                vehicle_end_data[veh_id]["reach_time"] = current_time
        step_counter -= 1
        if step_counter == 0:
            monitor.log(sim_time=current_time, mqtt_sent_now=mqtt_sent_now, mqtt_recv_now=mqtt_recv_now)
            mqtt_sent_now = 0
            mqtt_recv_now = 0
            step_counter = 5
    
    traci.close()
    monitor.end_time = time.time()
    monitor.save()
    client.loop_stop()
    client.disconnect()
    write_vehicle_end_data_to_csv(vehicle_end_data)
    print("Simulation complete. Vehicle log saved.")
