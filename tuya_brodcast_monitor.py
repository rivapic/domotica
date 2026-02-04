import tinytuya
import json
import time
import sys
from dps_utils import load_device_info,load_device_info_by_id, print_dps
from db_mariadb import insert_status_db

# Configurar logs
LOG_FILE = "/var/log/tinituya_brodcast_monitor_d.log"

# Función para escribir logs
def log_message(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except PermissionError:
        print(f"Error: Permiso denegado al escribir en {LOG_FILE}")
    except Exception as e:
        print(f"Error escribiendo log: {e}")

print(" Monitor Tuya iniciado. Escuchando cambios en la red...")
log_message("Monitor Tuya iniciado. Escuchando cambios en la red...")

def monitor():
    # El modo monitor escucha los paquetes 'broadcast' de estado
    # No requiere Local Key para detectar QUE algo cambió
    
    # Cargar mapeos de dispositivos
    try:
        with open('devices.monitor.json', 'r') as f:
            all_devices = json.load(f)
    except FileNotFoundError:
        all_devices = []
        msg = "Warning: devices.monitor.json no encontrado. Mostrando datos sin procesar."
        print(msg)
        log_message(msg)
    
    while True:
        try:
            # Buscamos dispositivos en la red de forma continua
            devices = tinytuya.deviceScan()
            
            for ip in devices:
                dev = devices[ip]
                print(dev)
                # Solo imprimimos si el dispositivo envió datos de estado (dps)
                if 'dps' in dev and dev['dps']:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    gwId = dev['gwId']
                    device_info=load_device_info_by_id(gwId)
                    if not device_info:
                        msg = f"Device id '{gwId}' not found in devices.json"
                        print(msg)
                        log_message(msg)
                        sys.exit(1)
                    DEVICE_NAME = device_info.get('name')

                    #print("--------")
                    ##print(dev)
                    #print("--------")
                    #print( dev['dps'])


                    
                    # Mostrar en pantalla
                    msg = f"Cambio detectado en {gwId} = {DEVICE_NAME} ({ip})"
                    print(f"\n[{timestamp}] {msg}")
                    log_message(msg)
                    print("-" * 50)

                    DPS = dev['dps']
                    print_dps(DPS, device_info, DEVICE_NAME)
                    # Buscar device info y mostrar datos formateados

                    insert_status_db(DEVICE_NAME, DPS, ip=dev['ip'], origin=dev['origin'])

                    

                        
        except KeyboardInterrupt:
            msg = "Monitor detenido por el usuario."
            print(f"\n{msg}")
            log_message(msg)
            break
        except Exception as e:
            msg = f"Error: {e}"
            print(msg)
            log_message(msg)
            time.sleep(2) # Pausa breve antes de reintentar

if __name__ == "__main__":
    monitor()