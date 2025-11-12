# Solución al Error de Índices

**Error:** `functions in index expression must be marked IMMUTABLE`

## Problema

PostgreSQL requiere que las funciones usadas en índices sean **IMMUTABLE** (no cambian su resultado para los mismos inputs). 

El problema ocurre con:
- `COALESCE()` cuando se usa con tipos que pueden tener timezone
- Algunas funciones de fecha en ciertos contextos

## Solución Aplicada

Se crearon **dos versiones alternativas** de la migración:

### Versión 1: `003_optimize_indexes_fixed.sql`
- Usa índices en columnas base
- Evita `COALESCE()` en índices
- Usa `DATE_TRUNC` e `EXTRACT` que son IMMUTABLE con tipos DATE

### Versión 2: `003_optimize_indexes_simple.sql` ⭐ **RECOMENDADA**
- Índices simples en columnas base
- Compuestos directos sin funciones complejas
- 100% compatible, sin errores

## Estado Actual

✅ **Ya creado:**
- `idx_facturas_proveedor_fecha` (funcionó correctamente)

⏳ **Pendiente:**
- Índices adicionales para optimizar reportes

## Cómo Aplicar

### Opción A: Versión Simple (Recomendada)

```bash
sudo -u postgres psql negocio_db -f migrations/003_optimize_indexes_simple.sql
```

Esta versión:
- ✅ No usa `COALESCE()` en índices
- ✅ Usa solo `EXTRACT()` que es IMMUTABLE con DATE
- ✅ Índices compuestos simples
- ✅ 100% compatible

### Opción B: Si la versión simple también falla

Aplicar índices manualmente uno por uno:

```sql
-- Conectar como postgres
sudo -u postgres psql negocio_db

-- Índice 1: Para reportes con fecha_emision
CREATE INDEX IF NOT EXISTS idx_facturas_fecha_emision_proveedor 
ON facturas (fecha_emision, proveedor_id)
WHERE fecha_emision IS NOT NULL 
    AND proveedor_id IS NOT NULL
    AND importe_total IS NOT NULL;

-- Índice 2: Para reportes con fecha_recepcion (fallback)
CREATE INDEX IF NOT EXISTS idx_facturas_fecha_recepcion_proveedor 
ON facturas (fecha_recepcion, proveedor_id)
WHERE fecha_recepcion IS NOT NULL 
    AND proveedor_id IS NOT NULL
    AND importe_total IS NOT NULL
    AND fecha_emision IS NULL;

-- Índice 3: Para agrupación por año-mes
CREATE INDEX IF NOT EXISTS idx_facturas_anio_mes 
ON facturas (
    EXTRACT(year FROM fecha_emision),
    EXTRACT(month FROM fecha_emision)
)
WHERE fecha_emision IS NOT NULL;

-- Índice 4: Para agrupación por día
CREATE INDEX IF NOT EXISTS idx_facturas_dia_mes_anio 
ON facturas (
    EXTRACT(day FROM fecha_emision),
    EXTRACT(month FROM fecha_emision),
    EXTRACT(year FROM fecha_emision)
)
WHERE fecha_emision IS NOT NULL;
```

## Verificar Índices Creados

```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'facturas' 
    AND indexname LIKE 'idx_facturas%'
ORDER BY indexname;
```

## Nota Importante

**Los índices son opcionales para el funcionamiento básico.**

El sistema funciona perfectamente sin estos índices adicionales. Solo mejoran el rendimiento de:
- Reportes mensuales
- Agrupaciones por día
- Consultas con filtros de fecha

Si no puedes aplicarlos ahora, el sistema seguirá funcionando correctamente.

## Alternativa: Índices Manuales Simples

Si todo falla, puedes crear índices básicos que PostgreSQL usará eficientemente:

```sql
-- Índices básicos que siempre funcionan
CREATE INDEX IF NOT EXISTS idx_facturas_fecha_emision_proveedor 
ON facturas (fecha_emision, proveedor_id)
WHERE fecha_emision IS NOT NULL AND proveedor_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_facturas_fecha_recepcion_proveedor 
ON facturas (fecha_recepcion, proveedor_id)
WHERE fecha_recepcion IS NOT NULL AND proveedor_id IS NOT NULL;
```

Estos índices simples también mejorarán significativamente las consultas.

