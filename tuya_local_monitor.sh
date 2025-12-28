#!/usr/bin/env bash
# Demonio que ejecuta monitores para todos los dispositivos Tuya
# Este script lanza generic_monitor_d.py para cada dispositivo en devices.monitor.json

# Directorio de logs
LOG_DIR="/var/log"
LOG_FILE="${LOG_DIR}/tuya_local_monitor.log"

# Función para loguear
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR" 2>/dev/null || true

# Iniciar logging
log "INFO" "========================================="
log "INFO" "Iniciando demonio Tuya Local Monitor"
log "INFO" "========================================="

# Activar virtualenv si existe
if [ -f .venv/bin/activate ]; then
    log "INFO" "Activando virtualenv..."
    source .venv/bin/activate
fi

# Variable para almacenar PIDs de procesos hijo
CHILD_PIDS=()

# Función para limpiar procesos hijo al recibir señal SIGTERM
cleanup() {
    log "INFO" "Recibida señal de parada. Deteniendo monitores..."
    for pid in "${CHILD_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            log "INFO" "Deteniendo proceso PID: $pid"
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null || true
    log "INFO" "Todos los monitores detenidos."
    log "INFO" "========================================="
    exit 0
}

# Capturar SIGTERM (desde systemd) e SIGINT (Ctrl+C)
trap cleanup SIGTERM SIGINT

# Ejecuta ./generic_monitor_d.py <name> para cada dispositivo listado en devices.monitor.json
# Lanza todos los procesos en paralelo (cada uno ejecuta su loop de monitoreo independiente)
run_all_device_monitors(){
  # extrae la lista de nombres desde devices.monitor.json usando jq
  if ! command -v jq >/dev/null 2>&1; then
    log "ERROR" "jq no está instalado. Instálalo (por ejemplo: sudo apt install jq)"
    return 1
  fi

  if [ ! -f devices.monitor.json ]; then
    log "ERROR" "No se encontró devices.monitor.json en $(pwd)"
    return 1
  fi

  mapfile -t names < <(jq -r '.[].name // empty' devices.monitor.json)

  if [ ${#names[@]} -eq 0 ]; then
    log "ERROR" "No se encontraron dispositivos en devices.monitor.json"
    return 1
  fi

  log "INFO" "Se encontraron ${#names[@]} dispositivo(s)"

  # Detener procesos anteriores si los hay
  for pid in "${CHILD_PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done

  for name in "${names[@]}"; do
    log "INFO" "Lanzando monitor para dispositivo: $name"
    ./generic_monitor_d.py "$name" >> "$LOG_FILE" 2>&1 &
    CHILD_PIDS+=("$!")
    log "INFO" "Monitor para '$name' lanzado con PID: ${CHILD_PIDS[-1]}"
  done

  # Esperar a todos los procesos de monitoreo (cada uno tiene su propio loop infinito)
  for pid in "${CHILD_PIDS[@]}"; do
    wait "$pid" || true
  done
}

# loop principal: correr continuamente
log "INFO" "Iniciando loop principal de monitoreo..."
while true; do
  run_all_device_monitors
  log "WARNING" "Se perdió la conexión con los monitores o hubo un error. Reiniciando en 5 segundos..."
  sleep 5
done
