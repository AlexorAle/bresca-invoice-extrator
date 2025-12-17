#!/bin/bash
# Script para monitorear el estado y ejecución del cron job de ingesta incremental

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     📊 MONITOREO DE CRON JOB - INGESTA INCREMENTAL         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar crontab
echo "📋 CONFIGURACIÓN DE CRONTAB:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec invoice-backend crontab -l 2>/dev/null | grep cron_ingest_incremental || echo "⚠️  No se encontró entrada de crontab"
echo ""

# Verificar estado del servicio cron
echo "🔧 ESTADO DEL SERVICIO CRON:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if docker exec invoice-backend bash -c "ps aux | grep -q '[c]ron'"; then
    echo "✅ Servicio cron: CORRIENDO"
else
    echo "❌ Servicio cron: NO ESTÁ CORRIENDO"
fi
echo ""

# Verificar logs
echo "📊 ESTADO DE LOGS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
LOG_FILE="/app/logs/cron/cron_ingest_incremental.log"
if docker exec invoice-backend test -f "$LOG_FILE"; then
    LOG_SIZE=$(docker exec invoice-backend stat -c%s "$LOG_FILE" 2>/dev/null || echo "0")
    LOG_SIZE_MB=$(echo "scale=2; $LOG_SIZE / 1024 / 1024" | bc 2>/dev/null || echo "0")
    LOG_MODIFY=$(docker exec invoice-backend stat -c%y "$LOG_FILE" 2>/dev/null | cut -d'.' -f1)
    echo "✅ Archivo de log existe"
    echo "   Tamaño: ${LOG_SIZE_MB} MB"
    echo "   Última modificación: $LOG_MODIFY"
else
    echo "⚠️  Archivo de log no existe aún"
fi
echo ""

# Últimas ejecuciones
echo "⏰ ÚLTIMAS EJECUCIONES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if docker exec invoice-backend test -f "$LOG_FILE"; then
    # Buscar líneas que indiquen inicio de ejecución
    docker exec invoice-backend bash -c "grep -E 'Iniciando ingesta incremental|INGESTA INCREMENTAL - GOOGLE DRIVE' $LOG_FILE 2>/dev/null | tail -5" || echo "No se encontraron ejecuciones registradas"
else
    echo "No hay logs disponibles"
fi
echo ""

# Resumen de última ejecución
echo "📈 RESUMEN DE ÚLTIMA EJECUCIÓN:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if docker exec invoice-backend test -f "$LOG_FILE"; then
    docker exec invoice-backend bash -c "tail -100 $LOG_FILE 2>/dev/null | grep -E 'RESUMEN DE EJECUCIÓN|Archivos listados|Procesados OK|Duplicados|Errores|Duración' | tail -10" || echo "No hay resumen disponible"
else
    echo "No hay logs disponibles"
fi
echo ""

# Próximas ejecuciones
echo "⏰ PRÓXIMAS EJECUCIONES PROGRAMADAS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CURRENT_HOUR=$(date +%H)
CURRENT_MINUTE=$(date +%M)
CURRENT_DATE=$(date +%Y-%m-%d)

if [ "$CURRENT_HOUR" -lt 12 ]; then
    NEXT_RUN="${CURRENT_DATE} 12:00:00"
    NEXT_RUN_DESC="Hoy a mediodía (12:00)"
else
    NEXT_DATE=$(date -d "tomorrow" +%Y-%m-%d 2>/dev/null || date -v+1d +%Y-%m-%d 2>/dev/null || echo "$CURRENT_DATE")
    NEXT_RUN="${NEXT_DATE} 00:00:00"
    NEXT_RUN_DESC="Mañana a medianoche (00:00)"
fi

echo "   Próxima ejecución: $NEXT_RUN_DESC"
echo "   Frecuencia: Cada 12 horas (00:00 y 12:00)"
echo ""

# Estadísticas de la BD
echo "💾 ESTADO DE LA BASE DE DATOS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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
    errores = estados.get('error_permanente', 0) + estados.get('error', 0)
    
    print(f'   Total facturas: {total}')
    print(f'   Procesadas: {procesadas}')
    print(f'   Con error: {errores}')
    print(f'   Progreso: {total}/1931 ({total*100/1931:.1f}%)')
    
db.close()
\"" 2>/dev/null | grep -v timestamp || echo "   No se pudo conectar a la base de datos"
echo ""

# Comandos útiles
echo "🔧 COMANDOS ÚTILES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Ver logs en tiempo real:"
echo "   docker exec invoice-backend tail -f /app/logs/cron/cron_ingest_incremental.log"
echo ""
echo "   Ver últimas 50 líneas:"
echo "   docker exec invoice-backend tail -50 /app/logs/cron/cron_ingest_incremental.log"
echo ""
echo "   Ejecutar manualmente:"
echo "   docker exec invoice-backend bash /app/scripts/cron_ingest_incremental.sh"
echo ""
echo "   Verificar crontab:"
echo "   docker exec invoice-backend crontab -l"
echo ""


