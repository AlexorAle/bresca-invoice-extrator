#!/bin/bash
# Script simple para iniciar el API (asume que el puerto está libre)

PROJECT_DIR="/home/alex/proyectos/invoice-extractor"
PORT=8001

cd "$PROJECT_DIR" || exit 1

# Activar venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Iniciar API
echo "🚀 Iniciando API en puerto $PORT..."
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT > /tmp/invoice-api.log 2>&1 &

NEW_PID=$!
echo "✅ API iniciado (PID: $NEW_PID)"
echo "📋 Logs: /tmp/invoice-api.log"
echo ""
echo "🧪 Espera 5 segundos y verifica:"
echo "   curl http://127.0.0.1:8001/api/facturas/summary?month=7&year=2025"

