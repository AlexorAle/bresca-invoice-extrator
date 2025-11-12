# Instrucciones para Aplicar Índices Optimizados

**Problema:** Los índices funcionales requieren ser owner de la tabla `facturas`.

## Solución Rápida

Ejecuta la migración como superusuario de PostgreSQL:

```bash
# Opción 1: Como usuario postgres
sudo -u postgres psql negocio_db -f migrations/003_optimize_indexes.sql

# Opción 2: Si tienes acceso directo como postgres
psql -U postgres negocio_db -f migrations/003_optimize_indexes.sql
```

## Alternativa: Cambiar Owner de la Tabla

Si prefieres que `extractor_user` sea el owner:

```sql
-- Conectar como postgres
psql -U postgres negocio_db

-- Cambiar owner
ALTER TABLE facturas OWNER TO extractor_user;
ALTER TABLE proveedores OWNER TO extractor_user;

-- Luego ejecutar migración como extractor_user
\q
psql $DATABASE_URL -f migrations/003_optimize_indexes.sql
```

## Verificar Índices Creados

```sql
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'facturas' 
    AND indexname IN (
        'idx_facturas_fecha_coalesce',
        'idx_facturas_mes_proveedor',
        'idx_facturas_dia_mes',
        'idx_facturas_proveedor_fecha'
    );
```

## Si No Puedes Aplicar los Índices Ahora

Los índices son **opcionales** para el funcionamiento básico. El sistema funcionará sin ellos, solo las consultas serán un poco más lentas. Puedes aplicarlos más tarde cuando tengas acceso de superusuario.

**Estado actual:**
- ✅ Migración 002 (normalización proveedor) - **COMPLETADA**
- ⏳ Migración 003 (índices) - **PENDIENTE** (requiere permisos de superusuario)

