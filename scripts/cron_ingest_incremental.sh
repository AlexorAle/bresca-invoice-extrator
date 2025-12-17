#!/bin/bash
# Script específico para ejecutar ingesta incremental desde cron
# Este script está diseñado para ejecutarse dentro del contenedor Docker

set -e

# Configurar PATH para incluir ubicaciones comunes de Python
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# Configurar variables de entorno
export PYTHONPATH="/app:$PYTHONPATH"

# Directorio de logs
LOG_DIR="/app/logs/cron"
mkdir -p "$LOG_DIR"

# Archivo de log con timestamp
LOG_FILE="$LOG_DIR/cron_ingest_incremental.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Redirigir stdout y stderr al log
exec >> "$LOG_FILE" 2>&1

echo "=========================================="
echo "[$TIMESTAMP] Iniciando ingesta incremental desde cron"
echo "=========================================="

# Cambiar al directorio de la aplicación
cd /app

# Ejecutar script de ingesta incremental
# El script maneja automáticamente:
# - Detección de duplicados (drive_file_id)
# - JobLock para prevenir ejecuciones concurrentes
# - Rate limits de OpenAI
# - Manejo de errores

# Usar ruta completa de Python para evitar problemas con PATH en cron
PYTHON_CMD=$(which python3 || which python || echo "/usr/local/bin/python3")
$PYTHON_CMD /app/scripts/run_ingest_incremental.py

TIMESTAMP_END=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP_END] Ingesta incremental completada"
echo "=========================================="
echo ""


