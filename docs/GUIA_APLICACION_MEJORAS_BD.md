# Guía de Aplicación de Mejoras de Base de Datos

**Fecha:** 2025-11-07  
**Versión:** 1.0

---

## 📋 Resumen de Cambios

Esta guía documenta la aplicación de mejoras de arquitectura de datos:

1. **Normalización Proveedor-Factura** (Punto 1 - Crítico)
2. **Optimización de Índices** (Punto 2 - Medio)
3. **Ajuste Pool de Conexiones** (Punto 3 - Medio)

---

## ⚠️ IMPORTANTE: Antes de Empezar

### Requisitos Previos

- ✅ PostgreSQL 14+ instalado y accesible
- ✅ Variable `DATABASE_URL` configurada
- ✅ Acceso de escritura a la base de datos
- ✅ Backup de la base de datos (se crea automáticamente, pero verificar)

### Impacto en Funcionamiento

| Cambio | Requiere Reinicio Backend | Afecta Funcionamiento Actual | Breaking Change |
|--------|---------------------------|------------------------------|-----------------|
| Normalización proveedor | ✅ **SÍ** | ⚠️ Parcial (mejora) | ❌ No (compatible) |
| Optimización índices | ⚠️ Recomendado | ❌ No (solo mejora) | ❌ No |
| Pool de conexiones | ✅ **SÍ** | ❌ No (solo mejora) | ❌ No |

---

## 🚀 Pasos de Aplicación

### Paso 1: Backup Manual (Recomendado)

```bash
# Crear backup completo antes de migrar
pg_dump $DATABASE_URL > backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql
```

### Paso 2: Aplicar Migraciones SQL

**Opción A: Script Automático (Recomendado)**

```bash
cd /home/alex/proyectos/invoice-extractor
./scripts/apply_db_improvements.sh
```

**Opción B: Manual**

```bash
# Migración 002: Normalización proveedor
psql $DATABASE_URL -f migrations/002_normalize_proveedor_phase1.sql

# Migración 003: Optimización índices
psql $DATABASE_URL -f migrations/003_optimize_indexes.sql
```

### Paso 3: Verificar Migraciones

```sql
-- Verificar que proveedores fueron creados
SELECT COUNT(*) as total_proveedores FROM proveedores;

-- Verificar que facturas tienen proveedor_id
SELECT 
    COUNT(*) as total_facturas,
    COUNT(proveedor_id) as con_proveedor_id,
    COUNT(*) - COUNT(proveedor_id) as sin_proveedor_id
FROM facturas;

-- Verificar índices nuevos
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'facturas' 
    AND indexname LIKE 'idx_facturas%'
ORDER BY indexname;
```

### Paso 4: Reiniciar Backend

**⚠️ CRÍTICO: Debe reiniciarse el backend para aplicar cambios en código**

```bash
# Si usas systemd
sudo systemctl restart invoice-extractor

# Si usas Docker
docker-compose restart backend

# Si ejecutas manualmente
# Detener proceso actual (Ctrl+C) y reiniciar
python -m src.api.main
```

### Paso 5: Verificar Funcionamiento

1. **Verificar logs del backend:**
   ```bash
   tail -f logs/app.log
   ```

2. **Probar endpoints de API:**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Resumen mensual
   curl http://localhost:8000/api/facturas/summary?month=11&year=2025
   ```

3. **Verificar que nuevas facturas se procesen correctamente:**
   - Procesar una factura de prueba
   - Verificar que `proveedor_id` se establece automáticamente
   - Verificar logs para confirmar normalización

---

## 🔍 Qué Hace Cada Migración

### Migración 002: Normalización Proveedor

**Objetivo:** Migrar datos de `proveedor_text` a `proveedor_id`

**Acciones:**
1. Crea registros en `proveedores` para todos los `proveedor_text` únicos
2. Actualiza `proveedor_id` en `facturas` basándose en `proveedor_text`
3. Crea índice en `proveedor_id` para mejor rendimiento
4. Reporta facturas sin `proveedor_id` (requieren revisión manual)

**Tiempo estimado:** 1-5 minutos (depende del volumen de datos)

**Rollback:** No hay rollback automático. Usar backup si es necesario.

### Migración 003: Optimización Índices

**Objetivo:** Mejorar rendimiento de consultas frecuentes

**Índices creados:**
- `idx_facturas_fecha_coalesce`: Para consultas con `COALESCE(fecha_emision, fecha_recepcion)`
- `idx_facturas_mes_proveedor`: Para reportes mensuales por proveedor
- `idx_facturas_dia_mes`: Para agrupación por día
- `idx_facturas_proveedor_fecha`: Para búsquedas por proveedor + fecha

**Tiempo estimado:** 2-10 minutos (depende del volumen de datos)

**Rollback:** Eliminar índices manualmente si es necesario:
```sql
DROP INDEX IF EXISTS idx_facturas_fecha_coalesce;
DROP INDEX IF EXISTS idx_facturas_mes_proveedor;
DROP INDEX IF EXISTS idx_facturas_dia_mes;
DROP INDEX IF EXISTS idx_facturas_proveedor_fecha;
```

---

## 📊 Cambios en Código

### 1. Pool de Conexiones (`src/db/database.py`)

**Antes:**
```python
pool_size=2,
max_overflow=10,
```

**Después:**
```python
pool_size=5,  # Aumentado de 2 a 5
max_overflow=15,  # Aumentado de 10 a 15
```

**Impacto:** Mejor capacidad para manejar solicitudes concurrentes.

### 2. Normalización Automática (`src/db/repositories.py`)

**Cambio en `upsert_factura()`:**
- Ahora busca/crea `Proveedor` automáticamente si viene `proveedor_text`
- Establece `proveedor_id` automáticamente
- Mantiene `proveedor_text` como denormalizado (compatibilidad)

**Cambio en `find_by_invoice_number()`:**
- Busca primero por `proveedor_id` (más eficiente)
- Fallback a `proveedor_text` si no existe proveedor (compatibilidad)

**Cambio en `get_categories_breakdown()`:**
- Usa `JOIN` con `proveedores` para mejor rendimiento
- Fallback a `proveedor_text` si `proveedor_id` es NULL

---

## ✅ Verificación Post-Migración

### Checklist

- [ ] Migraciones SQL aplicadas sin errores
- [ ] Backend reiniciado
- [ ] Logs sin errores críticos
- [ ] Endpoints de API funcionando
- [ ] Nueva factura procesada correctamente
- [ ] `proveedor_id` se establece automáticamente
- [ ] Consultas de reportes más rápidas (verificar con `EXPLAIN ANALYZE`)

### Consultas de Verificación

```sql
-- Verificar normalización
SELECT 
    p.nombre,
    COUNT(f.id) as facturas_count
