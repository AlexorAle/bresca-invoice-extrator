#!/bin/bash
# Script para monitorear Google Drive y procesar nuevos archivos
# Este script puede ejecutarse desde cron o manualmente
# ADAPTADO PARA CONTENEDOR DOCKER

set -e

# Detectar si estamos en contenedor o en host
if [ -d "/app" ]; then
    # Estamos en contenedor Docker
    PROJECT_DIR="/app"
    LOG_FILE="/app/logs/monitoreo_drive.log"
else
    # Estamos en host
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
    LOG_FILE="$PROJECT_DIR/logs/monitoreo_drive.log"
    
    # Activar entorno virtual solo si existe (host)
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        source "$PROJECT_DIR/venv/bin/activate"
    fi
fi

cd "$PROJECT_DIR"

# Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Crear directorio de logs
mkdir -p "$(dirname "$LOG_FILE")"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Iniciando monitoreo de Google Drive..." >> "$LOG_FILE"

# Ejecutar procesamiento incremental
# El sistema automáticamente:
# 1. Busca todos los PDFs en Drive
# 2. Compara con BD usando hash_contenido y drive_file_id
# 3. Solo procesa los nuevos archivos
python3 "$PROJECT_DIR/scripts/run_ingest_incremental.py" >> "$LOG_FILE" 2>&1

TIMESTAMP_END=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP_END] Monitoreo completado" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

