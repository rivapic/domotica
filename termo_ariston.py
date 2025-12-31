#!/usr/bin/env python3

import json
import os
import getpass
import sys
import time
import signal
from aquaaristonremotethermo.aristonaqua import AquaAristonHandler
from db_mariadb import insert_status_db

CREDENTIALS_FILE = 'credentials.json'
LOG_FILE = "/var/log/termo_ariston.log"
POLL_INTERVAL = 180  # 180 segundos

# Variable de control para el daemon
running = True

def log_message(message):
    """Escribe un mensaje en el archivo de log"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Error escribiendo log: {e}")

def signal_handler(sig, frame):
    """Manejador de señales para apagar el daemon gracefully"""
    global running
    running = False
    log_message("Señal de parada recibida. Apagando daemon...")

def get_credentials():
    """
    Obtiene las credenciales desde un archivo o las solicita al usuario.
    """
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            msg = "Error al leer el archivo de credenciales. Solicitando de nuevo."
            print(msg)
            log_message(msg)
    
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
    
    msg = f"Credenciales guardadas en {CREDENTIALS_FILE}"
    print(msg)
    log_message(msg)
    return credentials

# Configuración inicial
def setup_ariston_handler(username, password, boiler_type):
    """
    Inicializa y retorna una instancia de AquaAristonHandler.
    """
    handler = AquaAristonHandler(username=username, password=password, boiler_type=boiler_type)
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

# Función principal del daemon
def main():
    """Función principal que corre como daemon"""
    global running
    
    # Registrar manejadores de señales
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    log_message("Daemon termo iniciado")
    
    # Obtener credenciales
    try:
        creds = get_credentials()
    except Exception as e:
        msg = f"Error obteniendo credenciales: {e}"
        log_message(msg)
        return
    
    # Configura el handler de Ariston
    try:
        api_instance = setup_ariston_handler(
            username=creds['username'], 
            password=creds['password'], 
            boiler_type=creds['boiler_type']
        )
        log_message("Conexión con Ariston establecida")
    except Exception as e:
        msg = f"Error conectando con Ariston: {e}"
        log_message(msg)
        return

    try:
        # Bucle principal - consulta el termo cada POLL_INTERVAL segundos
        while running:
            try:
                sensor_values = api_instance.sensor_values
                
                # Guardar en base de datos
                insert_status_db("termo", sensor_values)
                
                # Mostrar valores en consola
                print_sensor_values(sensor_values)
                
                # Registrar en log
                temp_actual = sensor_values.get('current_temperature', {}).get('value', 'N/A')
                temp_objetivo = sensor_values.get('required_temperature', {}).get('value', 'N/A')
                log_message(f"Temp actual: {temp_actual}°C, Objetivo: {temp_objetivo}°C")
                
                # Esperar hasta la próxima consulta
                time.sleep(POLL_INTERVAL)
                
            except Exception as e:
                msg = f"Error consultando sensores: {e}"
                log_message(msg)
                print(msg)
                # Reintentar después de un tiempo
                time.sleep(10)

    except KeyboardInterrupt:
        msg = "Daemon detenido por interrupción del usuario"
        log_message(msg)
    except Exception as e:
        msg = f"Error inesperado en daemon: {e}"
        log_message(msg)
    finally:
        # Detener el handler al finalizar
        try:
            api_instance.stop()
            log_message("Conexión con Ariston cerrada")
        except Exception as e:
            log_message(f"Error cerrando conexión: {e}")

# Punto de entrada del programa
if __name__ == "__main__":
    main()

