#!/usr/bin/env python3

import tinytuya
import json
import sys
from datetime import datetime
import base64
from db_mariadb import insert_status_db

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
    product_name = device_info['product_name']
    device_name = device_info['name']
    # Using 'Auto' for IP as per common tinytuya usage when IP is dynamic or unknown
    # Using "device_info['ip'] if te ip local is en json file (normaly not I add manually before ) device_info['ip']
    #print(f"mac:  {device_info['mac']}")
    #print(f"Using IP:  {device_info['ip']}")  

    #ip_address = device_info['ip'] ## NO FUNCIONA AUNQUE SEA LA IP CORRECTA
    ip_address = 'Auto'


    #print(f"Connecting to {target_device_name}...")
    
    # Initialize the device
    # Using Device generic class as it's a sensor, not necessarily an Outlet
    # version 3.3 is standard for most new Tuya devices
    try:
        d = tinytuya.Device(dev_id=device_id, address=ip_address, local_key=device_key, version=3.3)
        
        #print("------- Product Name:", product_name)
    
        if product_name == 'Contact Sensor':
            #print("door sensor")
            status = d.status()
        elif device_name == 'Automatico':
            print(".")
        else:
            status = d.receive()

        # Get status or recive
        #status = d.status()
        #status = d.receive()
        
        
        ##### None ###
        ##print(status)
    except Exception as e:
        #print(f"Error connecting to device '{target_device_name}': {e}")
        #print("Possible causes:")
        #print("1. The device is offline or sleeping (common for battery sensors). Wake it up by pressing its button.")
        #print("2. The device is on a different network subnet.")
        #print("3. The local key is incorrect.")
        return
    
    if not status :
        #print("Failed to retrieve status from device.")
        return
    # Try to save status into DB but don't fail if DB is unreachable
    try:
        insert_status_db(target_device_name, status)
        #print("Status guardado en MariaDB para", target_device_name)
    except Exception as e:
        print("No se pudo guardar status en MariaDB:", e)

    # status sometimes contains an error payload (e.g. {'Error':..., 'Err':..., 'Payload': None})
    # Ensure we have the expected 'dps' key before proceeding to parse device points
    if not isinstance(status, dict) or 'dps' not in status:
        print("Respuesta del dispositivo no contiene 'dps', abortando parseo de DPS. status=", status)
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
        return num

    def get_code_for(dps_key):
        return mapping.get(str(dps_key), {}).get('code', 'N/A')

    def get_unit_for(dps_key):
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

    def get_type_for(dps_key):
        return mapping.get(str(dps_key), {}).get('type', 'N/A')

    def dps_sort_key(item):
        k, _ = item
        try:
            return int(k)
        except Exception:
            return k

    # Función para decodificar la Tension Intensidad y potencia
    def decode_phase(value):
            decoded_value = base64.b64decode(value)
            binary_value = ''.join(format(byte, '08b') for byte in decoded_value)
            Tension= int(binary_value[:16],2)
            Intensidad = int(binary_value[16:40],2)
            Potencia = int(binary_value[-24:],2)
            print(' Tension:', Tension /10,'V')
            print(' Intensidad:', Intensidad /1000,'A' )
            print(' Potencia:', Potencia /1000,'KW' ) 

    # Imprimir todos los DPS con su código y valor
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Dispositivo: {target_device_name} a las {now}")
    for k, v in sorted(dps.items(), key=dps_sort_key):
        code = get_code_for(k)
        scaled = scale_value(k, v)
        data_type = get_type_for(k)
        unit = get_unit_for(k)
        #print(f"DPS {k} ({code}): raw={v} scaled={scaled}")
        
        # Format output based on type
        if data_type == "Boolean":
            output = f"{code}={v}"
        else:
            output = f"{code}={scaled}"
            if unit:
                output += f" {unit}"
        
        print(output)
        if code=="phase_a":
            decode_phase(v)
        print("-" * 40) 

if __name__ == "__main__":
    main()
