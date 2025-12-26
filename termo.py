#!/usr/bin/env python3

import json
import os
import getpass
from aquaaristonremotethermo.aristonaqua import AquaAristonHandler
from db_mariadb import insert_status_db
import time

CREDENTIALS_FILE = 'credentials.json'

def get_credentials():
    """
    Obtiene las credenciales desde un archivo o las solicita al usuario.
    """
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error al leer el archivo de credenciales. Solicitando de nuevo.")
    
    print("No se encontraron credenciales guardadas. Por favor, ingréselas.")
    username = input("Usuario (email): ")
    password = getpass.getpass("Contraseña: ")
    boiler_type = input("Tipo de caldera (ej. velis): ")
    
    credentials = {
        'username': username,
        'password': password,
        'boiler_type': boiler_type
    }
    
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(credentials, f)
    
    print(f"Credenciales guardadas en {CREDENTIALS_FILE}")
    return credentials

tiempo_espera=15

# --- Insert status JSON into MariaDB ---




# Configuración inicial
def setup_ariston_handler(username, password, boiler_type):
    """
    Inicializa y retorna una instancia de AquaAristonHandler.
    """
    handler = AquaAristonHandler(username=username, password=password, boiler_type=boiler_type)
    #print(handler.version)
    handler.start()
    
    # Espera hasta que el handler esté disponible
    while not handler.available:
        time.sleep(1)
    
    return handler

# Función para imprimir los valores de los sensores
def print_sensor_values(sensor_values):
    """
    Imprime los valores de los sensores de manera formateada.
    """
    print("POWER =", sensor_values['power']['value'])
    print("HEATING =", sensor_values['heating']['value'])
    print("ECO =", sensor_values['eco']['value'])
    print("Temperatura Actual =", sensor_values['current_temperature']['value'])
    print("Temperatura Objetivo =", sensor_values['required_temperature']['value'])
    print("Tiempo requerido =", sensor_values['remaining_time']['value'])
    print("Duchas Disponibles =", sensor_values['showers']['value'])
    print("Modo =", sensor_values['mode']['value'])
    print("-" * 40)  # Separador para mejor legibilidad

# Función principal
def main():
    #print("TermoAriston - Iniciando...")

    # Obtener credenciales
    creds = get_credentials()
    
    # Configura el handler de Ariston
    api_instance = setup_ariston_handler(username=creds['username'], password=creds['password'], boiler_type=creds['boiler_type'])

    try:
        # Bucle principal para monitorear los valores de los sensores
        #while True:
        sensor_values = api_instance.sensor_values
            
        #print(sensor_values)
        insert_status_db("termo", sensor_values)
        print_sensor_values(sensor_values)
        time.sleep(tiempo_espera)  # Espera antes de la siguiente lectura

    except KeyboardInterrupt:
        print("\nTermoAriston - Deteniendo...")

    finally:
        # Detener el handler al finalizar
        api_instance.stop()
        #print("TermoAriston - Detenido.")

# Punto de entrada del programa
if __name__ == "__main__":
    main()