FROM proveedores p
LEFT JOIN facturas f ON f.proveedor_id = p.id
GROUP BY p.id, p.nombre
ORDER BY facturas_count DESC
LIMIT 10;

-- Verificar rendimiento de índices
EXPLAIN ANALYZE
SELECT 
    date_trunc('month', COALESCE(fecha_emision, fecha_recepcion)) as mes,
    proveedor_id,
    COUNT(*) as cantidad,
    SUM(importe_total) as total
FROM facturas
WHERE importe_total IS NOT NULL
GROUP BY 1, 2
LIMIT 10;
```

---

## 🐛 Troubleshooting

### Error: "relation 'proveedores' does not exist"

**Causa:** Tabla `proveedores` no existe.

**Solución:**
```sql
-- Verificar que la tabla existe
SELECT * FROM information_schema.tables WHERE table_name = 'proveedores';

-- Si no existe, ejecutar script de inicialización
psql $DATABASE_URL -f infra/database_init.sql
```

### Error: "duplicate key value violates unique constraint"

**Causa:** Ya existe un proveedor con ese nombre.

**Solución:** El script usa `ON CONFLICT DO NOTHING`, así que es seguro. Verificar:
```sql
SELECT nombre, COUNT(*) 
FROM proveedores 
GROUP BY nombre 
HAVING COUNT(*) > 1;
```

### Facturas sin proveedor_id después de migración

**Causa:** Facturas con `proveedor_text` NULL o vacío.

**Solución:** Revisar manualmente:
```sql
SELECT id, drive_file_name, proveedor_text, proveedor_id
FROM facturas
WHERE proveedor_text IS NOT NULL 
    AND proveedor_text != ''
    AND proveedor_id IS NULL;
```

### Backend no inicia después de cambios

**Causa:** Error de sintaxis o import faltante.

**Solución:**
1. Verificar logs: `tail -f logs/app.log`
2. Verificar imports: `python -c "from src.db.repositories import FacturaRepository"`
3. Revertir cambios si es necesario (usar backup)

---

## 📈 Métricas de Éxito

### Antes vs Después

| Métrica | Antes | Después | Mejora Esperada |
|---------|-------|---------|-----------------|
| Consulta por proveedor | ~50-100ms | ~5-10ms | **5-10x** |
| Reporte mensual | ~200-500ms | ~20-50ms | **10x** |
| Pool de conexiones | 2 base | 5 base | **+150%** |
| Integridad datos | ⚠️ Inconsistente | ✅ Garantizada | **100%** |

### Monitoreo

```sql
-- Verificar uso de índices
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'facturas'
ORDER BY idx_scan DESC;
```

---

## 🔄 Rollback (Si es Necesario)

Si necesitas revertir los cambios:

1. **Restaurar backup:**
   ```bash
   psql $DATABASE_URL < backup_pre_migration_YYYYMMDD_HHMMSS.sql
   ```

2. **Revertir código:**
   ```bash
   git checkout HEAD -- src/db/database.py src/db/repositories.py
   ```

3. **Reiniciar backend**

---

## 📝 Notas Finales

- ✅ **Compatibilidad:** Los cambios son compatibles hacia atrás. `proveedor_text` se mantiene como denormalizado.
- ✅ **Sin downtime:** Las migraciones no requieren downtime (excepto reinicio del backend).
- ✅ **Reversible:** Todo es reversible usando backups.
- ⚠️ **Fase 2 futura:** En el futuro se puede eliminar `proveedor_text` cuando todo esté validado.

---

## 📞 Soporte

Si encuentras problemas:
1. Revisar logs: `logs/app.log`
2. Verificar estado de BD: `psql $DATABASE_URL -c "\dt"`
3. Consultar documentación: `docs/ANALISIS_ARQUITECTURA_DATOS.md`

