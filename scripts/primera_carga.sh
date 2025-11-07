#!/bin/bash
# Script para primera carga de facturas desde Google Drive
# Este script procesa TODOS los archivos actuales en Drive

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Activar entorno virtual
source venv/bin/activate

# Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

echo "=========================================="
echo "PRIMERA CARGA DE FACTURAS"
echo "=========================================="
echo ""
echo "Este script procesará TODOS los PDFs encontrados en Google Drive"
echo "Solo procesará archivos que NO estén ya en la base de datos"
echo ""

# Ejecutar procesamiento
# El sistema automáticamente:
# 1. Busca todos los PDFs en Drive
# 2. Compara con BD usando hash_contenido
# 3. Solo procesa los nuevos
python3 src/main.py

echo ""
echo "=========================================="
echo "PRIMERA CARGA COMPLETADA"
echo "=========================================="

