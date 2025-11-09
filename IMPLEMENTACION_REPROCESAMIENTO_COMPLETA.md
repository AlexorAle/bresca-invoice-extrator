# Implementación Completada: Sistema de Reprocesamiento Automático

**Fecha:** 9 de noviembre de 2025  
**Estado:** ✅ COMPLETADO

---

## RESUMEN EJECUTIVO

Se ha implementado exitosamente el sistema de reprocesamiento automático de facturas en estado "revisar". El sistema:

- ✅ Detecta automáticamente facturas en estado "revisar" de los últimos 30 días
- ✅ Las reprocesa en cada ejecución del job incremental
- ✅ Limita intentos (máximo 3) para evitar loops infinitos
- ✅ Prioriza facturas con errores conocidos (bugs)
- ✅ Incluye auditoría completa y modo dry-run
- ✅ Marca facturas que fallan 3 veces como "error_permanente"

---

## ARCHIVOS MODIFICADOS/CREADOS

### 1. Migración de Base de Datos
**Archivo:** `migrations/004_add_reprocess_fields.sql` (NUEVO)
- Agrega columnas: `reprocess_attempts`, `reprocessed_at`, `reprocess_reason`
- Agrega índice para búsquedas eficientes
- Actualiza constraint de estado para incluir `error_permanente`

### 2. Modelo de Datos
**Archivo:** `src/db/models.py`
- Agregados campos: `reprocess_attempts`, `reprocessed_at`, `reprocess_reason`
- Actualizado constraint de estado

### 3. Repositorio
**Archivo:** `src/db/repositories.py`
- Nuevo método: `get_facturas_para_reprocesar()` - Consulta facturas con priorización
- Nuevo método: `increment_reprocess_attempts()` - Incrementa contador y maneja límite

### 4. Cliente de Drive
**Archivo:** `src/drive_client.py`
- Nuevo método: `get_file_by_id()` - Obtiene metadata de archivo por ID

### 5. Pipeline Incremental
**Archivo:** `src/pipeline/ingest_incremental.py`
- Agregada configuración de reprocesamiento (variables de entorno)
- Nuevo método: `_reprocess_review_invoices()` - Lógica completa de reprocesamiento
- Integrado en método `run()` - Se ejecuta antes de procesar archivos nuevos
- Agregadas estadísticas de reprocesamiento

### 6. Validación
**Archivo:** `src/pipeline/validate.py`
- Actualizado para aceptar estado `error_permanente`

### 7. Documentación
**Archivo:** `README.md`
- Agregada documentación de variables de entorno de reprocesamiento

---

## FUNCIONALIDADES IMPLEMENTADAS

### ✅ Reprocesamiento Automático
- Se ejecuta automáticamente en cada run del job incremental
- Solo procesa facturas de últimos N días (configurable, default: 30)
- Límite de facturas por ejecución (configurable, default: 50)

### ✅ Priorización Inteligente
- Facturas con errores de bugs conocidos tienen alta prioridad:
  - "tipo inválido"
  - "formato inválido"
  - "parsing failed"
  - "Validación de negocio falló"
- Facturas con errores de datos faltantes tienen baja prioridad

### ✅ Límite de Intentos
- Máximo 3 intentos por factura (configurable)
- Después del máximo, cambia estado a `error_permanente`
- Evita loops infinitos con facturas legítimamente problemáticas

### ✅ Modo Dry-Run
- Variable `REPROCESS_REVIEW_DRY_RUN=true`
- Muestra qué facturas se reprocesarían sin procesarlas
- Útil para testing después de bugs

### ✅ Auditoría Completa
- Campos en BD: `reprocess_attempts`, `reprocessed_at`, `reprocess_reason`
- Eventos en `ingest_events`:
  - `reprocess_start`
  - `reprocess_attempt`
  - `reprocess_success`
  - `reprocess_permanent_error`
- Logging estructurado con detalles completos

### ✅ Estadísticas
- `invoices_reprocessed_total`: Total reprocesadas
- `invoices_reprocessed_success`: Exitosas
- `invoices_reprocessed_failed`: Fallidas
- `invoices_reprocessed_permanent_error`: Error permanente

---

## VARIABLES DE ENTORNO

```env
# Reprocesamiento automático de facturas en "revisar"
REPROCESS_REVIEW_ENABLED=true              # Habilitar (default: true)
REPROCESS_REVIEW_MAX_DAYS=30                # Últimos N días (default: 30)
REPROCESS_REVIEW_MAX_COUNT=50               # Máximo por ejecución (default: 50)
REPROCESS_REVIEW_MAX_ATTEMPTS=3             # Máximo intentos (default: 3)
REPROCESS_REVIEW_DRY_RUN=false              # Modo dry-run (default: false)
```

