# Plan de Implementación: Sistema de Reprocesamiento Automático de Facturas

**Fecha:** 9 de noviembre de 2025  
**Estado:** ⏳ Pendiente de aprobación

---

## RESUMEN EJECUTIVO

Implementar sistema de reprocesamiento automático que:
- Detecta facturas en estado "revisar" de últimos 30 días
- Las reprocesa automáticamente en cada ejecución del job
- Limita intentos (máximo 3) para evitar loops infinitos
- Prioriza facturas con errores conocidos (bugs)
- Incluye auditoría completa y modo dry-run

**Impacto:** Resuelve 73 facturas bloqueadas por bug de validación + prepara sistema para futuros bugs.

---

## PLAN DE IMPLEMENTACIÓN

### FASE 1: Migración de Base de Datos

#### 1.1 Crear migración SQL
- [ ] Crear archivo `migrations/004_add_reprocess_fields.sql`
- [ ] Agregar columna `reprocess_attempts INTEGER DEFAULT 0`
- [ ] Agregar columna `reprocessed_at TIMESTAMPTZ`
- [ ] Agregar columna `reprocess_reason TEXT`
- [ ] Agregar constraint: `reprocess_attempts >= 0`
- [ ] Agregar índice: `idx_facturas_reprocess` en `(estado, reprocess_attempts, actualizado_en)`

#### 1.2 Actualizar modelo SQLAlchemy
- [ ] Modificar `src/db/models.py` - clase `Factura`
- [ ] Agregar: `reprocess_attempts = Column(Integer, default=0)`
- [ ] Agregar: `reprocessed_at = Column(DateTime)`
- [ ] Agregar: `reprocess_reason = Column(Text)`
- [ ] Agregar constraint en `__table_args__`

#### 1.3 Aplicar migración
- [ ] Ejecutar script de migración
- [ ] Verificar que columnas existen en BD
- [ ] Verificar índices creados

---

### FASE 2: Extensión de Repositorio

#### 2.1 Nuevo método en FacturaRepository
- [ ] Crear método `get_facturas_para_reprocesar()` en `src/db/repositories.py`
- [ ] Parámetros: `estado='revisar'`, `max_dias=30`, `limite=50`, `max_attempts=3`
- [ ] Query: facturas en estado, últimos N días, `reprocess_attempts < max_attempts`
- [ ] Ordenar por: `error_msg` (priorizar patrones conocidos), luego `actualizado_en DESC`
- [ ] Retornar: lista de dicts con `drive_file_id`, `drive_file_name`, metadata necesaria

#### 2.2 Método de actualización de contador
- [ ] Crear método `increment_reprocess_attempts()` en `FacturaRepository`
- [ ] Actualizar: `reprocess_attempts += 1`, `reprocessed_at = now()`, `reprocess_reason`
- [ ] Si `reprocess_attempts >= max_attempts`: cambiar estado a `error_permanente`

---

### FASE 3: Extensión de DriveClient

#### 3.1 Método para obtener archivo por ID
- [ ] Crear método `get_file_by_id()` en `src/drive_client.py`
- [ ] Usar Drive API: `files().get(fileId=file_id).execute()`
- [ ] Retornar formato compatible con `process_batch()`:
  - `id`: drive_file_id
  - `name`: nombre archivo
  - `modifiedTime`: timestamp
  - `size`: tamaño
  - `folder_name`: obtener de parents (opcional, puede ser None)

#### 3.2 Método helper para descargar factura existente
- [ ] Crear método `download_file_for_reprocess()` en `DriveClient`
- [ ] Wrapper de `download_file()` con metadata adicional
- [ ] Agregar `folder_name` si se puede obtener de metadata

---

### FASE 4: Lógica de Reprocesamiento

#### 4.1 Función de reprocesamiento
- [ ] Crear función `reprocess_review_invoices()` en `src/pipeline/ingest_incremental.py`
- [ ] Parámetros: `db`, `drive_client`, `extractor`, `config`
- [ ] Lógica:
  1. Consultar facturas para reprocesar (usar método de repositorio)
  2. Si modo dry-run: solo log, no procesar
  3. Para cada factura:
     - Descargar desde Drive
     - Preparar `file_info` compatible con `process_batch()`
     - Llamar `process_batch()` con lista de 1 archivo
     - Si falla: incrementar contador
     - Si pasa: resetear contador (estado cambia a "procesado")
  4. Registrar estadísticas

