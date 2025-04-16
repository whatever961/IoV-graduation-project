import func

def on_connect(client, userdata, flags, rc, properties):
    print("Connected with result code " + str(rc))
    client.subscribe("cp/#")        # MQTT_sub from Simulation (control path)
    client.subscribe("dpback/#")    # MQTT_sub from Strategy (data path back)

def on_message(client, userdata, msg):  # Fix later
    # To screen
    print(f"Message from {msg.topic}: {msg.payload.decode('utf-8')}")
    
    # MQTT_pub to Strategy
    if(msg.topic == "cp"):
        # Sent the data
        data = json.loads(msg.payload.decode('utf-8'))
        client.publish('dpgo', data)
    # Change Traci
    else if(msg.topic == "dpback"):
        option = json.loads(msg.payload.decode('utf-8'))
        adjustDrivingEnv(option)


# Initialize the client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("rw", "readwrite")

# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the server
client.connect("127.0.0.1", 1883, 60)

# Connect to the broker
client.loop_forever()   # Change later