import func

"""
Used for connecting database,
now only support mysql and postgresql
"""
def connectDB(db_type = "mysql", db_name, user, password, host, port):
    match db_type:
        case "mysql":
            if host is None:
                print("host is not specified")
            if user is None:
                print("user is not specified")
            if db_name is None:
                print("database name is not specified")
            conn=mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
            )
            cursor=conn.cursor()

            cursor.close()
            conn.close()
        case "postgresql":
            if host is None:
                print("host is not specified")
            if user is None:
                print("user is not specified")
            if db_name is None:
                print("database name is not specified")
            conn = psycopg2.connect(
            dbname = db_name,
            user = user,
            password = password,
            host = host,
            port = port
            )
            cursor = conn.cursor()

            cursor.close()
            conn.close()
        case _:
            print("Database not support")
    return



"""
To get external data from open data site
Mostly we get weather data
But it may get various data as long as the URL is valid
""" 
def fetchExternalData(url, headers=None, params=None, timeout=10):
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)

        data_format = detectDataFormat(response)
        match data_format:
            case "json":
                return response.json()
            case "xml":
                return ET.fromstring(response.text)
            case "csv":
                return list(csv.reader(StringIO(response.text)))
            case "text":
                return response.text
            case _:
                print("Unknown data format")
                return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def parseWeather(weather_str):
    cloud_weight = 1.0  #Default
    weather_weight = 1.0  #Default
    
    # Determine cloud weight
    for cloud in cloud_mapping.keys():
        if weather_str.startswith(cloud):
            cloud_weight = cloud_mapping[cloud]
            weather_str = weather_str[len(cloud):]  #Remove cloud part
            break #Take first matched condition
    
    # Determine weather weight
    for condition in weather_mapping.keys():
        if condition in weather_str:
            weather_weight = weather_mapping[condition]
            break #Take first matched condition

    return cloud_weight, weather_weight

def averageWeightedWeather(weather_list):
    weighted_weather = 0
    count = 0

    for weather in weather_list:
        cloud_weight, weather_weight = parseWeather(weather)
        weighted_weather += (cloud_weight * weather_weight)
        count += 1
    
    #Avoid division by zero
    return total_weighted_weather / count if count>0 else 1

def OBUProcessData(cloud_data):
    if cloud_data is None or "records" not in cloud_data or "Station" not in cloud_data["records"]:
        print("Invalid data format or missing records.")
        return
    
    weather_string = []
    
    # Process each station's data
    for station in cloud_data["records"]["Station"]:
        #station_name = station.get("StationName", "Unknown")
        #datetime = station.get("ObsTime", {}).get("DateTime", "Unknown")
        #county_name = station.get("GeoInfo", {}).get("CountyName", "Unknown")
        weather = station.get("WeatherElement", {}).get("Weather", "Unknown")
        visibility = station.get("WeatherElement", {}).get("VisibilityDescription", "Unknown") #idk where to use this, but I'll leave it here just in case
        weather_string.append(weather)
        
        if visibility == "-99":
            visibility = "Unknown"
    weighted_weather = averageWeightedWeather(weather_string)

    """
    total_10min = 0
    total_1hr = 0
    count = 0
    for station in rain_data["records"]["Station"]:
        past_10 = station.get("RainfallElement", {}).("Past10Min", {}).get("Precipitation", 0)
        past_1h = station.get("RainfallElement", {}).get("Past1hr", {}).get("Precipitation", 0)
        total_10min += past_10
        total_1hr += past_1h
        count += 1
    avg_10min = total_10min / count if count > 0 else 0
    avg_1hr = total_1hr / count if count > 0 else 0
    """
    return weighted_weather


def setOption(weather_factor, veh_ids): 
    #IMPORTANT!!! weather_factor is a NEGATIVE DOUBLE. represent how many % should a variable reduce
    vehicle = None
    option = []
    for veh_id in veh_ids:
        """
        Shorter accel, decel, max_speed
        Longer tau, min_gap
        """
        adj_accel = (1 + weather_factor) * traci.vehicle.getAccel(veh_id)
        adj_decel = (1 + weather_factor) * traci.vehicle.getDecel(veh_id)
        adj_max_speed = (1 + weather_factor) * traci.vehicle.getMaxSpeed(veh_id)
        adj_speed = (1 + weather_factor) * traci.vehicle.getSpeed(veh_id)
        speed_mode = traci.vehicle.getSpeedMode(veh_id)
        adj_tau = (1 - weather_factor) * traci.vehicle.getTau(traci.vehicle.getTypeID(veh_id))
        adj_min_gap = (1 - weather_factor) * traci.vehicle.getMinGap(traci.vehicle.getTypeID(veh_id))
        
        vehicle = Vehicle(
            vehID=veh_id,
            slowDownSpeed=adj_speed
            slowDownDuration=3
            safeDist=adj_min_gap
            accel=adj_accel
            decel=adj_decel
            speedMode=speed_mode
            maxSpeed=adj_max_speed
            response=adj_tau
        )
        option.append(vehicle)

    return option

# Initialize the client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("rw", "readwrite")

# Assign callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect("127.0.0.1", 1883, 60)

# Connect to the broker
client.loop_forever()   # Change later

'''
if __name__ == "__main__":
    collision_list = []
    collision_file = open("collide_log", "ra")

    #Start simulation
    traci.start(["sumo-gui", "-c", "map.sumo.cfg"])
    while traci.simulation.getMinExpectedNumber()>0:
        if traci.simulation.getCurrentTime()%900000==0: #get new data every 15 minutes
            cloud_data = fetchExternalData("https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=CWA-7B465ABE-F54D-4231-ABB4-D62EEFC1F684&format=JSON&StationId=466930,466910,466920,CAAH60,A0A460,AOA010,G2AI50&WeatherElement=Weather,VisibilityDescription,Now&GeoInfo=CountyName,TownName")
            #rain_data = fetchExternalData("https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization=CWA-7B465ABE-F54D-4231-ABB4-D62EEFC1F684&format=JSON&StationId=466930,466910,466920,CAAH60,A0A460,AOA010,G2AI50&RainfallElement=Past10Min,Past1hr&GeoInfo=CountyName,TownName")
            if cloud_data is None:
                p = input("No weather data found.\nContinue simulation without adjusting factors?(y/n)")
                if p == "n":
                    try:
                        os._exit(0)
                    except:
                        print("die")
            weather_factor = OBUProcessData(cloud_data)
            option = setOption(weather_factor)
            adjustDrivingEnv(option)
        traci.simulation.step()
        #If there's a car accident, record ID of cars
        #if(traci.getCollidingVehiclesNumber()>0):
            #collision_list.append(traci.getCollidingVehiclesIDList())
    traci.close()

    #Write log file base on whatever the fuck we got(not implement yet)

    collision_file.close()
    '''
