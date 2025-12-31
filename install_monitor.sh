#!/bin/bash
# Script para instalar monitores como servicios systemd

if [ "$EUID" -ne 0 ]; then 
    echo "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

LOG_DIR="/var/log"
SCRIPTS_DIR="/home/riva/src/domotica"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"

# Función para instalar servicio Python
install_python_service() {
    local service_name=$1
    local script_name=$2
    local service_file="/etc/systemd/system/${service_name}.service"
    local script_path="${SCRIPTS_DIR}/${script_name}"
    
    echo ""
    echo "=========================================="
    echo "Instalando: $service_name"
    echo "=========================================="
    
    if [ ! -f "$script_path" ]; then
        echo "Error: $script_path no encontrado"
        return 1
    fi
    
    # Hacer el script ejecutable
    chmod +x "$script_path"
    
    echo "Creando archivo de servicio..."
    cat > "$service_file" << EOF
[Unit]
Description=$service_name
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPTS_DIR
ExecStart=/usr/bin/python3 $script_path
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl_operations "$service_name"
}

# Función para instalar servicio Shell Script
install_shell_service() {
    local service_name=$1
    local script_name=$2
    local service_file="/etc/systemd/system/${service_name}.service"
    local script_path="${SCRIPTS_DIR}/${script_name}"
    
    echo ""
    echo "=========================================="
    echo "Instalando: $service_name"
    echo "=========================================="
    
    if [ ! -f "$script_path" ]; then
        echo "Error: $script_path no encontrado"
        return 1
    fi
    
    # Hacer el script ejecutable
    chmod +x "$script_path"
    
    echo "Creando archivo de servicio..."
    cat > "$service_file" << EOF
[Unit]
Description=$service_name
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPTS_DIR
ExecStart=/bin/bash $script_path
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl_operations "$service_name"
}

# Operaciones comunes de systemctl
systemctl_operations() {
    local service_name=$1
    
    echo "Recargando systemd daemon..."
    systemctl daemon-reload
    
    echo "Habilitando servicio..."
    systemctl enable "$service_name.service"
    
    echo "Iniciando servicio..."
    systemctl start "$service_name.service"
    
    echo ""
    echo "Estado del servicio:"
    systemctl status "$service_name.service" || true
    
    echo ""
    echo "Para ver los logs:"
    echo "  journalctl -u ${service_name}.service -f"
    echo ""
}

# Instalar demonios automáticos
echo ""
echo "########################################"
echo "# Instalando Demonios de Monitoreo    #"
echo "########################################"

# Instalar broadcast monitor (Python)
install_python_service "generic-brodcast-monitor-d" "generic_brodcast_monitor.py"

# Instalar termo ariston (Python)
install_python_service "termo-ariston-d" "termo.py"

# Instalar tuya local monitor (Shell script)
install_shell_service "tuya-local-monitor-d" "tuya_local_monitor.sh"

echo ""
echo "########################################"
echo "# Instalación Completada              #"
echo "########################################"
echo ""
echo "Servicios instalados:"
systemctl list-units --type=service | grep -E "monitor-d|ariston-d"
echo ""
echo "Para ver todos los logs:"
echo "  sudo journalctl -f"
echo ""
echo "Comandos útiles:"
echo "  Ver estado:     systemctl status <nombre_servicio>"
echo "  Reiniciar:      sudo systemctl restart <nombre_servicio>"
echo "  Detener:        sudo systemctl stop <nombre_servicio>"
echo "  Ver logs vivos: sudo journalctl -u <nombre_servicio> -f"

