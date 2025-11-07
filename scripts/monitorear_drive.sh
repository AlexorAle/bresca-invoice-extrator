#!/bin/bash
# Script para monitorear Google Drive y procesar nuevos archivos
# Este script debe ejecutarse periódicamente (cron job)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Activar entorno virtual
source venv/bin/activate

# Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Log file
LOG_FILE="$PROJECT_DIR/logs/monitoreo_drive.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Iniciando monitoreo de Google Drive..." >> "$LOG_FILE"

# Ejecutar procesamiento incremental
# El sistema automáticamente:
# 1. Busca todos los PDFs en Drive
# 2. Compara con BD usando hash_contenido y drive_file_id
# 3. Solo procesa los nuevos archivos
python3 scripts/run_ingest_incremental.py >> "$LOG_FILE" 2>&1

TIMESTAMP_END=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP_END] Monitoreo completado" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

