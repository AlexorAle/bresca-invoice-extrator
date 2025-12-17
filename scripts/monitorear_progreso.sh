#!/bin/bash
# Script para monitorear el progreso de la carga masiva

echo "=========================================="
echo "📊 MONITOREO DE CARGA MASIVA"
echo "=========================================="
echo ""

# Verificar si el proceso está corriendo
PID_FILE="/app/invoice_processor.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if docker exec invoice-backend ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Proceso activo (PID: $PID)"
    else
        echo "⚠️  PID file existe pero proceso no está corriendo"
    fi
else
    echo "❌ No se encontró PID file"
fi

echo ""

# Estadísticas de BD
docker exec invoice-backend bash -c "cd /app && PYTHONPATH=/app python3 -c \"
from src.db.database import Database
from sqlalchemy import text

db = Database()
with db.get_session() as session:
    result = session.execute(text('SELECT COUNT(*) FROM facturas'))
    total = result.scalar()
    
    result = session.execute(text('SELECT estado, COUNT(*) FROM facturas GROUP BY estado'))
    estados = dict(result.fetchall())
    
    procesadas = estados.get('procesado', 0)
    revisar = estados.get('revisar', 0)
    error = estados.get('error', 0)
    
    print(f'📊 Total facturas en BD: {total}')
    print(f'   ✅ Procesadas: {procesadas}')
    print(f'   ⚠️  En revisar: {revisar}')
    print(f'   ❌ Con error: {error}')
    
    if total > 1175:
        nuevas = total - 1175
        progreso = (nuevas / 756) * 100 if nuevas <= 756 else 100
        print(f'')
        print(f'📈 Progreso estimado: {progreso:.1f}% ({nuevas}/756 nuevas)')
    else:
        print(f'')
        print(f'📈 Progreso: 0% (aún no hay nuevas facturas)')
db.close()
\"" 2>/dev/null

echo ""
echo "📋 Últimas 10 líneas del log:"
echo "----------------------------------------"
docker exec invoice-backend bash -c "ls -t /app/logs/carga_masiva_*.log 2>/dev/null | head -1 | xargs tail -10" 2>/dev/null | sed 's/^/   /'

echo ""
echo "=========================================="

