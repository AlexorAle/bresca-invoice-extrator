#!/bin/bash
# Script para aplicar la migración de categorías
# Fecha: 2025-12-11

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Aplicando migración de categorías ===${NC}"

# Cargar DATABASE_URL desde .env
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}ERROR: Archivo .env no encontrado${NC}"
    exit 1
fi

# Cargar DATABASE_URL desde .env de forma segura
DATABASE_URL_LINE=$(grep "^DATABASE_URL=" "$ENV_FILE" | head -1)
if [ -n "$DATABASE_URL_LINE" ]; then
    DATABASE_URL_VALUE="${DATABASE_URL_LINE#*=}"
    export DATABASE_URL="$DATABASE_URL_VALUE"
    echo -e "${GREEN}✓${NC} DATABASE_URL cargado"
else
    echo -e "${YELLOW}Advertencia: DATABASE_URL no encontrada en .env${NC}"
    echo "Configura DATABASE_URL en .env o como variable de entorno"
    exit 1
fi

# Verificar que DATABASE_URL esté configurada
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL no está configurada${NC}"
    echo "Configura DATABASE_URL en .env o como variable de entorno"
    exit 1
fi

# Aplicar migración
MIGRATION_FILE="migrations/004_create_categorias_table.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}ERROR: Archivo de migración no encontrado: $MIGRATION_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Aplicando migración: $MIGRATION_FILE${NC}"

if psql "$DATABASE_URL" -f "$MIGRATION_FILE"; then
    echo -e "${GREEN}✓${NC} Migración aplicada correctamente"
    
    # Verificar que la tabla se creó
    echo -e "${YELLOW}Verificando tabla categorias...${NC}"
    COUNT=$(psql "$DATABASE_URL" -tAc "SELECT COUNT(*) FROM categorias;" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓${NC} Tabla categorias creada con $COUNT categorías"
    
    echo -e "${GREEN}=== Migración completada exitosamente ===${NC}"
else
    echo -e "${RED}ERROR: Fallo al aplicar la migración${NC}"
    exit 1
fi
