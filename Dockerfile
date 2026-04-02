FROM python:latest

WORKDIR /app

# Instalar jq (necesario para tuya_local_monitor.sh)
RUN apt-get update && apt-get install -y --no-install-recommends jq && \
    rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY *.py ./
COPY *.sh ./
COPY *.json ./

ENV TZ=Europe/Madrid
