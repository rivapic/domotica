#!/usr/bin/env python3

import tinytuya
import json
import sys
from datetime import datetime

def main():
    # Load devices.json
    try:
        with open('devices.json', 'r') as f:
            devices = json.load(f)
    except FileNotFoundError:
        print("Error: devices.json not found.")
        return

    # Obtener el nombre del dispositivo desde el primer argumento de la terminal
    if len(sys.argv) < 2:
        print("Uso: termometro.py <nombre_dispositivo>")
        return
    target_device_name = sys.argv[1]

    device_info = next((d for d in devices if d['name'] == target_device_name), None)

    if not device_info:
        print(f"Error: Device '{target_device_name}' not found in devices.json.")
        return

    # Extract device details
    device_id = device_info['id']
    device_key = device_info['key']
    # Using 'Auto' for IP as per common tinytuya usage when IP is dynamic or unknown
    ip_address = 'Auto' 

    #print(f"Connecting to {target_device_name}...")
    
    # Initialize the device
    # Using Device generic class as it's a sensor, not necessarily an Outlet
    # version 3.3 is standard for most new Tuya devices
    try:
        d = tinytuya.Device(dev_id=device_id, address=ip_address, local_key=device_key, version=3.3)
        
        # Get status
        status = d.status()
    except Exception as e:
        #print(f"Error connecting to device '{target_device_name}': {e}")
        #print("Possible causes:")
        #print("1. The device is offline or sleeping (common for battery sensors). Wake it up by pressing its button.")
        #print("2. The device is on a different network subnet.")
        #print("3. The local key is incorrect.")
        return
    
    if not status or 'dps' not in status:
        print("Failed to retrieve status from device.")
        return

    dps = status['dps']
    mapping = device_info.get('mapping', {}) or {}

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

    def get_scale_for(dps_key):
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
        # raw_values can describe multiple sub-keys; for simple types it may contain 'scale'
        if isinstance(raw, dict) and 'scale' in raw:
            try:
                return int(raw['scale'])
            except Exception:
                pass
        return None

    def scale_value(dps_key, raw_value):
        # Try to convert numeric, otherwise return as-is
        try:
            num = float(raw_value)
        except Exception:
            return raw_value
        scale = get_scale_for(dps_key)
        if scale is not None:
            return num / (10 ** scale)
        # fallback: keep previous behaviour for temperature/humidity
        if str(dps_key) in ('1', '2'):
            return num / 10.0
        return num

    def get_code_for(dps_key):
        return mapping.get(str(dps_key), {}).get('code', 'N/A')

    def dps_sort_key(item):
        k, _ = item
        try:
            return int(k)
        except Exception:
            return k

    # Imprimir todos los DPS con su código y valor raw/escala
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Dispositivo: {target_device_name} a las {now}")
    for k, v in sorted(dps.items(), key=dps_sort_key):
        code = get_code_for(k)
        scaled = scale_value(k, v)
        #print(f"DPS {k} ({code}): raw={v} scaled={scaled}")
        print(f"{code}={scaled}")

    # Mostrar resumen de temperatura/humedad si existen
    if '1' in dps:
        temperature = scale_value('1', dps['1'])
        humedad = scale_value('2', dps.get('2')) if '2' in dps else None

        #print(f"Temperatura {target_device_name} {now} : {temperature} °C")
        #if humedad is not None:
        #    print(f"Humedad {target_device_name} {now} : {humedad} %")
    else:
        print("Temperature data (DPS 1) not found in response.")
        print(f"Full response: {status}")

if __name__ == "__main__":
    main()
