-- Migración: Añadir tabla costos_personal para gestión de costos de personal mensuales
-- Fecha: 2026-01-19
-- Autor: Arquitecto Senior Invoice Extractor

-- ============================================================================
-- CREAR TABLA costos_personal
-- ============================================================================

CREATE TABLE IF NOT EXISTS costos_personal (
    id SERIAL PRIMARY KEY,
    mes INTEGER NOT NULL,
    año INTEGER NOT NULL,
    sueldos_netos DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    coste_empresa DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    notas TEXT,
    creado_en TIMESTAMP DEFAULT NOW(),
    actualizado_en TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_costo_mes_range CHECK (mes >= 1 AND mes <= 12),
    CONSTRAINT check_costo_año_range CHECK (año >= 2000 AND año <= 2100),
    CONSTRAINT check_sueldos_netos_positive CHECK (sueldos_netos >= 0),
    CONSTRAINT check_coste_empresa_positive CHECK (coste_empresa >= 0),
    CONSTRAINT uq_costos_personal_mes_año UNIQUE (mes, año)
);

-- ============================================================================
-- CREAR ÍNDICES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_costos_personal_año ON costos_personal(año);
CREATE INDEX IF NOT EXISTS idx_costos_personal_mes_año ON costos_personal(mes, año);

-- ============================================================================
-- COMENTARIOS (Documentación)
-- ============================================================================

COMMENT ON TABLE costos_personal IS 'Costos de personal mensuales: sueldos netos y coste empresa (seguros sociales)';
COMMENT ON COLUMN costos_personal.mes IS 'Mes (1-12)';
COMMENT ON COLUMN costos_personal.año IS 'Año (2000-2100)';
COMMENT ON COLUMN costos_personal.sueldos_netos IS 'Total de sueldos netos pagados al personal en el mes';
COMMENT ON COLUMN costos_personal.coste_empresa IS 'Total coste empresa (seguros sociales, cotizaciones) del mes';
COMMENT ON COLUMN costos_personal.notas IS 'Notas opcionales (ej: "2 empleados", "bonus incluido", etc.)';

-- ============================================================================
-- DATOS DE EJEMPLO (OPCIONAL - comentado por defecto)
-- ============================================================================

-- Descomentar para cargar datos de ejemplo:
-- INSERT INTO costos_personal (mes, año, sueldos_netos, coste_empresa, notas) VALUES
-- (1, 2025, 2500.00, 800.00, 'Enero 2025 - 1 empleado'),
-- (2, 2025, 2500.00, 800.00, 'Febrero 2025 - 1 empleado'),
-- (3, 2025, 5000.00, 1600.00, 'Marzo 2025 - 2 empleados');

-- ============================================================================
-- ROLLBACK (Instrucciones para revertir)
-- ============================================================================

-- Para revertir esta migración, ejecutar:
-- DROP INDEX IF EXISTS idx_costos_personal_mes_año;
-- DROP INDEX IF EXISTS idx_costos_personal_año;
-- DROP TABLE IF EXISTS costos_personal;

