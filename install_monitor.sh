#!/bin/bash
# Script para instalar el monitor genérico como servicio systemd

if [ "$EUID" -ne 0 ]; then 
    echo "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Uso: sudo ./install_monitor.sh <nombre_dispositivo>"
    echo "Ejemplo: sudo ./install_monitor.sh mi_lampara"
    exit 1
fi

DEVICE_NAME="$1"
SERVICE_NAME="generic-monitor-d@${DEVICE_NAME}.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"
TEMPLATE_FILE="/home/riva/src/domotica/generic-monitor-d.service"
SCRIPT_PATH="/home/riva/src/domotica/generic_monitor_d.py"
LOG_DIR="/var/log"

# Crear archivo de servicio personalizado
echo "Creando servicio: $SERVICE_NAME"
sudo sed "s/device_name/${DEVICE_NAME}/g" "$TEMPLATE_FILE" > "$SERVICE_FILE"

# Asegurar permisos en el directorio de logs
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Recargar systemd
echo "Recargando systemd daemon..."
systemctl daemon-reload

# Habilitar el servicio para que se inicie automáticamente
echo "Habilitando servicio..."
systemctl enable "$SERVICE_NAME"

# Iniciar el servicio
echo "Iniciando servicio..."
systemctl start "$SERVICE_NAME"

# Mostrar estado
echo ""
echo "Estado del servicio:"
systemctl status "$SERVICE_NAME"

echo ""
echo "Para ver los logs:"
echo "  journalctl -u $SERVICE_NAME -f"
echo ""
echo "Para detener el servicio:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo ""
echo "Para reiniciar el servicio:"
echo "  sudo systemctl restart $SERVICE_NAME"
