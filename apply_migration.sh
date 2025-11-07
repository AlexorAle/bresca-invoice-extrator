#!/bin/bash
# Script para aplicar migración de detección de duplicados

echo "🔧 Aplicando migración del sistema de detección de duplicados..."
echo ""

# Intentar con sudo -u postgres (pedirá contraseña de sudo)
echo "Este script requiere permisos de postgres para modificar el esquema."
echo "Se te pedirá tu contraseña de sudo."
echo ""

sudo -u postgres psql -d negocio_db << 'EOFSQL'
-- Añadir índice único en hash_contenido
CREATE UNIQUE INDEX IF NOT EXISTS idx_facturas_hash_contenido_unique 
ON facturas (hash_contenido) 
WHERE hash_contenido IS NOT NULL;

-- Añadir columna revision
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'facturas' AND column_name = 'revision'
    ) THEN
        ALTER TABLE facturas ADD COLUMN revision INT DEFAULT 1;
    END IF;
END $$;

-- Añadir columna drive_modified_time
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'facturas' AND column_name = 'drive_modified_time'
    ) THEN
        ALTER TABLE facturas ADD COLUMN drive_modified_time TIMESTAMP;
    END IF;
END $$;

-- Actualizar constraint de estado
DO $$ 
BEGIN
    ALTER TABLE facturas DROP CONSTRAINT IF EXISTS check_estado_values;
    ALTER TABLE facturas ADD CONSTRAINT check_estado_values 
    CHECK (estado IN ('procesado', 'pendiente', 'error', 'revisar', 'duplicado'));
END $$;

-- Añadir índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_facturas_proveedor_numero 
ON facturas (proveedor_text, numero_factura) 
WHERE proveedor_text IS NOT NULL AND numero_factura IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_facturas_fecha_emision 
ON facturas (fecha_emision) 
WHERE fecha_emision IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_facturas_estado 
ON facturas (estado);

CREATE INDEX IF NOT EXISTS idx_facturas_drive_modified 
ON facturas (drive_modified_time);

-- Añadir campos en ingest_events
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ingest_events' AND column_name = 'hash_contenido'
    ) THEN
        ALTER TABLE ingest_events ADD COLUMN hash_contenido TEXT;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ingest_events' AND column_name = 'decision'
    ) THEN
        ALTER TABLE ingest_events ADD COLUMN decision TEXT;
    END IF;
END $$;

-- Crear vista para análisis de duplicados
CREATE OR REPLACE VIEW v_duplicate_analysis AS
SELECT 
    hash_contenido,
    COUNT(*) as num_ocurrencias,
    STRING_AGG(DISTINCT drive_file_id, ', ') as file_ids,
    STRING_AGG(DISTINCT drive_file_name, ', ') as file_names,
    MAX(creado_en) as ultima_ingesta,
    ARRAY_AGG(DISTINCT estado) as estados
FROM facturas
WHERE hash_contenido IS NOT NULL
GROUP BY hash_contenido
HAVING COUNT(*) > 1
ORDER BY num_ocurrencias DESC;

-- Crear función para obtener última fecha de ingesta
CREATE OR REPLACE FUNCTION get_last_ingest_timestamp()
RETURNS TIMESTAMP AS \$\$
BEGIN
    RETURN COALESCE(
        (SELECT MAX(drive_modified_time) FROM facturas WHERE drive_modified_time IS NOT NULL),
        '2000-01-01 00:00:00'::TIMESTAMP
    );
END;
\$\$ LANGUAGE plpgsql;

-- Otorgar permisos al usuario extractor_user
GRANT ALL PRIVILEGES ON TABLE facturas TO extractor_user;
GRANT ALL PRIVILEGES ON TABLE ingest_events TO extractor_user;
GRANT SELECT ON v_duplicate_analysis TO extractor_user;

SELECT '✅ Migración completada exitosamente' as status;
EOFSQL

echo ""
echo "✅ Migración aplicada correctamente"
echo "📊 Sistema de detección de duplicados activado"
