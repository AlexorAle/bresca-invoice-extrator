#!/bin/bash
# Script para ejecutar el monitoreo inmediatamente (sin esperar al cron)

PROJECT_DIR="/home/alex/proyectos/invoice-extractor"
SCRIPT_PATH="$PROJECT_DIR/scripts/monitorear_drive.sh"

echo "🚀 Ejecutando monitoreo de Drive ahora (sin esperar al cron)..."
echo ""

cd "$PROJECT_DIR" || exit 1

# Ejecutar el script de monitoreo
bash "$SCRIPT_PATH"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Monitoreo completado exitosamente"
    echo ""
    echo "📋 Revisa los logs en:"
    echo "   tail -f $PROJECT_DIR/logs/monitoreo_drive.log"
else
    echo "❌ Monitoreo falló con código: $EXIT_CODE"
    echo ""
    echo "📋 Revisa los logs para más detalles:"
    echo "   tail -f $PROJECT_DIR/logs/monitoreo_drive.log"
fi

exit $EXIT_CODE



