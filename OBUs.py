import random
import func
import Strategy

# Callback when connected to the broker
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[{args.pc_topic_id}] Connected to MQTT with result code {rc}")
    client.subscribe(obu_topic)

# Callback when a message is received
def on_message(client, userdata, msg):
    print(f"Message from {msg.topic}: {msg.payload.decode('utf-8')}")
    veh_ids=[]
    # Parse incoming vehicle data
    try:
        assigned_vehicles = json.loads(msg.payload.decode())
        veh_ids = [v["id"] for v in assigned_vehicles]
    except Exception as e:
        print(f"Failed to parse message: {e}")
        return
    option = None
    weather_factor = None
    if traci.getCurrentTime()%1200000==0:
        #cloud_data = fetchExternalData("https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWA-7B465ABE-F54D-4231-ABB4-D62EEFC1F684&format=JSON&StationId=466930,466910,466920,CAAH60,A0A460,AOA010,G2AI50&WeatherElement=Weather,VisibilityDescription,Now&GeoInfo=CountyName,TownName")
        #weather_factor = OBUProcessData(cloud_data)
        weather_factor = random.choice([-0.07, -0.13, -0.11, -0.09])
        option = setOption(weather_factor, veh_ids)
    ack_topic = f"controller/ack/pc{args.pc_topic_id}"
    client.publish(ack_topic, json.dumps({"option": option, "weather_factor": weather_factor}))

parser = argparse.ArgumentParser()
parser.add_argument('--pc_topic_id', type=int, required=True, help="Topic for distributed OBUs' PC (e.g. pc0, pc1)")
args = parser.parse_args()
obu_topic = f"controller/send/pc{args.pc_topic_id}"

# Initialize the client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("rw", "readwrite")

# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect("127.0.0.1", 1883, 60)
client.loop_forever()
