-- Migración 004: Agregar campos para reprocesamiento automático de facturas
-- Fecha: 2025-11-09
-- Descripción: Agrega campos para rastrear intentos de reprocesamiento y auditoría

-- Agregar columnas para reprocesamiento
ALTER TABLE facturas
ADD COLUMN IF NOT EXISTS reprocess_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS reprocessed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS reprocess_reason TEXT;

-- Agregar constraint para reprocess_attempts
ALTER TABLE facturas
ADD CONSTRAINT check_reprocess_attempts_positive 
CHECK (reprocess_attempts >= 0);

-- Agregar índice para búsquedas eficientes de facturas a reprocesar
CREATE INDEX IF NOT EXISTS idx_facturas_reprocess 
ON facturas (estado, reprocess_attempts, actualizado_en DESC)
WHERE estado = 'revisar';

-- Actualizar constraint de estado para incluir 'error_permanente'
ALTER TABLE facturas
DROP CONSTRAINT IF EXISTS check_estado_values;

ALTER TABLE facturas
ADD CONSTRAINT check_estado_values 
CHECK (estado IN ('procesado', 'pendiente', 'error', 'revisar', 'duplicado', 'error_permanente'));

-- Comentarios para documentación
COMMENT ON COLUMN facturas.reprocess_attempts IS 'Número de intentos de reprocesamiento realizados';
COMMENT ON COLUMN facturas.reprocessed_at IS 'Timestamp del último intento de reprocesamiento';
COMMENT ON COLUMN facturas.reprocess_reason IS 'Razón del último reprocesamiento';