#### 4.2 Priorización por error_msg
- [ ] Crear función helper `_prioritize_by_error()` en `reprocess_reprocess_review_invoices()`
- [ ] Patrones de alta prioridad (bugs conocidos):
  - "tipo inválido"
  - "formato inválido"
  - "parsing failed"
  - "Validación de negocio falló" (genérico)
- [ ] Patrones de baja prioridad (datos faltantes):
  - "Campo obligatorio faltante"
  - "proveedor_text es obligatorio"
- [ ] Ordenar lista: alta prioridad primero

#### 4.3 Manejo de límite de intentos
- [ ] En `reprocess_review_invoices()`:
  - Antes de reprocesar: verificar `reprocess_attempts < max_attempts`
  - Después de fallar: llamar `increment_reprocess_attempts()`
  - Si `reprocess_attempts >= max_attempts`: cambiar estado a `error_permanente`
  - Si pasa validación: resetear `reprocess_attempts = 0` (implícito al cambiar estado)

---

### FASE 5: Integración en Job Incremental

#### 5.1 Modificar IncrementalIngestPipeline
- [ ] Modificar `src/pipeline/ingest_incremental.py` - clase `IncrementalIngestPipeline`
- [ ] Agregar método `_reprocess_review_invoices()` (llama función de Fase 4)
- [ ] Modificar `run()` para incluir reprocesamiento:
  - Opción A: Antes de procesar archivos nuevos
  - Opción B: Después de procesar archivos nuevos
  - **Recomendación:** Opción A (reprocesar primero, luego nuevos)

#### 5.2 Configuración
- [ ] Agregar variables de entorno en `.env.example`:
  - `REPROCESS_REVIEW_ENABLED=true`
  - `REPROCESS_REVIEW_MAX_DAYS=30`
  - `REPROCESS_REVIEW_MAX_COUNT=50`
  - `REPROCESS_REVIEW_MAX_ATTEMPTS=3`
  - `REPROCESS_REVIEW_DRY_RUN=false`
- [ ] Leer configuración en `__init__()` de `IncrementalIngestPipeline`

#### 5.3 Estadísticas
- [ ] Agregar contadores en `IncrementalIngestStats`:
  - `invoices_reprocessed_total`
  - `invoices_reprocessed_success`
  - `invoices_reprocessed_failed`
  - `invoices_reprocessed_permanent_error`
- [ ] Incluir en log final y JSON de estadísticas

---

### FASE 6: Auditoría y Logging

#### 6.1 Eventos de auditoría
- [ ] Modificar `EventRepository.insert_event()` si es necesario
- [ ] Agregar eventos específicos:
  - `reprocess_start`: Inicio de reprocesamiento
  - `reprocess_attempt`: Intento de reprocesamiento
  - `reprocess_success`: Reprocesamiento exitoso
  - `reprocess_permanent_error`: Máximo de intentos alcanzado

#### 6.2 Logging estructurado
- [ ] Agregar logs en `reprocess_review_invoices()`:
  - INFO: Facturas encontradas para reprocesar
  - INFO: Factura siendo reprocesada (drive_file_id, attempt)
  - INFO: Reprocesamiento exitoso
  - WARNING: Reprocesamiento falló (attempt, reason)
  - ERROR: Máximo de intentos alcanzado

---

### FASE 7: Modo Dry-Run

#### 7.1 Implementar dry-run
- [ ] En `reprocess_review_invoices()`:
  - Si `REPROCESS_REVIEW_DRY_RUN=true`:
    - Consultar facturas (igual)
    - Log: "DRY-RUN: Reprocesaría X facturas"
    - Para cada factura: log detalle sin procesar
    - NO descargar PDFs
    - NO llamar `process_batch()`
    - NO actualizar BD
    - Retornar estadísticas simuladas

#### 7.2 Validación de dry-run
- [ ] Verificar que no se modifica BD en dry-run
- [ ] Verificar que logs son claros sobre modo dry-run

---

### FASE 8: Manejo de Estado "error_permanente"

#### 8.1 Agregar nuevo estado
- [ ] Modificar `src/db/models.py`:
  - Actualizar constraint: `estado IN ('procesado', 'pendiente', 'error', 'revisar', 'duplicado', 'error_permanente')`
- [ ] Modificar `src/pipeline/validate.py`:
  - Agregar 'error_permanente' a validación de estado

#### 8.2 Excluir de reprocesamiento
- [ ] En `get_facturas_para_reprocesar()`:
  - Filtrar: `estado = 'revisar' AND estado != 'error_permanente'`
  - Implícito si solo buscamos 'revisar', pero documentar

---

### FASE 9: Testing y Validación

