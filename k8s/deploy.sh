#!/bin/bash
# Script para desplegar domotica en Kubernetes
# Uso: ./deploy.sh [REGISTRY] [TAG]
# Ejemplo: ./deploy.sh registry.example.com/domotica latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REGISTRY="${1:-domotica}"
IMAGE_TAG="${2:-latest}"
FULL_IMAGE="${REGISTRY}:${IMAGE_TAG}"

echo "=== Desplegando Domotica en Kubernetes ==="
echo "Imagen: ${FULL_IMAGE}"
echo ""

# 1. Construir la imagen Docker
echo ">>> Construyendo imagen Docker..."
docker build -t "${FULL_IMAGE}" "${PROJECT_DIR}"

# 2. Crear namespace
echo ">>> Creando namespace..."
kubectl apply -f "${SCRIPT_DIR}/00-namespace.yaml"

# 3. Crear el ConfigMap del dashboard.json desde archivo (demasiado grande para inline)
echo ">>> Creando ConfigMap para dashboard.json..."
kubectl create configmap grafana-dashboard-json \
  --from-file=dashboard.json="${PROJECT_DIR}/dashboard.json" \
  --namespace=domotica \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Aplicar secrets y configmaps
echo ">>> Aplicando Secrets y ConfigMaps..."
kubectl apply -f "${SCRIPT_DIR}/01-secrets.yaml"
kubectl apply -f "${SCRIPT_DIR}/02-configmaps.yaml"

# 5. Aplicar PVCs
echo ">>> Aplicando PersistentVolumeClaims..."
kubectl apply -f "${SCRIPT_DIR}/03-pvcs.yaml"

# 6. Desplegar servicios
echo ">>> Desplegando MariaDB..."
kubectl apply -f "${SCRIPT_DIR}/10-mariadb.yaml"

echo ">>> Esperando a que MariaDB esté listo..."
kubectl rollout status deployment/mariadb -n domotica --timeout=120s

echo ">>> Desplegando Grafana..."
kubectl apply -f "${SCRIPT_DIR}/11-grafana.yaml"

echo ">>> Desplegando Ingress..."
kubectl apply -f "${SCRIPT_DIR}/12-ingress.yaml"

echo ">>> Desplegando monitores Python..."
kubectl apply -f "${SCRIPT_DIR}/20-tuya-broadcast-monitor.yaml"
kubectl apply -f "${SCRIPT_DIR}/21-tuya-polling-monitor.yaml"
kubectl apply -f "${SCRIPT_DIR}/22-termo-ariston.yaml"

echo ""
echo "=== Despliegue completado ==="
echo ""
echo "Verificar estado:"
echo "  kubectl get all -n domotica"
echo "  kubectl get ingress -n domotica"
echo ""
echo "Ver logs:"
echo "  kubectl logs -n domotica deployment/mariadb"
echo "  kubectl logs -n domotica deployment/grafana"
echo "  kubectl logs -n domotica deployment/tuya-broadcast-monitor"
echo "  kubectl logs -n domotica deployment/tuya-polling-monitor"
echo "  kubectl logs -n domotica deployment/termo-ariston"
echo ""

# Mostrar la info del Ingress
echo "Grafana accesible via Ingress:"
echo "  https://domotica.local"
echo ""
echo "Nota: Asegúrate de que 'domotica.local' resuelve a la IP de tu Ingress controller."
