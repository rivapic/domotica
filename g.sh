#!/usr/bin/env bash
source .venv/bin/activate  # activate virtualenv if present

# Variable para almacenar PIDs de procesos hijo
CHILD_PIDS=()

# Función para limpiar procesos hijo al recibir Ctrl+C
cleanup() {
  echo ""
  echo "Deteniendo monitores..."
  for pid in "${CHILD_PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  wait
  echo "Todos los monitores detenidos."
  exit 0
}

# Capturar Ctrl+C (SIGINT) y ejecutar cleanup
trap cleanup SIGINT

# Ejecuta ./generic_monitor_d.py <name> para cada dispositivo listado en devices.json
# Lanza todos los procesos en paralelo (cada uno ejecuta su loop de monitoreo independiente)
run_all_device_monitors(){
  # extrae la lista de nombres desde devices.json usando jq
  if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq no está instalado. Instálalo (por ejemplo: sudo apt install jq)" >&2
    return
  fi

  if [ ! -f devices.json ]; then
    echo "No se encontró devices.json" >&2
    return
  fi

  mapfile -t names < <(jq -r '.[].name // empty' devices.json)

  if [ ${#names[@]} -eq 0 ]; then
    echo "No se encontraron dispositivos en devices.json" >&2
    return
  fi

  CHILD_PIDS=()
  for name in "${names[@]}"; do
    echo "Lanzando generic_monitor_d.py para: $name"
    ./generic_monitor_d.py "$name" &
    CHILD_PIDS+=("$!")
  done

  # Esperar a todos los procesos de monitoreo (cada uno tiene su propio loop infinito)
  for pid in "${CHILD_PIDS[@]}"; do
    wait "$pid" || true
  done
}

# loop principal: correr continuamente
while true; do
  run_all_device_monitors
  sleep 1
done
