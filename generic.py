#!/usr/bin/env python3
# TinyTuya Generic Monitor - Reads device params from devices.json
# -*- coding: utf-8 -*-

import tinytuya
import time
import json
import sys
import base64
from datetime import datetime
from db_mariadb import insert_status_db

##tinytuya.set_debug(True)

# Load devices.json and get device by name from command-line argument
if len(sys.argv) < 2:
    print("Uso: ./generic.py <nombre_dispositivo>")
    sys.exit(1)

target_device_name = sys.argv[1]

try:
    with open('devices.json', 'r') as f:
        devices = json.load(f)
except FileNotFoundError:
    print("Error: devices.json not found.")
    sys.exit(1)

device_info = next((d for d in devices if d['name'] == target_device_name), None)
if not device_info:
    print(f"Error: Device '{target_device_name}' not found in devices.json.")
    sys.exit(1)

# Extract device parameters
DEVICEID = device_info.get('id')
DEVICEKEY = device_info.get('key')
DEVICEIP = device_info.get('ip', 'Auto')  # Use 'Auto' if IP is not specified
DEVICEVERSION = device_info.get('version', '3.3')  # Default to 3.3 if not specified
DEVICE_NAME = device_info.get('name')

# Setting the address to 'Auto' or None will trigger a scan which will auto-detect both the address and version, but this can take up to 8 seconds
d = tinytuya.Device(DEVICEID,DEVICEIP, DEVICEKEY, version=DEVICEVERSION, persist=True)
# If you know both the address and version then supplying them is a lot quicker
# d = tinytuya.Device(DEVICEID, DEVICEIP, DEVICEKEY, version=DEVICEVERSION, persist=True)

STATUS_TIMER = 30
KEEPALIVE_TIMER = 12



# Funciones para parsear y decodificar DPS (copiadas de generico.py)
def _parse_values_obj(obj):
    # mapping entries sometimes store JSON as strings; try to parse
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except Exception:
            return {}
    return {}

def get_scale_for(dps_key, mapping):
    entry = mapping.get(str(dps_key), {})
    # check 'values'
    vals = _parse_values_obj(entry.get('values', {}))
    if isinstance(vals, dict) and 'scale' in vals:
        try:
            return int(vals['scale'])
        except Exception:
            pass
    # check 'raw_values' (often a JSON string)
    raw = _parse_values_obj(entry.get('raw_values', {}))
    if isinstance(raw, dict) and 'scale' in raw:
        try:
            return int(raw['scale'])
        except Exception:
            pass
    return None

def scale_value(dps_key, raw_value, mapping):
    # Try to convert numeric, otherwise return as-is
    try:
        num = float(raw_value)
    except Exception:
        return raw_value
    scale = get_scale_for(dps_key, mapping)
    if scale is not None:
        return num / (10 ** scale)
    return num

def get_code_for(dps_key, mapping):
    return mapping.get(str(dps_key), {}).get('code', 'N/A')

def get_unit_for(dps_key, mapping):
    entry = mapping.get(str(dps_key), {})
    # check 'values'
    vals = _parse_values_obj(entry.get('values', {}))
    if isinstance(vals, dict) and 'unit' in vals:
        return vals['unit']
    # check 'raw_values'
    raw = _parse_values_obj(entry.get('raw_values', {}))
    if isinstance(raw, dict) and 'unit' in raw:
        return raw['unit']
    return None

def get_type_for(dps_key, mapping):
    return mapping.get(str(dps_key), {}).get('type', 'N/A')

def dps_sort_key(item):
    k, _ = item
    try:
        return int(k)
    except Exception:
        return k

def decode_phase(value):
    decoded_value = base64.b64decode(value)
    binary_value = ''.join(format(byte, '08b') for byte in decoded_value)
    Tension = int(binary_value[:16], 2)
    Intensidad = int(binary_value[16:40], 2)
    Potencia = int(binary_value[-24:], 2)
    print(' Tension:', Tension / 10, 'V')
    print(' Intensidad:', Intensidad / 1000, 'A')
    print(' Potencia:', Potencia / 1000, 'KW')

def print_dps(dps_data, device_info, device_name):
    """Print formatted DPS data from status payload"""
    if not dps_data or 'dps' not in dps_data:
        return
    
    dps = dps_data['dps']
    mapping = device_info.get('mapping', {}) or {}
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Dispositivo: {device_name} a las {now}")
    
    # Imprimir timestamp si está disponible
    if 't' in dps_data:
        try:
            timestamp = int(dps_data['t'])
            dt = datetime.fromtimestamp(timestamp)
            dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            print(f"Timestamp: {dt_str}")
        except Exception as e:
            print(f"Timestamp: {dps_data['t']} (error al convertir: {e})")
    
    for k, v in sorted(dps.items(), key=dps_sort_key):
        code = get_code_for(k, mapping)
        scaled = scale_value(k, v, mapping)
        data_type = get_type_for(k, mapping)
        unit = get_unit_for(k, mapping)
        
        # Format output based on type
        if data_type == "Boolean":
            output = f"{code}={v}"
        else:
            output = f"{code}={scaled}"
            if unit:
                output += f" {unit}"
        
        print(output)
        if code == "phase_a":
            decode_phase(v)
        




print(f" > Monitoring Device: {DEVICE_NAME} < ")
print(" > Send Request for Status < ")
data = d.status()
print('Initial Status: %r' % data)
print_dps(data, device_info, DEVICE_NAME)
print("-" * 40)

if data and 'Err' in data:
    print("Status request returned an error, is version %r and local key %r correct?" % (d.version, d.local_key))
    
if data is not None:
    print(f'{DEVICE_NAME}: Received Payload: %r' % data)
    # Print formatted DPS data
    try:
        print_dps(data, device_info, DEVICE_NAME)
        print("-" * 40)
    except Exception as e:
        print(f"Error parsing DPS: {e}")
    
if data :
    try:
        insert_status_db(DEVICE_NAME, data)
        #print("Status guardado en MariaDB para", DEVICE_NAME)
    except Exception as e:
        print("No se pudo guardar status en MariaDB:", e)

if data and 'Err' in data:
    print("Received error!")
    # rate limit retries so we don't hammer the device
    time.sleep(20)
