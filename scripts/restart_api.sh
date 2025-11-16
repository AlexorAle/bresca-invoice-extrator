#!/bin/bash
# Script para reiniciar el API de Invoice Extractor

PROJECT_DIR="/home/alex/proyectos/invoice-extractor"
PORT=8001

echo "🔄 Reiniciando Invoice Extractor API..."

# Encontrar y detener TODOS los procesos en el puerto 8001
echo "⏹️  Deteniendo procesos en puerto $PORT..."

# Obtener todos los PIDs que usan el puerto
PIDS=$(lsof -ti :$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{print $1}')

if [ -z "$PIDS" ]; then
    # Fallback: buscar por nombre de proceso
    PIDS=$(ps aux | grep "uvicorn.*8001" | grep -v grep | awk '{print $2}')
fi

if [ -n "$PIDS" ]; then
    echo "   Encontrados procesos: $PIDS"
    for PID in $PIDS; do
        echo "   Deteniendo PID: $PID..."
        sudo kill $PID 2>/dev/null || kill $PID 2>/dev/null
    done
    sleep 3
    
    # Forzar detención si aún están corriendo
    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            echo "   Forzando detención de PID: $PID..."
            sudo kill -9 $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
    done
    sleep 2
else
    echo "ℹ️  No hay procesos corriendo en el puerto $PORT"
fi

# Verificar que el puerto está libre
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  El puerto $PORT todavía está en uso después de intentar detener procesos"
    echo "   Ejecuta manualmente: sudo lsof -ti :$PORT | xargs sudo kill -9"
    exit 1
fi

echo "✅ Puerto $PORT libre"

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR" || exit 1

# Activar venv si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Iniciar el API
echo "🚀 Iniciando API en puerto $PORT..."

# Usar python3 -m uvicorn en lugar de uvicorn directamente
nohup python3 -m uvicorn src.api.main:app --log-config /dev/null --access-log --no-use-colors --host 0.0.0.0 --port $PORT > /tmp/invoice-api.log 2>&1 &

NEW_PID=$!
sleep 5  # Dar más tiempo para que inicie

# Verificar que está corriendo
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ API iniciado correctamente (PID: $NEW_PID)"
    echo "📋 Logs en: /tmp/invoice-api.log"
    echo ""
    echo "🧪 Verificando endpoint..."
    sleep 2
    if curl -s "http://127.0.0.1:$PORT/api/facturas/summary?month=7&year=2025" | grep -q "total_facturas\|detail"; then
        echo "✅ API respondiendo correctamente"
    else
        echo "⚠️  El API puede no estar respondiendo correctamente"
        echo "📋 Revisa los logs: tail -f /tmp/invoice-api.log"
    fi
else
    echo "❌ Error al iniciar el API"
    echo "📋 Revisa los logs: tail -f /tmp/invoice-api.log"
    exit 1
fi

