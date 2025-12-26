#!/usr/bin/bash
source .venv/bin/activate ## . .venv/bin/activate
#while true; do ./termometro.py termometro_oficina; sleep 2; done

cicloserie(){
  #./termometro.py termometro_oficina
  #./termometro.py termometro_dormitorio
  #./termometro.py termometro_salon
  #./generico-status.py puerta_entrada
  ./termo.py
}

ciclofork(){
  ./termometro.py termometro_oficina &
  ./termometro.py termometro_dormitorio &
  ./termometro.py termometro_salon &
  ./termometro.py Puerta_entrada &
}

cicloforkespera(){
  ./termometro.py termometro_oficina &
  pid1=$!
  ./termometro.py termometro_dormitorio &
  pid2=$!
  ./termometro.py termometro_salon &
  pid3=$!
  ./termometro.py Puerta_entrada &
  pid4=$!
  wait $pid1
  wait $pid2
  wait $pid3
  wait $pid4
}
  
while true; do cicloforkespera; sleep 0.1; done
