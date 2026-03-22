#!/bin/sh
# Auto-generate self-signed SSL certificates if they don't exist
if [ ! -f /etc/nginx/certs/nginx.crt ] || [ ! -f /etc/nginx/certs/nginx.key ]; then
  echo "Installing openssl..."
  apk add --no-cache openssl
  echo "Generating self-signed SSL certificates..."
  mkdir -p /etc/nginx/certs
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout /etc/nginx/certs/nginx.key \
    -out /etc/nginx/certs/nginx.crt \
    -subj "/CN=domotica/O=domotica"
  echo "SSL certificates generated successfully."
else
  echo "SSL certificates already exist, skipping generation."
fi

exec nginx -g 'daemon off;'
