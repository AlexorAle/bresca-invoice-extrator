#!/bin/bash
# Script para verificar el estado de la carga masiva

echo "=========================================="
echo "🔍 VERIFICACIÓN DE ESTADO DE CARGA"
echo "=========================================="
echo ""

# Verificar PID
PID_FILE="/tmp/invoice_processor.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "📋 PID file encontrado: $PID"
    
    # Verificar si el proceso está corriendo
    if pgrep -f "main.py" > /dev/null 2>&1; then
        echo "✅ Proceso está CORRIENDO (PID: $PID)"
    else
        echo "⚠️  PID file existe pero proceso NO está corriendo"
        echo "   (El proceso puede haber terminado o fallado)"
    fi
else
    echo "⚠️  No se encontró PID file"
fi
echo ""

# Verificar logs recientes
LOG_FILE="/app/logs/extractor.log"
if [ -f "$LOG_FILE" ]; then
    echo "📊 ÚLTIMOS MENSAJES DEL LOG:"
    echo "---"
    tail -10 "$LOG_FILE" | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line:
        try:
            data = json.loads(line)
            ts = data.get('timestamp', '')[:19].replace('T', ' ')
            level = data.get('level', 'INFO')
            msg = data.get('msg', '')
            print(f\"[{ts}] {level}: {msg}\")
        except:
            print(line)
" 2>/dev/null || tail -10 "$LOG_FILE"
    echo "---"
    echo ""
    
    # Estadísticas
    echo "📈 ESTADÍSTICAS:"
    TOTAL_PROCESSED=$(grep -c "Factura procesada exitosamente\|ingest_complete.*exitoso" "$LOG_FILE" 2>/dev/null || echo "0")
    TOTAL_ERRORS=$(grep -c "ERROR\|ingest_error\|fallido" "$LOG_FILE" 2>/dev/null || echo "0")
    EN_PROCESO=$(grep -c "Procesando.*:" "$LOG_FILE" 2>/dev/null || echo "0")
    
    echo "   ✅ Procesadas exitosamente: $TOTAL_PROCESSED"
    echo "   ❌ Errores: $TOTAL_ERRORS"
    echo "   🔄 Intentos de procesamiento: $EN_PROCESO"
    echo ""
else
    echo "⚠️  Log file no encontrado: $LOG_FILE"
    echo ""
fi

# Verificar base de datos
echo "💾 ESTADO DE BASE DE DATOS:"
python3 -c "
from src.db.connection import get_db
from src.db.repositories import FacturaRepository
from sqlalchemy import text
from datetime import datetime, timedelta

try:
    db = next(get_db())
    repo = FacturaRepository(db)
    
    # Total de facturas
    total = repo.count_all()
    print(f'   Total facturas en BD: {total}')
    
    # Facturas en última hora
    result = db.execute(text(\"SELECT COUNT(*) as total FROM facturas WHERE created_at > NOW() - INTERVAL '1 hour'\"))
    ultima_hora = result.fetchone()[0]
    print(f'   Facturas en última hora: {ultima_hora}')
    
    # Facturas hoy
    result = db.execute(text(\"SELECT COUNT(*) as total FROM facturas WHERE DATE(created_at) = CURRENT_DATE\"))
    hoy = result.fetchone()[0]
    print(f'   Facturas procesadas hoy: {hoy}')
    
except Exception as e:
    print(f'   ⚠️  Error consultando BD: {e}')
" 2>&1
echo ""

# Verificar archivos temporales
echo "📁 ARCHIVOS TEMPORALES:"
TEMP_COUNT=$(ls -1 /app/temp/*.pdf 2>/dev/null | wc -l)
echo "   Archivos PDF en /app/temp: $TEMP_COUNT"
echo ""

# Verificar si hay errores recientes
echo "⚠️  ERRORES RECIENTES (últimos 5):"
grep -i "error\|exception\|traceback" "$LOG_FILE" 2>/dev/null | tail -5 | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line:
        try:
            data = json.loads(line)
            ts = data.get('timestamp', '')[:19].replace('T', ' ')
            msg = data.get('msg', '')
            print(f\"   [{ts}] {msg[:100]}\")
        except:
            print(f\"   {line[:100]}\")
" 2>/dev/null || echo "   (No se encontraron errores recientes)"
echo ""

echo "=========================================="



