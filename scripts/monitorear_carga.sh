#!/bin/bash
# Script de monitoreo para carga masiva de facturas
# Permite ver logs en tiempo real y detener ejecución si es necesario

LOG_FILE="/app/logs/extractor.log"
PID_FILE="/tmp/invoice_processor.pid"
STOP_FILE="/tmp/stop_processing.flag"

echo "=========================================="
echo "🔍 MONITOREO DE CARGA MASIVA"
echo "=========================================="
echo ""

# Función para verificar si el proceso está corriendo
check_process() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
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
    exit 0
}

# Trap para capturar Ctrl+C
trap stop_processing INT TERM

# Verificar si hay proceso corriendo
if check_process; then
    PID=$(cat "$PID_FILE")
    echo "✅ Proceso detectado (PID: $PID)"
    echo ""
else
    echo "⚠️  No se detectó proceso activo"
    echo "   (El proceso puede no haber iniciado o ya terminó)"
    echo ""
fi

# Mostrar estadísticas iniciales
echo "📊 Estadísticas iniciales:"
if [ -f "$LOG_FILE" ]; then
    TOTAL_PROCESSED=$(grep -c "Factura procesada exitosamente\|ingest_complete" "$LOG_FILE" 2>/dev/null || echo "0")
    TOTAL_ERRORS=$(grep -c "ERROR\|ingest_error" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "   Facturas procesadas: $TOTAL_PROCESSED"
    echo "   Errores: $TOTAL_ERRORS"
else
    echo "   Log file no encontrado aún"
fi
echo ""

# Monitoreo continuo
echo "📡 Monitoreando logs en tiempo real..."
echo "   Presiona Ctrl+C para detener el monitoreo y la ejecución"
echo ""

# Monitorear logs
tail -f "$LOG_FILE" 2>/dev/null | while IFS= read -r line; do
    # Mostrar línea
    echo "$line"
    
    # Detectar errores críticos
    if echo "$line" | grep -qi "error crítico\|fatal\|critical error"; then
        echo ""
        echo "⚠️  ERROR CRÍTICO DETECTADO"
        echo "   Considera detener la ejecución"
        echo ""
    fi
    
    # Detectar si se solicita detención
    if [ -f "$STOP_FILE" ]; then
        echo ""
        echo "🛑 Detención solicitada..."
        stop_processing
    fi
done

