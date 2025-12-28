# Configuración del Monitor Tuya como Demonio de Linux

## Descripción
El demonio `tuya_local_monitor.sh` ejecuta múltiples instancias de `generic_monitor_d.py`, una para cada dispositivo listado en `devices.monitor.json`. Todos los logs se guardan en `/var/log/`.

## Instalación

### Instalación automática (recomendado)
```bash
cd /home/riva/src/domotica
sudo chmod +x install_daemon.sh
sudo ./install_daemon.sh
```

Esto:
1. Crea el servicio systemd `tuya-local-monitor.service`
2. Lo habilita para iniciar automáticamente
3. Inicia el servicio inmediatamente

## Características

- **Monitor único**: Un solo servicio gestiona todos los dispositivos
- **Logging automático**: Logs en `/var/log/tuya_local_monitor.log` y `/var/log/generic_monitor_d.log`
- **Reinicio automático**: Si falla, systemd lo reinicia automáticamente
- **Múltiples dispositivos**: Detecta automáticamente todos los dispositivos en `devices.json`
- **Gestión de procesos**: Si un monitor falla, se reinicia automáticamente

## Comandos útiles

### Ver estado del servicio
```bash
sudo systemctl status tuya-local-monitor.service
```

### Ver logs en tiempo real (demonio principal)
```bash
journalctl -u tuya-local-monitor.service -f
```

### Ver logs del archivo de demonio
```bash
tail -f /var/log/tuya_local_monitor.log
```

### Ver logs de un dispositivo específico
```bash
tail -f /var/log/generic_monitor_d_lampara_salon.log
```

### Ver logs de todos los dispositivos
```bash
tail -f /var/log/generic_monitor_d_*.log
```

### Detener el servicio
```bash
sudo systemctl stop tuya-local-monitor.service
```

### Reiniciar el servicio
```bash
sudo systemctl restart tuya-local-monitor.service
```

### Ver PIDs de los procesos en ejecución
```bash
ps aux | grep generic_monitor_d.py
```

### Deshabilitar el servicio (no se inicia al reboot)
```bash
sudo systemctl disable tuya-local-monitor.service
```

## Estructura de logs

Los logs se organizan de la siguiente manera:

1. **`/var/log/tuya_local_monitor.log`**
   - Log del script demonio principal
   - Información de lanzamiento/parada de procesos
   - Errores en la configuración

2. **`/var/log/generic_monitor_d_<nombre_dispositivo>.log`**
   - Un archivo de log **para cada dispositivo**
   - Estado específico de cada dispositivo
   - Errores de base de datos por dispositivo

**Ejemplo:**
```
/var/log/generic_monitor_d_lampara_salon.log
/var/log/generic_monitor_d_aire_acondicionado.log
/var/log/generic_monitor_d_termostato.log
```

## Monitoreo

Para monitorear el estado de dispositivos específicos:
```bash
# Ver logs del demonio principal
tail -f /var/log/tuya_local_monitor.log

# Ver logs de un dispositivo
tail -f /var/log/generic_monitor_d_nombre_dispositivo.log

# Ver logs de todos los dispositivos
tail -f /var/log/generic_monitor_d_*.log
```

## Configuración adicional

### Cambiar nivel de logging en generic_monitor_d.py
En [generic_monitor_d.py](generic_monitor_d.py), línea que comienza con `level=logging.INFO`:
- `logging.DEBUG` - Muy detallado
- `logging.INFO` - Información general (predeterminado)
- `logging.WARNING` - Solo advertencias y errores
- `logging.ERROR` - Solo errores

### Cambiar ubicación de logs
Si necesitas cambiar `/var/log` a otra ubicación, edita:
1. `generic_monitor_d.py`: Línea `log_file = f"/var/log/generic_monitor_d_{target_device_name}.log"`
2. `tuya_local_monitor.sh`: Línea `LOG_FILE="${LOG_DIR}/tuya_local_monitor.log"`

## Rotación de logs

Los logs en `/var/log` se rotan automáticamente con `logrotate`. Para configurar la rotación personalizada, crea `/etc/logrotate.d/tuya-monitor`:

```bash
sudo nano /etc/logrotate.d/tuya-monitor
```

Añade:
```
/var/log/tuya_local_monitor.log
/var/log/generic_monitor_d_*.log
{
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0644 root root
}
```

## Desinstalación

Para remover el servicio:
```bash
sudo systemctl stop tuya-local-monitor.service
sudo systemctl disable tuya-local-monitor.service
sudo rm /etc/systemd/system/tuya-local-monitor.service
sudo systemctl daemon-reload
```

## Permisos

- El servicio se ejecuta como `root` para acceder a `/var/log`
- Si necesitas ejecutarlo como otro usuario, modifica `User=root` en `/etc/systemd/system/tuya-local-monitor.service`
- Requiere que `devices.json` sea accesible desde el directorio `/home/riva/src/domotica`
