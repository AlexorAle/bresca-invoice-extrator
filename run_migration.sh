#!/bin/bash

# Script para ejecutar la migración de base de datos
# Uso: ./run_migration.sh

echo "🔄 Aplicando migración de base de datos..."

cd "$(dirname "$0")"

sudo -u postgres psql -d negocio_db << EOF
-- Agregar columna si no existe
DO \$\$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'facturas' AND column_name = 'drive_modified_time'
    ) THEN
        ALTER TABLE facturas ADD COLUMN drive_modified_time TIMESTAMP;
        RAISE NOTICE 'Columna drive_modified_time agregada exitosamente';
    ELSE
        RAISE NOTICE 'Columna drive_modified_time ya existe';
    END IF;
END \$\$;

-- Crear índice si no existe
CREATE INDEX IF NOT EXISTS idx_facturas_drive_modified ON facturas (drive_modified_time);
EOF

if [ $? -eq 0 ]; then
    echo "✅ Migración completada exitosamente"
else
    echo "❌ Error en la migración"
    exit 1
fi

