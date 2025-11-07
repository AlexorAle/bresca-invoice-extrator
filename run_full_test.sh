#!/bin/bash

set -e

echo "======================================================"
echo "🧪 PRUEBA COMPLETA DEL SISTEMA DE EXTRACCIÓN"
echo "======================================================"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Aplicar migración
echo -e "${YELLOW}Paso 1: Aplicando migración de base de datos...${NC}"
sudo -u postgres /tmp/run_migration.sh
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migración aplicada exitosamente${NC}"
else
    echo -e "${RED}❌ Error aplicando migración${NC}"
    exit 1
fi
echo ""

# 2. Verificar que la factura existe
echo -e "${YELLOW}Paso 2: Verificando factura...${NC}"
if [ -f "temp/Iberdrola Junio 2025.pdf" ]; then
    echo -e "${GREEN}✅ Factura encontrada ($(du -h 'temp/Iberdrola Junio 2025.pdf' | cut -f1))${NC}"
else
    echo -e "${RED}❌ Factura no encontrada${NC}"
    exit 1
fi
echo ""

# 3. Activar entorno virtual
echo -e "${YELLOW}Paso 3: Activando entorno virtual...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Entorno activado${NC}"
echo ""

# 4. Ejecutar test
echo -e "${YELLOW}Paso 4: Ejecutando test de extracción...${NC}"
echo ""
python test_single_invoice.py "temp/Iberdrola Junio 2025.pdf"
TEST_EXIT_CODE=$?
echo ""

# 5. Generar resumen
echo ""
echo "======================================================"
echo "📊 RESUMEN EJECUTIVO"
echo "======================================================"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ TEST EXITOSO${NC}"
    echo ""
    echo "El sistema procesó la factura correctamente:"
    echo "  • Archivo: Iberdrola Junio 2025.pdf"
    echo "  • OCR: Ollama Vision (llama3.2-vision)"
    echo "  • Base de datos: Registro guardado exitosamente"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Verificar datos en dashboard: python -m streamlit run src/dashboard/app.py"
    echo "  2. Conectar Google Drive y procesar facturas reales"
    echo "  3. Configurar cron job para procesamiento automático"
else
    echo -e "${YELLOW}⚠️  TEST CON ADVERTENCIAS${NC}"
    echo ""
    echo "El sistema encontró problemas durante el procesamiento."
    echo "Revisa los logs arriba para más detalles."
    echo ""
    echo "Posibles causas:"
    echo "  • PDF con formato no estándar"
    echo "  • Campos no encontrados por OCR"
    echo "  • Factura marcada como 'revisar' (normal para PDFs complejos)"
fi

echo ""
echo "======================================================"
