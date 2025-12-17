#!/bin/bash
# Script de monitoreo mejorado para carga masiva de facturas
# Permite ver logs en tiempo real, estadísticas y detener ejecución

LOG_FILE="/app/logs/extractor.log"
PID_FILE="/tmp/invoice_processor.pid"
STOP_FILE="/tmp/stop_processing.flag"
STATS_FILE="/tmp/processing_stats.json"

echo "=========================================="
echo "🔍 MONITOREO DE CARGA MASIVA"
echo "=========================================="
echo ""

# Función para parsear JSON de logs
parse_json_log() {
    local line="$1"
    # Extraer campos del JSON
    echo "$line" | grep -o '"msg":"[^"]*"' | sed 's/"msg":"\(.*\)"/\1/'
}

# Función para obtener estadísticas
get_stats() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "0|0|0"
        return
    fi
    
    # Contar facturas procesadas exitosamente
    EXITOSOS=$(grep -c "Factura procesada exitosamente\|ingest_complete.*exitoso" "$LOG_FILE" 2>/dev/null || echo "0")
    
    # Contar errores
    ERRORES=$(grep -c "ERROR\|ingest_error\|fallido" "$LOG_FILE" 2>/dev/null || echo "0")
    
    # Contar en proceso
    EN_PROCESO=$(grep -c "Procesando.*:" "$LOG_FILE" 2>/dev/null || echo "0")
    
    echo "${EXITOSOS}|${ERRORES}|${EN_PROCESO}"
}

# Función para mostrar estadísticas
show_stats() {
    local stats=$(get_stats)
    local exitosos=$(echo "$stats" | cut -d'|' -f1)
    local errores=$(echo "$stats" | cut -d'|' -f2)
    local en_proceso=$(echo "$stats" | cut -d'|' -f3)
    
    echo ""
    echo "📊 ESTADÍSTICAS ACTUALES:"
    echo "   ✅ Procesadas exitosamente: $exitosos"
    echo "   ❌ Errores: $errores"
    echo "   🔄 En proceso: $en_proceso"
    echo "   📈 Total procesadas: $((exitosos + errores))"
    echo ""
}

# Función para detener procesamiento
stop_processing() {
    echo ""
    echo "🛑 Deteniendo procesamiento..."
    touch "$STOP_FILE"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Enviando señal de interrupción al proceso $PID..."
            kill -INT "$PID" 2>/dev/null
            sleep 2
            
            # Si aún está corriendo, forzar
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Forzando detención..."
                kill -9 "$PID" 2>/dev/null
            fi
        fi
    fi
    
    echo "✅ Procesamiento detenido"
    show_stats
    exit 0
}

# Trap para capturar Ctrl+C
trap stop_processing INT TERM

# Verificar si hay proceso corriendo
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Proceso detectado (PID: $PID)"
    else
        echo "⚠️  PID file existe pero proceso no está corriendo"
    fi
else
    echo "⚠️  No se detectó proceso activo"
    echo "   (El proceso puede no haber iniciado o ya terminó)"
fi

# Mostrar estadísticas iniciales
show_stats

# Verificar si el log file existe
if [ ! -f "$LOG_FILE" ]; then
    echo "⚠️  Log file no encontrado: $LOG_FILE"
    echo "   Esperando a que se cree..."
    sleep 5
fi

# Monitoreo continuo
echo "📡 Monitoreando logs en tiempo real..."
echo "   Presiona Ctrl+C para detener el monitoreo y la ejecución"
echo "   (Se mostrarán estadísticas cada 30 segundos)"
echo ""

# Contador para estadísticas periódicas
STATS_COUNTER=0

# Monitorear logs
tail -f "$LOG_FILE" 2>/dev/null | while IFS= read -r line; do
    # Mostrar línea (solo mensaje si es JSON)
    if echo "$line" | grep -q '^{'; then
        # Es JSON, extraer solo el mensaje
        msg=$(parse_json_log "$line")
        if [ -n "$msg" ]; then
            echo "$msg"
        else
            echo "$line"
        fi
    else
        echo "$line"
    fi
    
    # Detectar errores críticos
    if echo "$line" | grep -qi "error crítico\|fatal\|critical error\|rate limit exceeded"; then
        echo ""
        echo "⚠️  ⚠️  ⚠️  ALERTA ⚠️  ⚠️  ⚠️"
        if echo "$line" | grep -qi "rate limit"; then
            echo "   Rate limit detectado - El sistema reintentará automáticamente"
        else
            echo "   ERROR CRÍTICO DETECTADO"
            echo "   Considera revisar los logs completos"
        fi
        echo ""
    fi
    
    # Mostrar estadísticas cada 30 líneas (~30 segundos)
    STATS_COUNTER=$((STATS_COUNTER + 1))
    if [ $STATS_COUNTER -ge 30 ]; then
        show_stats
        STATS_COUNTER=0
    fi
    
    # Detectar si se solicita detención
    if [ -f "$STOP_FILE" ]; then
        echo ""
        echo "🛑 Detención solicitada..."
        stop_processing
    fi
done