#### 9.1 Testing unitario
- [ ] Test: `get_facturas_para_reprocesar()` retorna facturas correctas
- [ ] Test: `increment_reprocess_attempts()` actualiza contador
- [ ] Test: Cambio a `error_permanente` cuando alcanza máximo
- [ ] Test: Priorización por error_msg funciona

#### 9.2 Testing de integración
- [ ] Test: Reprocesamiento completo de 1 factura (dry-run)
- [ ] Test: Reprocesamiento completo de 1 factura (real)
- [ ] Test: Límite de intentos funciona
- [ ] Test: Integración en job incremental

#### 9.3 Validación manual
- [ ] Ejecutar dry-run y verificar logs
- [ ] Ejecutar reprocesamiento real de 1-2 facturas
- [ ] Verificar que contadores se actualizan
- [ ] Verificar que estado cambia correctamente

---

### FASE 10: Documentación

#### 10.1 Documentación técnica
- [ ] Actualizar `docs/implementation.md` con sección de reprocesamiento
- [ ] Documentar variables de entorno nuevas
- [ ] Documentar flujo de reprocesamiento

#### 10.2 Documentación de usuario
- [ ] Actualizar `README.md` o crear `REPROCESSING.md`
- [ ] Explicar cómo funciona el reprocesamiento automático
- [ ] Explicar cómo usar dry-run
- [ ] Explicar qué hacer con facturas en `error_permanente`

---

## ORDEN DE IMPLEMENTACIÓN

1. **Fase 1** (BD) → Base para todo
2. **Fase 2** (Repositorio) → Consultas necesarias
3. **Fase 3** (DriveClient) → Descarga de archivos
4. **Fase 4** (Lógica) → Core del reprocesamiento
5. **Fase 5** (Integración) → Conectar con job
6. **Fase 6** (Auditoría) → Trazabilidad
7. **Fase 7** (Dry-run) → Testing seguro
8. **Fase 8** (Estado permanente) → Manejo de errores
9. **Fase 9** (Testing) → Validar funcionamiento
10. **Fase 10** (Docs) → Documentar

---

## ARCHIVOS A MODIFICAR/CREAR

### Nuevos archivos:
- `migrations/004_add_reprocess_fields.sql`
- `docs/REPROCESSING.md` (opcional)

### Archivos a modificar:
- `src/db/models.py` (agregar campos)
- `src/db/repositories.py` (nuevos métodos)
- `src/drive_client.py` (método get_file_by_id)
- `src/pipeline/ingest_incremental.py` (integración)
- `src/pipeline/validate.py` (nuevo estado)
- `.env.example` (nuevas variables)

---

## VARIABLES DE ENTORNO NUEVAS

```env
# Reprocesamiento automático de facturas en "revisar"
REPROCESS_REVIEW_ENABLED=true
REPROCESS_REVIEW_MAX_DAYS=30
REPROCESS_REVIEW_MAX_COUNT=50
REPROCESS_REVIEW_MAX_ATTEMPTS=3
REPROCESS_REVIEW_DRY_RUN=false
```

---

## ESTIMACIÓN DE ESFUERZO

- **Fase 1-3:** 2-3 horas (BD, repositorio, DriveClient)
- **Fase 4-5:** 3-4 horas (Lógica e integración)
- **Fase 6-8:** 1-2 horas (Auditoría, dry-run, estados)
- **Fase 9-10:** 2-3 horas (Testing y docs)

**Total estimado:** 8-12 horas

---

## RIESGOS Y MITIGACIONES

| Riesgo | Mitigación |
|--------|-----------|
| Reprocesar facturas legítimamente problemáticas infinitamente | Límite de 3 intentos + estado `error_permanente` |
| Sobrecargar OpenAI API | Límite de 50 facturas por ejecución |
| Consumir demasiado tiempo en job | Ejecutar antes de procesar nuevos (más rápido) |
| Facturas muy antiguas en loop | Límite de 30 días |
| Dry-run no funciona correctamente | Testing exhaustivo antes de activar |

---

## CRITERIOS DE ÉXITO

- ✅ 73 facturas actuales en "revisar" se reprocesan automáticamente
- ✅ Facturas que pasan validación cambian a "procesado"
- ✅ Facturas que fallan 3 veces se marcan como "error_permanente"
- ✅ No se reprocesan facturas indefinidamente
- ✅ Dry-run funciona correctamente
- ✅ Auditoría completa en logs y BD
- ✅ Job incremental incluye reprocesamiento sin errores

---

**Estado:** ⏳ Esperando aprobación para comenzar implementación

