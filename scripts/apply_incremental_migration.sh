#!/bin/bash
# Script para aplicar la migración de sync_state
# Uso: ./scripts/apply_incremental_migration.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  MIGRACIÓN: sync_state table"
echo "=========================================="
echo ""

# Verificar que existe .env
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: Archivo .env no encontrado${NC}"
    echo "Crear archivo .env con DATABASE_URL configurado"
    exit 1
fi

# Cargar DATABASE_URL desde .env
export $(grep -v '^#' .env | grep DATABASE_URL | xargs)

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL no configurado en .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} DATABASE_URL cargado"
echo ""

# Verificar que existe el archivo de migración
MIGRATION_FILE="migrations/001_add_sync_state_table.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}ERROR: Archivo de migración no encontrado: $MIGRATION_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Archivo de migración encontrado: $MIGRATION_FILE"
echo ""

# Preguntar confirmación
echo -e "${YELLOW}¿Desea aplicar la migración ahora? (s/n)${NC}"
read -r response

if [[ ! "$response" =~ ^[Ss]$ ]]; then
    echo "Migración cancelada"
    exit 0
fi

echo ""
echo "Aplicando migración..."
echo ""

# Aplicar migración con psql
if psql "$DATABASE_URL" -f "$MIGRATION_FILE"; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  ✓ MIGRACIÓN APLICADA EXITOSAMENTE"
    echo "==========================================${NC}"
    echo ""
    
    # Verificar tabla creada
    echo "Verificando tabla sync_state..."
    psql "$DATABASE_URL" -c "SELECT COUNT(*) as registros FROM sync_state;"
    
    echo ""
    echo -e "${GREEN}✓${NC} Sistema incremental listo para usar"
    echo ""
else
    echo ""
    echo -e "${RED}=========================================="
    echo "  ✗ ERROR AL APLICAR MIGRACIÓN"
    echo "==========================================${NC}"
    echo ""
    exit 1
fi

