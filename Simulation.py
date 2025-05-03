import func

# Initialize the client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("rw", "readwrite")
# Connect to the server(local)
client.connect("127.0.0.1", 1883, 60)

if __name__ == "__main__":
    collision_list = []
    collision_file = open("collide_log", "ra")

    #Start simulation
    traci.start(["sumo-gui", "-c", "map.sumo.cfg"])
    while traci.simulation.getMinExpectedNumber()>0:
        #Split and distribute simulation data

        #Wait for all PCs ack back

        #Continue simulation
        traci.simulation.step()
        #If there's a car accident, record ID of cars
        #if(traci.getCollidingVehiclesNumber()>0):
            #collision_list.append(traci.getCollidingVehiclesIDList())
    traci.close()

    #Write log file base on whatever the fuck we got(not implement yet)

    collision_file.close()
