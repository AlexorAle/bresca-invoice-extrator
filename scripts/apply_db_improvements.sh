#!/bin/bash
# ============================================================================
# Script para aplicar mejoras de arquitectura de datos
# Fecha: 2025-11-07
# ============================================================================

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Mejoras de Arquitectura de Datos${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Cargar variables de entorno desde .env si existe
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Cargando variables de entorno desde .env...${NC}"
    # Cargar DATABASE_URL desde .env de forma segura
    # Usar source con un subshell para evitar problemas con caracteres especiales
    DATABASE_URL_LINE=$(grep "^DATABASE_URL=" "$ENV_FILE" | head -1)
    if [ -n "$DATABASE_URL_LINE" ]; then
        # Extraer valor después del =
        DATABASE_URL_VALUE="${DATABASE_URL_LINE#*=}"
        export DATABASE_URL="$DATABASE_URL_VALUE"
        echo -e "${GREEN}✓ Variables cargadas${NC}"
    else
        echo -e "${YELLOW}Advertencia: DATABASE_URL no encontrada en .env${NC}"
    fi
else
    echo -e "${YELLOW}Advertencia: Archivo .env no encontrado en $ENV_FILE${NC}"
fi

# Verificar que DATABASE_URL esté configurada
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL no está configurada${NC}"
    echo "Configura DATABASE_URL en .env o como variable de entorno"
    exit 1
fi

# Directorio de migraciones
MIGRATIONS_DIR="$(dirname "$0")/../migrations"
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo -e "${YELLOW}Base de datos: ${DB_NAME}${NC}"
echo -e "${YELLOW}Directorio de migraciones: ${MIGRATIONS_DIR}${NC}"
echo ""

# Confirmar antes de continuar
read -p "¿Deseas continuar con la aplicación de migraciones? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operación cancelada"
    exit 0
fi

# Backup antes de migrar
echo -e "${YELLOW}Creando backup de seguridad...${NC}"
BACKUP_FILE="data/backups/pre_migration_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p data/backups
pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null || {
    echo -e "${YELLOW}Advertencia: No se pudo crear backup automático${NC}"
    echo "Continúa manualmente si es necesario"
}
echo -e "${GREEN}✓ Backup creado: ${BACKUP_FILE}${NC}"
echo ""

# Aplicar migraciones en orden
echo -e "${YELLOW}Aplicando migraciones...${NC}"

# Migración 002: Normalización proveedor
if [ -f "${MIGRATIONS_DIR}/002_normalize_proveedor_phase1.sql" ]; then
    echo -e "${YELLOW}→ Aplicando migración 002 (Normalización proveedor)...${NC}"
    psql "$DATABASE_URL" -f "${MIGRATIONS_DIR}/002_normalize_proveedor_phase1.sql" && \
        echo -e "${GREEN}✓ Migración 002 completada${NC}" || {
        echo -e "${RED}✗ Error en migración 002${NC}"
        exit 1
    }
else
    echo -e "${RED}✗ Archivo de migración 002 no encontrado${NC}"
    exit 1
fi

# Migración 003: Optimización de índices
if [ -f "${MIGRATIONS_DIR}/003_optimize_indexes.sql" ]; then
    echo -e "${YELLOW}→ Aplicando migración 003 (Optimización índices)...${NC}"
    psql "$DATABASE_URL" -f "${MIGRATIONS_DIR}/003_optimize_indexes.sql" && \
        echo -e "${GREEN}✓ Migración 003 completada${NC}" || {
        echo -e "${RED}✗ Error en migración 003${NC}"
        exit 1
    }
else
    echo -e "${RED}✗ Archivo de migración 003 no encontrado${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Todas las migraciones aplicadas${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "1. Reiniciar el backend para aplicar cambios en código (pool de conexiones)"
echo "2. Verificar que las consultas funcionen correctamente"
echo "3. Monitorear logs para detectar posibles problemas"
echo ""
echo -e "${YELLOW}Backup disponible en: ${BACKUP_FILE}${NC}"

