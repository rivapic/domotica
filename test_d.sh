#!/usr/bin/bash
source .venv/bin/activate ## . .venv/bin/activate

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

ciclo(){
  CHILD_PIDS=()
  ./generic_monitor_d.py  termometro_salon &
  CHILD_PIDS+=("$!")
  ./generic_monitor_d.py termometro_oficina &
  CHILD_PIDS+=("$!")
  ./generic_monitor_d.py  termometro_dormitorio &
  CHILD_PIDS+=("$!")
  ./generic_monitor_d.py  termometro_display &
  CHILD_PIDS+=("$!")
  ./generic_monitor_d.py  Puerta_entrada &
  CHILD_PIDS+=("$!")
  
  
  # Esperar a que todos terminen
  for pid in "${CHILD_PIDS[@]}"; do
    wait "$pid" || true
  done
}

ciclo
