import func

# Initialize the client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("rw", "readwrite")
# Connect to the server(local)
client.connect("127.0.0.1", 1883, 60)

# Collision log
collision_list = []
collision_file = open("collide_log", "ra")

# Start simulation
traci.start(["sumo-gui", "-c", "map.sumo.cfg"])
while traci.simulation.getMinExpectedNumber()>0:
    if traci.simulation.getCurrentTime()%900000==0: # Get new data every 15 minutes
        # MQTT_pub to OBU
        # Get data from Traci
        msg = json.loads('{"ID": 12, "first_name": "Michael", "last_name": "Rodgers", "department": "Marketing"}')   # <- wait for fix
        # Publish data to OBU
        client.publish("cp", json.dumps(msg))
    traci.simulation.step()
    # If there's a car accident, record ID of cars
    # if(traci.getCollidingVehiclesNumber()>0):
        # collision_list.append(traci.getCollidingVehiclesIDList())
traci.close()

# Write log file base on whatever the fuck we got(not implement yet)

collision_file.close()