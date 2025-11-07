#!/bin/bash
# Script para iniciar la API del dashboard

# Activar entorno virtual
source venv/bin/activate

# Ejecutar API
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

