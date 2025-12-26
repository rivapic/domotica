#!/usr/bin/env python3

import tinytuya
import base64
import time
import json


INTESIDAD_CONTRATADA= 16   ### La intensidad contrada 16*230= 3680w
device_name = "Automatico" ### El nombre que le pones a tu dispositivo Tuya
IP_ADDRESS = 'Auto'        ### La Ip local o Auto para automatico

print (tinytuya.version)


# Cargar el archivo devices.json extraido con tinytuya wizzard
with open('devices.json', 'r') as file:
    devices = json.load(file)


# Buscar un dispositivo por nombre
device_info = next((device for device in devices if device["name"] == device_name), None)

if device_info:
    DEVICE_ID = device_info["id"]
    LOCAL_KEY = device_info["key"]
    mapping = device_info.get("mapping", {})
    ##print(f"Mapping del dispositivo {device_name}: {mapping}")


    print(f"Configurando dispositivo: {device_name}")
else:
    print(f"Dispositivo {device_name} no encontrado en devices.json")


# Crear un diccionario inverso para mapear dps a códigos
dps_to_code = {str(dps): data["code"] for dps, data in mapping.items()}
#print(f"Diccionario dps a código: {dps_to_code}")


# Función para configurar el dispositivo Tuya
def setup_device():
    device = tinytuya.OutletDevice(dev_id=DEVICE_ID, address=IP_ADDRESS, local_key=LOCAL_KEY, version=3.3)
    return device

# Función para enviar una solicitud de estado al dispositivo
def request_status(device):
    response = device.status()
    #print("Respuesta de status:", response)
    return response

# Función para recibir datos del dispositivo
def receive_data(device):
    data = device.receive()
    #print("Datos recibidos:", data)
    return data

# Función para decodificar la Tension Intensidad y potencia
def decode_phase(value):
            ##print(value)
            decoded_value = base64.b64decode(value)
            ##binary_value = bin(int.from_bytes(decoded_value, byteorder='big'))
            #print('---Binary:',binary_value)
            binary_value = ''.join(format(byte, '08b') for byte in decoded_value)
            ##print('---Binary:',binary_value2)
            binary_value_imprimible = ' '.join(format(byte, '08b') for byte in decoded_value)
            grupo1 = binary_value[:16] 
            Tension= int(grupo1,2)
            grupo2 = binary_value[16:40]
            Intensidad = int(grupo2, 2)
            grupo3 = binary_value[-24:]
            Potencia = int(grupo3,2)
            bytes_decimal = [int.from_bytes(decoded_value[i:i+3], byteorder='big') for i in range(0, len(decoded_value), 3)]
           # print('Data RAW DP 6= %r' % data['dps']['6'])
           # print('decoded_value',decoded_value)
           # print('Binary:', binary_value_imprimible)
           # print('grupo1:',grupo1 , '        Tension:', voltaje /10,'V')
           # print('grupo2:',grupo2 , 'Intensidad:', intensidad /1000,'A' )
           # print('grupo3:',grupo3, 'Potencia:', potencia /1000,'KW' )
            print(' Tension:', Tension /10,'V')
            print(' Intensidad:', Intensidad /1000,'A' )
            print(' Potencia:', Potencia /1000,'KW' ) 
            porcentaje= (Intensidad/10)/INTESIDAD_CONTRATADA
            print(' Porcentaje contratado:', porcentaje ,'%' )

# Función para procesar los datos recibidos
def process_data(data):
     if data and 'dps' in data:

        timestamp = data.get("t")  # El timestamp está en la clave 't'
        if timestamp:
            # Convertir el timestamp a una fecha y hora legible
            readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            print(f"Timestamp: {readable_time}")
        #else:
            #print("No se encontró timestamp en los datos recibidos.")

        for dps, value in data['dps'].items():
            code = dps_to_code.get(dps, f"dps_{dps}")  # Si no se encuentra el código, usa "dps_X"
            print(f"Código: {code}, Valor: {value}")

            # Aquí puedes agregar lógica específica para cada código
            if code == "phase_a":
                decode_phase(value)
        print("-" * 40)  # Separador para mejor legibilidad



# Función principal
def main():
    device = setup_device()
    #Solicitar el estado del dispositivo

    try:
        process_data(request_status(device))
        
        # Recibir los datos desde el dispositivo
        received_data = receive_data(device)
            
        # Procesar los datos recibidos
        process_data(received_data)

    except KeyboardInterrupt:
        print("\nSaliendo del programa...")

# Ejecutar el programa si es el archivo principal
if __name__ == '__main__':
    main()
