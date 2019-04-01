#!/usr/bin/env python3
import re
import socket
import datetime
import time
from influxdb import InfluxDBClient

# put your influx server ip, port number and the name of the database
server_ip = '192.168.10.10'
server_port = 8086
db_name = 'ups_stats'

# NUT server ip, port number
HOST = ('192.168.10.1') 
PORT = 3493

# iso = datetime.datetime.now()
iso = datetime.datetime.utcnow().isoformat() + 'Z'

while True:

    # Open socket with remote host
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    # Send command
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(b'LIST VAR 9180\n')
    time.sleep(.25)
    data = s.recv(2048)
    utf8 = data.decode('utf-8')
    #print (utf8) # uncomment to see raw output from UPS
    s.close()

    values = re.findall(r'"(.*?)"', utf8) # find values using regex
    #print(values) # uncomment to see regex output
    
    # split results we want from "values" into individual variables
    try:
        BCHG = float(values[0])
        TIMELEFT = round(float(values[2])/60,2)
        UPSMODEL = (values[5])
        LINEV = float(values[19])
        LOAD = float(values[42])
        SERVER = (values[50])
        STATUS = (values[51])
    
    except:
        # shift values during power outage due to additional status line
        BCHG = float(values[0])
        TIMELEFT = round(float(values[2])/60,2)
        UPSMODEL = (values[5])
        LINEV = float(values[20])
        LOAD = float(values[43])
        SERVER = (values[51])
        STATUS = (values[52]) 
        continue
    
    # Prepare UPS variabes in JSON format for upload to Influxdb
    json_ups = [
        {
            "measurement": "apcaccess",
            "tags": {
                "status": STATUS,
                "upsmodel": UPSMODEL,
                "server": SERVER
            },
            #"time": iso, # Comment out if influxdb is not writing data points
            "fields": {
                "LINEV": LINEV,
                "LOAD": LOAD,
                "BCHG": BCHG,
                "TIMELEFT": TIMELEFT,
            }
        }
    ]

    # write values to influxdb
    # note that the username and password are blank, put them inside the '' if you have
    # implemented authentication
    # retries=0 is infinite retries.
    client = InfluxDBClient(server_ip, server_port, '', '', db_name, timeout=5,retries=3)
    try:
        client.create_database(db_name) # will create db if none exists
        client.write_points(json_ups)
    except ConnectionError:
        print('influxdb server not responding')
        continue
    # Wait before repeating loop
    time.sleep(5)