import func
import time

NUM_PCS = 2  # Number of PC to be distributed
ACK_TIMEOUT = 5  # seconds

acks_received = {}

def on_ack(client, userdata, msg):
    group_id = msg.topic.split("/")[-1]  # e.g. controller/ack/pc2
    acks_received.add(group_id)

def get_vehicle_state(veh_id):
    return {
        "id": veh_id,
        "pos": traci.vehicle.getPosition(veh_id),
        "speed": traci.vehicle.getSpeed(veh_id),
        "max_speed": traci.vehicle.getMaxSpeed(veh_id),
        "angle": traci.vehicle.getAngle(veh_id),
        "road": traci.vehicle.getRoadID(veh_id),
        "accel": traci.vehicle.getAccel(veh_id),
        "decel": traci.vehicle.getDecel(veh_id),
        "speed_mode": traci.vehicle.getSpeedMode(veh_id),
        "tau": traci.vehicle.getTau(traci.vehicle.getTypeID(veh_id)),
        "min_gap": traci.vehicle.getMinGap(traci.vehicle.getTypeID(veh_id)),
    }

# Initialize the client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("rw", "readwrite")
client.on_message = on_ack
# Connect to the server(local)
client.connect("127.0.0.1", 1883, 60)
client.subscribe("controller/ack/#")
client.loop_start()

if __name__ == "__main__":
    is_timeout = false;
    collision_list = []
    collision_file = open("collide_log", "ra")
    expected_acks = {f"pc{i}" for i in range(NUM_OBUS)}

    #Start simulation
    traci.start(["sumo-gui", "-c", "map.sumo.cfg"])
    #Split and distribute simulation data
    vehicle_ids = traci.vehicle.getIDList()
    vehicle_groups = split_vehicles(vehicle_ids, NUM_PCS)
    while traci.simulation.getMinExpectedNumber()>0:
        # Send vehicle states to each OBU
        for i, group in enumerate(vehicle_groups):
            group_data = [get_vehicle_state(vid) for vid in group]
            topic = f"controller/send/pc{i}"
            client.publish(topic, json.dumps(group_data))
            
        # Wait for ACKs from all vehicles or timeout
        start_time = time.time()
        while time.time() - start_time < ACK_TIMEOUT:
            if acks_received == expected_acks:
                is_timeout = false;
                break
            time.sleep(0.01)
            is_timeout = true;

        if is_timeout == true:
            print("WARNING: Some OBUs did not respond in time!")

        #Continue simulation
        acks_received.clear()
        is_timeout = false;
        traci.simulation.step()
        #If there's a car accident, record ID of cars
        #if(traci.getCollidingVehiclesNumber()>0):
            #collision_list.append(traci.getCollidingVehiclesIDList())
    traci.close()

    #Write log file base on whatever the fuck we got(not implement yet)

    collision_file.close()
