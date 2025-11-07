#!/bin/bash
# Script para configurar el cron job de monitoreo de Drive

PROJECT_DIR="/home/alex/proyectos/invoice-extractor"
SCRIPT_PATH="$PROJECT_DIR/scripts/monitorear_drive.sh"
LOG_DIR="$PROJECT_DIR/logs"
CRON_LOG="$LOG_DIR/cron-monitor.log"

echo "🔧 Configurando cron job para monitoreo diario de Google Drive..."
echo ""

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

# Verificar que el script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: No se encuentra el script $SCRIPT_PATH"
    exit 1
fi

# Hacer el script ejecutable
chmod +x "$SCRIPT_PATH"

# Crear entrada de cron
# Ejecutar cada 6 horas (00:00, 06:00, 12:00, 18:00)
CRON_ENTRY="0 */6 * * * $SCRIPT_PATH >> $CRON_LOG 2>&1"

# Verificar si ya existe una entrada de cron
if crontab -l 2>/dev/null | grep -q "monitorear_drive.sh"; then
    echo "⚠️  Ya existe una entrada de cron para monitorear_drive.sh"
    echo ""
    echo "Entrada actual:"
    crontab -l 2>/dev/null | grep "monitorear_drive.sh"
    echo ""
    read -p "¿Deseas reemplazarla? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        # Eliminar entrada antigua
        crontab -l 2>/dev/null | grep -v "monitorear_drive.sh" | crontab -
        # Agregar nueva entrada
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
        echo "✅ Entrada de cron actualizada"
    else
        echo "ℹ️  Manteniendo entrada existente"
        exit 0
    fi
else
    # Agregar nueva entrada
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Entrada de cron agregada"
fi

echo ""
echo "📋 Configuración de cron:"
echo "   Frecuencia: Cada 6 horas (00:00, 06:00, 12:00, 18:00)"
echo "   Script: $SCRIPT_PATH"
echo "   Log: $CRON_LOG"
echo ""
echo "Para ver los cron jobs configurados:"
echo "   crontab -l"
echo ""
echo "Para editar manualmente:"
echo "   crontab -e"
echo ""
echo "Para ver los logs:"
echo "   tail -f $CRON_LOG"

