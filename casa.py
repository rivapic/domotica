#!/usr/bin/env python3

import TermoAriston
import TuyaBreaker
import time

tiempo_espera=15

# Configurar el handler
creds = TermoAriston.get_credentials()
api_instance = TermoAriston.setup_ariston_handler(username=creds['username'], password=creds['password'], boiler_type=creds['boiler_type'])

#Configura tuya

try:
    # Obtener y mostrar los valores de los sensores
    sensor_values = api_instance.sensor_values
    
    device = TuyaBreaker.setup_device()
    #Solicitar el estado del dispositivo
    
    TuyaBreaker.process_data(TuyaBreaker.request_status(device))
    

          

    while True:
        # Recibir los datos desde el dispositivo
        TuyaBreaker.received_data = TuyaBreaker.receive_data(device)
            
        # Procesar los datos recibidos
        TuyaBreaker.process_data(TuyaBreaker.received_data)

        sensor_values = api_instance.sensor_values
        TermoAriston.print_sensor_values(sensor_values)

        time.sleep(tiempo_espera)  # Espera antes de la siguiente lectura
except KeyboardInterrupt:
        print("\n Deteniendo...")


finally:
        # Detener el handler
        api_instance.stop()
        print("TermoAriston - Detenido.")