**Nota:** Todas las variables tienen valores por defecto sensatos, no es necesario configurarlas.

---

## PRÓXIMOS PASOS

### 1. Aplicar Migración de Base de Datos

```bash
# Opción 1: Desde línea de comandos
psql -d tu_base_de_datos -f migrations/004_add_reprocess_fields.sql

# Opción 2: Usar script de migración si existe
python migrations/apply_migration.py migrations/004_add_reprocess_fields.sql
```

### 2. Verificar Migración

```sql
-- Verificar que las columnas existen
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'facturas' 
AND column_name LIKE 'reprocess%';

-- Debe mostrar:
-- reprocess_attempts | integer
-- reprocessed_at | timestamp with time zone
-- reprocess_reason | text
```

### 3. Ejecutar Job Incremental

El siguiente run del job incremental (cron cada 6 horas) automáticamente:

1. Detectar las 73 facturas en estado "revisar"
2. Reprocesarlas (máximo 50 por ejecución)
3. Si pasan validación → estado cambia a "procesado"
4. Si fallan → incrementa contador
5. Si alcanzan 3 intentos → estado cambia a "error_permanente"

### 4. Monitorear Resultados

```bash
# Ver logs del reprocesamiento
tail -f logs/extractor.log | grep -i reprocess

# Ver estadísticas en JSON
cat logs/last_run_stats.json | jq '.invoices_reprocessed_*'
```

---

## CASOS DE USO

### Caso 1: Facturas Actuales (73 facturas)
- **Situación:** 73 facturas en "revisar" por bug de validación (ya corregido)
- **Resultado esperado:**
  - Primera ejecución: 50 facturas → estado "procesado"
  - Segunda ejecución: 23 facturas restantes → estado "procesado"
  - Total: 2 ejecuciones (12 horas)

### Caso 2: Nuevo Bug Detectado
- **Situación:** Bug en validación detectado y corregido
- **Resultado:** Job siguiente ejecución reprocesa automáticamente
- **Sin intervención manual requerida**

### Caso 3: Factura con Problema Real
- **Situación:** Factura en "revisar" por datos faltantes legítimos
- **Resultado:**
  - Intento 1: Falla → `reprocess_attempts = 1`
  - Intento 2: Falla → `reprocess_attempts = 2`
  - Intento 3: Falla → `reprocess_attempts = 3` → estado `error_permanente`
  - No se reprocesa más

---

## TESTING

### Modo Dry-Run (Recomendado Primero)

```bash
# Configurar dry-run
export REPROCESS_REVIEW_DRY_RUN=true

# Ejecutar job
python scripts/run_ingest_incremental.py

# Verificar logs - debe mostrar facturas que se reprocesarían sin procesarlas
```

### Ejecución Real

```bash
# Desactivar dry-run
export REPROCESS_REVIEW_DRY_RUN=false

# Ejecutar job
python scripts/run_ingest_incremental.py

# Monitorear resultados
tail -f logs/extractor.log
```

---

## VERIFICACIÓN

### Verificar Facturas Reprocesadas

```sql
-- Facturas que fueron reprocesadas
SELECT 
    drive_file_name,
    estado,
    reprocess_attempts,
    reprocessed_at,
    reprocess_reason
FROM facturas
WHERE reprocess_attempts > 0
ORDER BY reprocessed_at DESC;
```

### Verificar Eventos de Auditoría

```sql
-- Eventos de reprocesamiento
SELECT 
    drive_file_id,
    etapa,
    nivel,
    detalle,
    ts
FROM ingest_events
WHERE etapa LIKE 'reprocess%'
ORDER BY ts DESC
LIMIT 20;
```

---

## NOTAS IMPORTANTES

1. **No requiere configuración:** Los valores por defecto son sensatos
2. **No afecta procesamiento normal:** Solo se ejecuta si está habilitado
3. **Seguro:** Límites previenen loops infinitos
4. **Auditable:** Trazabilidad completa en BD y logs
5. **Eficiente:** Prioriza facturas con bugs conocidos

---

## ESTADO FINAL

✅ **Implementación completa y lista para usar**

El sistema está listo para:
- Reprocesar automáticamente las 73 facturas actuales
- Manejar futuros bugs de validación
- Prevenir loops infinitos
- Proporcionar auditoría completa

**Siguiente acción:** Aplicar migración de BD y ejecutar job incremental.

