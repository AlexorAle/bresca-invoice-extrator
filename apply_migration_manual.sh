#!/bin/bash

# Este script debe ejecutarse CON SUDO
# Uso: sudo ./apply_migration_manual.sh

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Este script debe ejecutarse con sudo"
    echo "Uso: sudo ./apply_migration_manual.sh"
    exit 1
fi

echo "🔄 Aplicando migración de base de datos..."
su - postgres -c "psql -d negocio_db -f /home/alex/proyectos/invoice-extractor/migration_allow_null_importe.sql"

if [ $? -eq 0 ]; then
    echo "✅ Migración aplicada exitosamente"
else
    echo "❌ Error aplicando migración"
    exit 1
fi
