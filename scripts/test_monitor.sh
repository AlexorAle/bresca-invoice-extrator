#!/bin/bash
# Script de prueba para verificar que el monitoreo funciona

PROJECT_DIR="/home/alex/proyectos/invoice-extractor"
SCRIPT_PATH="$PROJECT_DIR/scripts/monitorear_drive.sh"

echo "🧪 Probando script de monitoreo de Drive..."
echo ""

cd "$PROJECT_DIR" || exit 1

# Activar venv si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Ejecutar el script de monitoreo
echo "Ejecutando: $SCRIPT_PATH"
echo ""

bash "$SCRIPT_PATH"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Script ejecutado correctamente"
else
    echo "❌ Script falló con código: $EXIT_CODE"
    echo "Revisa los logs para más detalles"
fi

exit $EXIT_CODE



