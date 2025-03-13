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
        
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None



def writeLog(file, log_type):
    pass
    return

def adjustDrivingEnv(data):
    

if __name__ == "__main__":
    #Initialize and get external data and adjust the environment first
    collision_list = []
    collision_file = open("collide_log", "ra")
    ext_data = fetchExternalData("my_url")
    if ext_data is None:
        p = input("No external data found.\nContinue simulation without adjusting factors?(y/n)")
        if p == "n":
            try:
                os._exit(0)
            except:
                print("die")

    adjustDrivingEnv(ext_data)

    #Start simulation
    traci.start(["sumo-gui", "-c", "map.sumo.cfg"])
    while traci.simulation.getMinExpectedNumber()>0:
        traci.simulation.step()
        #If there's a car accident, record ID of cars
        if(traci.getCollidingVehiclesNumber()>0):
            collision_list.append(traci.getCollidingVehiclesIDList())
    traci.close()

    #Write log file base on whatever the fuck we got(not implement yet)

    collision_file.close()