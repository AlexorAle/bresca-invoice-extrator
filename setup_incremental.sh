#!/bin/bash
# ============================================================================
# SETUP AUTOMÁTICO - Sistema de Ingesta Incremental
# ============================================================================
# Ejecutar con: bash setup_incremental.sh
#
# Este script hace TODO el setup automáticamente:
#   1. Aplica migración SQL
#   2. Configura variables en .env
#   3. Crea directorios
#   4. Valida setup
#   5. Ejecuta dry-run
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "================================================================================"
echo -e "${BLUE}  🚀 SETUP AUTOMÁTICO - Sistema de Ingesta Incremental${NC}"
echo "================================================================================"
echo ""

# ============================================================================
# Detectar y activar virtualenv
# ============================================================================

# Buscar virtualenv
VENV_PYTHON=""
if [ -f "venv/bin/python" ]; then
    VENV_PYTHON="venv/bin/python"
    echo -e "${GREEN}✓${NC} Virtualenv encontrado: venv/"
    PYTHON_CMD="venv/bin/python"
elif [ -f "venv/bin/python3" ]; then
    VENV_PYTHON="venv/bin/python3"
    echo -e "${GREEN}✓${NC} Virtualenv encontrado: venv/"
    PYTHON_CMD="venv/bin/python3"
elif command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  No se encontró virtualenv, usando Python del sistema${NC}"
    echo "Recomendación: crear virtualenv con: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    PYTHON_CMD="python3"
else
    echo -e "${RED}❌ ERROR: No se encontró Python 3${NC}"
    echo "Instalar con: sudo apt install python3"
    exit 1
fi

# Verificar dependencias críticas
echo "Verificando dependencias..."
if ! $PYTHON_CMD -c "import dotenv" 2>/dev/null; then
    echo -e "${RED}❌ ERROR: Dependencias no instaladas${NC}"
    echo ""
    echo "Por favor, instalar dependencias primero:"
    echo ""
    if [ -n "$VENV_PYTHON" ]; then
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
    else
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
    fi
    echo ""
    echo "Luego ejecutar de nuevo: bash setup_incremental.sh"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python con dependencias: $PYTHON_CMD"
echo ""

# ============================================================================
# PASO 1: Aplicar Migración
# ============================================================================
echo "================================================================================"
echo -e "${YELLOW}PASO 1/5: Aplicar migración SQL${NC}"
echo "================================================================================"
echo ""

if [ ! -f .env ]; then
    echo -e "${RED}❌ ERROR: Archivo .env no encontrado${NC}"
    echo "Crear archivo .env con DATABASE_URL antes de continuar"
    exit 1
fi

# Cargar DATABASE_URL
export $(grep -v '^#' .env | grep DATABASE_URL | xargs)

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL no configurado en .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} DATABASE_URL cargado"

# Verificar si ya existe la tabla
TABLA_EXISTE=$(psql "$DATABASE_URL" -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'sync_state');" 2>/dev/null || echo "false")

if [ "$TABLA_EXISTE" = "t" ]; then
    echo -e "${YELLOW}⚠️  Tabla sync_state ya existe (migración ya aplicada)${NC}"
    echo "Saltando migración..."
else
    echo "Aplicando migración..."
    if psql "$DATABASE_URL" -f migrations/001_add_sync_state_table.sql > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Migración aplicada exitosamente"
    else
        echo -e "${RED}❌ ERROR al aplicar migración${NC}"
        exit 1
    fi
fi

echo ""

# ============================================================================
# PASO 2: Configurar Variables de Entorno
# ============================================================================
echo "================================================================================"
echo -e "${YELLOW}PASO 2/5: Configurar variables en .env${NC}"
echo "================================================================================"
echo ""

# Verificar si ya existen las variables
if grep -q "SYNC_WINDOW_MINUTES" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Variables de ingesta incremental ya configuradas en .env${NC}"
    echo "Saltando configuración..."
else
    echo "Agregando variables de ingesta incremental a .env..."
    
    cat >> .env << 'EOF'

