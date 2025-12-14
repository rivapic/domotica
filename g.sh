#!/usr/bin/env bash
source .venv/bin/activate  # activate virtualenv if present

# Ejecuta ./generico.py <name> para cada dispositivo listado en devices.json
# Lanza todos los procesos en paralelo y espera a que terminen antes de repetir
run_all_devices(){
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

  pids=()
  for name in "${names[@]}"; do
    #echo "Lanzando generico.py para: $name"
    ./generico.py "$name" &
    pids+=("$!")
  done

  # Esperar a todos los procesos lanzados
  for pid in "${pids[@]}"; do
    wait "$pid" || true
  done
}

# loop principal: correr continuamente con un pequeño retardo
while true; do
  run_all_devices
  sleep 1
done
