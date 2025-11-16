#!/bin/bash
# Script para iniciar la API del dashboard

# Activar entorno virtual
source venv/bin/activate

# Ejecutar API
# --log-config /dev/null: Deshabilitar config por defecto (usamos nuestro formatter)
# --access-log: Mantener access logs
# --no-use-colors: Sin colores en logs (mejor para JSON)
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 --log-config /dev/null --access-log --no-use-colors

