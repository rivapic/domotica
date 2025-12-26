#!/usr/bin/env python3
# TinyTuya Generic Monitor - Reads device params from devices.json
# -*- coding: utf-8 -*-

import tinytuya
import time
import json
import sys
from db_mariadb import insert_status_db
from dps_utils import print_dps, load_device_info

##tinytuya.set_debug(True)

# Load devices.json and get device by name from command-line argument
if len(sys.argv) < 2:
    print("Uso: ./generic_monitor_d.py <nombre_dispositivo>")
    sys.exit(1)

target_device_name = sys.argv[1]

device_info = load_device_info(target_device_name)
if not device_info:
    sys.exit(1)

# Extract device parameters
DEVICEID = device_info.get('id')
DEVICEKEY = device_info.get('key')
DEVICEIP = device_info.get('ip', 'Auto')  # Use 'Auto' if IP is not specified
DEVICEVERSION = device_info.get('version', '3.3')  # Default to 3.3 if not specified
DEVICE_NAME = device_info.get('name')

# Setting the address to 'Auto' or None will trigger a scan which will auto-detect both the address and version, but this can take up to 8 seconds
d = tinytuya.Device(DEVICEID, DEVICEIP, DEVICEKEY, version=DEVICEVERSION, persist=True)
# If you know both the address and version then supplying them is a lot quicker
# d = tinytuya.Device(DEVICEID, DEVICEIP, DEVICEKEY, version=DEVICEVERSION, persist=True)

STATUS_TIMER = 30
KEEPALIVE_TIMER = 12


print(f" > Monitoring Device: {DEVICE_NAME} < ")
print(" > Send Request for Status < ")
data = d.status()
print('Initial Status: %r' % data)
print_dps(data, device_info, DEVICE_NAME)
print("-" * 40)

if data and 'Err' in data:
    print("Status request returned an error, is version %r and local key %r correct?" % (d.version, d.local_key))

print(" > Begin Monitor Loop <")
heartbeat_time = time.time() + KEEPALIVE_TIMER
status_time =  None


# Uncomment if you want the monitor to constantly request status - otherwise you
# will only get updates when state changes
#status_time = time.time() + STATUS_TIMER

while(True):
    if status_time and time.time() >= status_time:
        # Uncomment if your device provides power monitoring data but it is not updating
        # Some devices require a UPDATEDPS command to force measurements of power.
        # print(" > Send DPS Update Request < ")
        # Most devices send power data on DPS indexes 18, 19 and 20
        # d.updatedps(['18','19','20'], nowait=True)
        # Some Tuya devices will not accept the DPS index values for UPDATEDPS - try:
        # payload = d.generate_payload(tinytuya.UPDATEDPS)
        # d.send(payload)

        # poll for status
        print(" > Send Request for Status < ")
        data = d.status()
        status_time = time.time() + STATUS_TIMER
        heartbeat_time = time.time() + KEEPALIVE_TIMER
    elif time.time() >= heartbeat_time:
        # send a keep-alive
        data = d.heartbeat(nowait=False)
        heartbeat_time = time.time() + KEEPALIVE_TIMER
    else:
        # no need to send anything, just listen for an asynchronous update
        data = d.receive()
    
    if data is not None:
        print(f'{DEVICE_NAME}: Received Payload: %r' % data)
        # Print formatted DPS data
        try:
            print_dps(data, device_info, DEVICE_NAME)
            print("-" * 40)
        except Exception as e:
            print(f"Error parsing DPS: {e}")
    
    if data :
        # No guardar si hay un Error
        if 'Error' not in data:
            try:
                insert_status_db(DEVICE_NAME, data)
                #print("Status guardado en MariaDB para", DEVICE_NAME)
            except Exception as e:
                print("No se pudo guardar en MariaDB:", e)


    if data and 'Err' in data:
        print(f'{DEVICE_NAME}: Received error, watiting to retry...')
        print("Received error!")
        # rate limit retries so we don't hammer the device
        time.sleep(5)
