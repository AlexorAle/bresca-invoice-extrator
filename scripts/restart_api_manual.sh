#!/bin/bash
# Script manual para reiniciar el API (sin sudo automático)

PROJECT_DIR="/home/alex/proyectos/invoice-extractor"
PORT=8001

echo "🔄 Reiniciando Invoice Extractor API..."
echo ""

# Paso 1: Detener procesos
echo "⏹️  Paso 1: Detener procesos en puerto $PORT"
echo "   Ejecuta esto manualmente (necesita sudo):"
echo "   sudo pkill -f 'uvicorn.*8001'"
echo ""
read -p "   Presiona Enter después de ejecutar el comando sudo..."

# Verificar que se detuvo
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  El puerto $PORT todavía está en uso"
    echo "   Ejecuta: sudo lsof -ti :$PORT | xargs sudo kill -9"
    exit 1
fi

echo "✅ Puerto $PORT libre"
echo ""

# Paso 2: Cambiar al directorio
cd "$PROJECT_DIR" || exit 1

# Paso 3: Activar venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Venv activado"
else
    echo "⚠️  No se encontró venv"
fi

# Paso 4: Iniciar API
echo "🚀 Iniciando API en puerto $PORT..."
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT > /tmp/invoice-api.log 2>&1 &

NEW_PID=$!
sleep 5

# Verificar
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ API iniciado (PID: $NEW_PID)"
    echo "📋 Logs: /tmp/invoice-api.log"
    echo ""
    echo "🧪 Verificando..."
    sleep 2
    if curl -s "http://127.0.0.1:$PORT/api/facturas/summary?month=7&year=2025" | grep -q "total_facturas\|detail"; then
        echo "✅ API respondiendo correctamente"
    else
        echo "⚠️  Revisa los logs: tail -f /tmp/invoice-api.log"
    fi
else
    echo "❌ Error al iniciar"
    echo "📋 Logs: tail -f /tmp/invoice-api.log"
    exit 1
fi