# ============================================================================
# INGESTA INCREMENTAL (agregado automáticamente por setup_incremental.sh)
# ============================================================================

# Control de ingesta
SYNC_WINDOW_MINUTES=1440
BATCH_SIZE=10
SLEEP_BETWEEN_BATCH_SEC=10
MAX_PAGES_PER_RUN=10
ADVANCE_STRATEGY=MAX_OK_TIME

# Estado
STATE_BACKEND=db

# Drive API
DRIVE_PAGE_SIZE=100
DRIVE_RETRY_MAX=5
DRIVE_RETRY_BASE_MS=500

# Directorios
QUARANTINE_DIR=data/quarantine
PENDING_DIR=data/pending

# Logging
LOG_LEVEL=INFO
LOG_JSON=true
EOF

    echo -e "${GREEN}✓${NC} Variables agregadas a .env"
fi

echo ""

# ============================================================================
# PASO 3: Crear Directorios
# ============================================================================
echo "================================================================================"
echo -e "${YELLOW}PASO 3/5: Crear directorios${NC}"
echo "================================================================================"
echo ""

mkdir -p data/quarantine data/pending state logs

echo -e "${GREEN}✓${NC} Directorios creados:"
echo "   - data/quarantine"
echo "   - data/pending"
echo "   - state"
echo "   - logs"
echo ""

# ============================================================================
# PASO 4: Validar Setup
# ============================================================================
echo "================================================================================"
echo -e "${YELLOW}PASO 4/5: Validar setup completo${NC}"
echo "================================================================================"
echo ""

echo "Ejecutando tests de validación..."
echo ""

if $PYTHON_CMD scripts/test_incremental_system.py; then
    echo ""
    echo -e "${GREEN}✓${NC} Todos los tests pasaron"
else
    echo ""
    echo -e "${YELLOW}⚠️  Algunos tests fallaron, pero continuando...${NC}"
    echo "Revisar logs arriba para detalles"
fi

echo ""

# ============================================================================
# PASO 5: Dry Run
# ============================================================================
echo "================================================================================"
echo -e "${YELLOW}PASO 5/5: Ejecutar dry-run (validación sin procesar)${NC}"
echo "================================================================================"
echo ""

echo "Ejecutando dry-run para verificar que todo funciona..."
echo ""

if $PYTHON_CMD scripts/run_ingest_incremental.py --dry-run; then
    echo ""
    echo -e "${GREEN}✓${NC} Dry-run completado exitosamente"
else
    echo ""
    echo -e "${RED}❌ Dry-run falló${NC}"
    echo "Revisar configuración en .env (especialmente GOOGLE_DRIVE_FOLDER_ID)"
    exit 1
fi

echo ""

# ============================================================================
# RESUMEN FINAL
# ============================================================================
echo "================================================================================"
echo -e "${GREEN}  ✅ SETUP COMPLETADO EXITOSAMENTE${NC}"
echo "================================================================================"
echo ""
echo "El sistema de ingesta incremental está listo para usar."
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo ""
echo "1. Ejecutar primera ingesta (manual):"
echo -e "   ${YELLOW}$PYTHON_CMD scripts/run_ingest_incremental.py${NC}"
echo ""
echo "2. Configurar cron para ejecución automática (cada 30 min):"
echo -e "   ${YELLOW}crontab -e${NC}"
echo ""
echo "   Agregar esta línea:"
echo "   */30 * * * * cd $(pwd) && $PYTHON_CMD scripts/run_ingest_incremental.py >> logs/cron.log 2>&1"
echo ""
echo "3. Monitorear logs:"
echo -e "   ${YELLOW}tail -f logs/extractor.log${NC}"
echo ""
echo -e "${BLUE}Documentación:${NC}"
echo "   - README_INCREMENTAL.md              (overview)"
echo "   - INCREMENTAL_SETUP_GUIDE.md         (guía completa)"
echo "   - QUICK_REFERENCE_INCREMENTAL.md     (comandos rápidos)"
echo ""
echo "================================================================================"
echo ""

