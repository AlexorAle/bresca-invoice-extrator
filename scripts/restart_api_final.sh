#!/bin/bash
# Script final para reiniciar el API correctamente

PROJECT_DIR="/home/alex/proyectos/invoice-extractor"
PORT=8001

echo "🔄 Reiniciando Invoice Extractor API..."
echo ""

# Detener TODOS los procesos uvicorn en el puerto
echo "⏹️  Deteniendo procesos..."
echo "   Ejecuta: sudo pkill -9 -f 'uvicorn.*8001'"
read -p "   Presiona Enter después de ejecutar el comando..."

# Verificar que el puerto está libre
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  El puerto $PORT todavía está en uso"
    echo "   Ejecuta: sudo lsof -ti :$PORT | xargs sudo kill -9"
    exit 1
fi

echo "✅ Puerto $PORT libre"
echo ""

# Cambiar al directorio
cd "$PROJECT_DIR" || exit 1

# Activar venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Venv activado"
else
    echo "⚠️  No se encontró venv"
    exit 1
fi

# Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
echo "✅ PYTHONPATH configurado: $PYTHONPATH"
echo ""

# Verificar que las rutas se pueden cargar
echo "🧪 Verificando que las rutas se pueden cargar..."
python3 -c "from src.api.main import app; routes = [r.path for r in app.routes if hasattr(r, 'path')]; facturas = [r for r in routes if 'factura' in r.lower()]; print(f'✅ Rutas de facturas encontradas: {len(facturas)}'); exit(0 if len(facturas) > 0 else 1)" 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Error: Las rutas no se pueden cargar"
    exit 1
fi

# Iniciar API
echo ""
echo "🚀 Iniciando API en puerto $PORT..."
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT > /tmp/invoice-api.log 2>&1 &

NEW_PID=$!
sleep 5

# Verificar
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ API iniciado (PID: $NEW_PID)"
    echo "📋 Logs: /tmp/invoice-api.log"
    echo ""
    echo "🧪 Verificando endpoints..."
    sleep 3
    
    # Verificar OpenAPI
    ENDPOINTS=$(curl -s "http://127.0.0.1:$PORT/openapi.json" 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); paths = [p for p in d.get('paths', {}).keys() if 'factura' in p.lower()]; print(len(paths))" 2>/dev/null)
    
    if [ "$ENDPOINTS" -gt 0 ]; then
        echo "✅ API respondiendo con $ENDPOINTS endpoints de facturas"
        echo ""
        echo "🧪 Probando endpoint..."
        curl -s "http://127.0.0.1:$PORT/api/facturas/summary?month=7&year=2025" | head -3
    else
        echo "⚠️  El API no tiene endpoints de facturas registrados"
        echo "📋 Revisa los logs: tail -f /tmp/invoice-api.log"
    fi
else
    echo "❌ Error al iniciar el API"
    echo "📋 Revisa los logs: tail -f /tmp/invoice-api.log"
    exit 1
fi

