#!/usr/bin/env python3

import tinytuya
import json
import sys
from datetime import datetime
import base64
import os
import pymysql

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
        
        # Get status or recive
        status = d.status()
        #status = d.receive()
        print(status)
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

    # --- Insert status JSON into MariaDB ---
    def get_db_config():
        # Try to read DB credentials from credentials.json under key 'mariadb'
        db_defaults = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASS', ''),
            'db': os.getenv('DB_NAME', 'domotica'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
        }
        try:
            with open('credentials.json', 'r') as cf:
                cj = json.load(cf)
                mariadb = cj.get('mariadb', {}) or {}
                if mariadb:
                    db_defaults.update({
                        'host': mariadb.get('host', db_defaults['host']),
                        'user': mariadb.get('user', db_defaults['user']),
                        'password': mariadb.get('password', db_defaults['password']),
                        'db': mariadb.get('database', db_defaults['db']),
                        'port': int(mariadb.get('port', db_defaults['port'])),
                    })
        except Exception:
            # If credentials.json not present or missing key, use env/defaults
            pass
        # Remove cursorclass before passing to connect (pymysql expects it in connect args though it's fine)
        return db_defaults

    def ensure_table(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS device_status (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    device_name VARCHAR(255),
                    ts DATETIME,
                    status_json LONGTEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )
        conn.commit()

    def insert_status_db(device_name, status_obj):
        db_conf = get_db_config()
        try:
            conn = pymysql.connect(host=db_conf['host'], user=db_conf['user'], password=db_conf['password'],
                                   database=db_conf['db'], port=int(db_conf['port']), charset=db_conf.get('charset','utf8mb4'))
            try:
                ensure_table(conn)
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO device_status (device_name, ts, status_json) VALUES (%s, NOW(), %s)",
                                (device_name, json.dumps(status_obj)))
                conn.commit()
                print("Status guardado en MariaDB para", device_name)
            finally:
                conn.close()
        except Exception as e:
            # Non-fatal: log and continue
            print("No se pudo guardar status en MariaDB:", e)

    # Try to save status into DB but don't fail if DB is unreachable
    try:
        insert_status_db(target_device_name, status)
    except Exception:
        pass

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

if __name__ == "__main__":
    main()
