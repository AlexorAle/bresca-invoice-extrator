# Plan de Implementación: Mejoras de Edge Cases

**Fecha:** 9 de noviembre de 2025  
**Objetivo:** Implementar mejoras críticas y medias para robustecer el sistema

---

## ESTRATEGIA DE IMPLEMENTACIÓN

- **Enfoque:** Fases incrementales con pruebas completas antes de avanzar
- **Principio:** Una fase a la vez, verificar funcionamiento, luego avanzar
- **Testing:** Cada fase incluye pruebas unitarias, de integración y de escenario real

---

## FASE 1: Protección contra Ejecuciones Concurrentes (7.4)

**Prioridad:** 🔴 ALTA  
**Esfuerzo:** Bajo  
**Riesgo de implementación:** Bajo

### Objetivo
Prevenir que múltiples instancias del job se ejecuten simultáneamente, evitando condiciones de carrera y procesamiento duplicado.

### Implementación

#### 1.1 Instalar dependencia
```bash
pip install filelock
```

#### 1.2 Crear módulo de lock
**Archivo:** `src/pipeline/job_lock.py` (NUEVO)
- Usar `filelock.FileLock` para crear lock file
- Lock file: `data/.job_running.lock`
- Timeout: 5 minutos (si otro proceso muere, el lock se libera)
- Context manager para manejo seguro

#### 1.3 Integrar en pipeline incremental
**Archivo:** `src/pipeline/ingest_incremental.py`
- Agregar lock al inicio de `run()`
- Liberar lock en `finally` block
- Si lock está activo → log warning y salir con código 1

#### 1.4 Integrar en scripts de ejecución
**Archivos:** 
- `scripts/run_ingest_incremental.py`
- `scripts/monitorear_drive.sh`
- Verificar lock antes de ejecutar

### Pruebas

#### Test 1.1: Ejecución única
```bash
# Terminal 1
python scripts/run_ingest_incremental.py

# Terminal 2 (mientras corre el primero)
python scripts/run_ingest_incremental.py
# Esperado: Segundo proceso debe detectar lock y salir con mensaje claro
```

#### Test 1.2: Lock liberado después de crash
```bash
# Simular crash
python scripts/run_ingest_incremental.py &
PID=$!
sleep 5
kill -9 $PID

# Verificar que lock se libera después de timeout
# Esperado: Lock file debe desaparecer o ser liberable después de timeout
```

#### Test 1.3: Ejecución normal con lock
```bash
# Ejecutar job normal
python scripts/run_ingest_incremental.py
# Esperado: Debe ejecutarse normalmente, lock se crea y libera correctamente
```

#### Test 1.4: Verificar en logs
```bash
# Verificar que logs muestran información de lock
grep -i "lock" logs/extractor.log
# Esperado: Logs claros sobre adquisición/liberación de lock
```

### Criterios de Éxito
- ✅ Segundo proceso detecta lock y sale sin procesar
- ✅ Lock se libera correctamente después de ejecución normal
- ✅ Lock se libera después de timeout si proceso muere
- ✅ Logs claros sobre estado del lock
- ✅ No hay condiciones de carrera en pruebas concurrentes

### Archivos a Modificar/Crear
- `src/pipeline/job_lock.py` (NUEVO)
- `src/pipeline/ingest_incremental.py`
- `scripts/run_ingest_incremental.py`
- `requirements.txt` (agregar filelock)

---

## FASE 2: Validación de Tamaño de PDF (9.2)

**Prioridad:** 🔴 ALTA  
**Esfuerzo:** Bajo  
**Riesgo de implementación:** Bajo

### Objetivo
Validar tamaño de archivo antes de descargar/procesar para evitar timeouts y consumo excesivo de recursos.

### Implementación

#### 2.1 Agregar variable de entorno
```env
MAX_PDF_SIZE_MB=50  # Límite por defecto
```

#### 2.2 Validar tamaño en DriveClient
**Archivo:** `src/drive_client.py`
- En `download_file()`, verificar `file_info.get('size')` antes de descargar
- Convertir a MB y comparar con límite
- Si excede → retornar `False` y log error

#### 2.3 Validar en pipeline
**Archivo:** `src/pipeline/ingest.py`
- Antes de descargar, verificar tamaño desde metadata de Drive
- Si excede → marcar como error, registrar evento, mover a cuarentena
- Mensaje: "Archivo excede tamaño máximo permitido: X MB"

#### 2.4 Agregar estadística
**Archivo:** `src/pipeline/ingest_incremental.py`
- Contador: `files_rejected_size`
- Incluir en estadísticas finales

### Pruebas

#### Test 2.1: PDF normal (dentro del límite)
```bash
# Procesar PDF de 5MB
# Esperado: Se procesa normalmente
```

#### Test 2.2: PDF grande (excede límite)
```bash
# Crear PDF de 60MB (o configurar límite a 10MB y usar PDF de 15MB)
# Esperado: 
# - No se descarga
# - Se marca como error
# - Mensaje claro en logs
# - Estadística files_rejected_size incrementada
```

#### Test 2.3: Límite configurable
```bash
# Configurar MAX_PDF_SIZE_MB=10
# Procesar PDF de 15MB
# Esperado: Rechazado

# Configurar MAX_PDF_SIZE_MB=100
# Procesar mismo PDF
# Esperado: Aceptado
```

#### Test 2.4: Sin información de tamaño
```bash
# Procesar archivo donde Drive no devuelve size
# Esperado: Se procesa normalmente (no falla por falta de size)
```

### Criterios de Éxito
- ✅ PDFs grandes se rechazan antes de descargar
- ✅ Mensaje de error claro en logs
- ✅ Estadística se incrementa correctamente
- ✅ Límite es configurable vía variable de entorno
- ✅ PDFs normales no se afectan

### Archivos a Modificar
- `src/drive_client.py`
- `src/pipeline/ingest.py`
- `src/pipeline/ingest_incremental.py`
- `.env.example` (documentar MAX_PDF_SIZE_MB)

---

## FASE 3: Script de Reprocesamiento Manual (10.5)

**Prioridad:** 🔴 ALTA  
**Esfuerzo:** Bajo  
**Riesgo de implementación:** Bajo

### Objetivo
Crear herramienta CLI para reprocesar facturas específicas manualmente sin modificar BD directamente.

### Implementación

#### 3.1 Crear script CLI
**Archivo:** `scripts/reprocess_invoice.py` (NUEVO)
- Argumentos:
  - `--drive-file-id`: ID del archivo en Drive (requerido)
  - `--force`: Forzar reprocesamiento aunque esté en "procesado"
  - `--reset-attempts`: Resetear contador de intentos
- Funcionalidad:
  - Buscar factura en BD por `drive_file_id`
  - Si no existe → error
  - Si existe y está en "procesado" sin `--force` → error
  - Descargar desde Drive
  - Reprocesar usando `process_batch()`
  - Mostrar resultado

#### 3.2 Integrar con sistema existente
- Reutilizar `process_batch()` de `ingest.py`
- Usar `DriveClient.get_file_by_id()`
- Usar `FacturaRepository` para consultas

#### 3.3 Agregar opción de dry-run
- `--dry-run`: Mostrar qué se haría sin ejecutar

### Pruebas

#### Test 3.1: Reprocesar factura en "revisar"
```bash
# Obtener drive_file_id de factura en "revisar"
python scripts/reprocess_invoice.py --drive-file-id <id>
# Esperado: 
# - Descarga archivo
# - Reprocesa
# - Muestra resultado
# - Actualiza estado si pasa validación
```

#### Test 3.2: Reprocesar factura en "procesado" (sin force)
```bash
python scripts/reprocess_invoice.py --drive-file-id <id_procesado>
# Esperado: Error claro indicando que necesita --force
```

#### Test 3.3: Reprocesar con --force
```bash
python scripts/reprocess_invoice.py --drive-file-id <id> --force
# Esperado: Reprocesa aunque esté en "procesado"
```

#### Test 3.4: Resetear intentos
```bash
python scripts/reprocess_invoice.py --drive-file-id <id> --reset-attempts
# Esperado: 
# - reprocess_attempts se resetea a 0
# - Se reprocesa
```

#### Test 3.5: Factura inexistente
```bash
python scripts/reprocess_invoice.py --drive-file-id "inexistente"
# Esperado: Error claro indicando que no existe
```

#### Test 3.6: Dry-run
```bash
python scripts/reprocess_invoice.py --drive-file-id <id> --dry-run
# Esperado: Muestra información sin ejecutar
```

### Criterios de Éxito
- ✅ Script funciona con todos los argumentos
- ✅ Maneja errores correctamente (factura no existe, ya procesada, etc.)
- ✅ Reprocesa correctamente facturas en "revisar"
- ✅ ✅ Opción --force funciona para facturas procesadas
- ✅ Dry-run muestra información sin ejecutar
- ✅ Logs claros de lo que hace

### Archivos a Crear/Modificar
- `scripts/reprocess_invoice.py` (NUEVO)
- `README.md` (documentar script)

---

## FASE 4: Detección de Archivos Eliminados de Drive (2.5)

**Prioridad:** 🔴 ALTA  
**Esfuerzo:** Medio  
**Riesgo de implementación:** Medio

### Objetivo
Detectar y marcar facturas en BD cuyos archivos fueron eliminados de Drive, evitando crecimiento indefinido de registros huérfanos.

### Implementación

#### 4.1 Agregar campo en BD
**Migración:** `migrations/005_add_deleted_flag.sql`
- Agregar columna: `deleted_from_drive BOOLEAN DEFAULT FALSE`
- Agregar índice: `idx_facturas_deleted` en `deleted_from_drive`
- Actualizar modelo: `src/db/models.py`

#### 4.2 Crear job de reconciliación
**Archivo:** `scripts/reconcile_deleted_files.py` (NUEVO)
- Consultar todas las facturas en BD (no eliminadas)
- Para cada una, verificar existencia en Drive usando `get_file_by_id()`
- Si no existe → marcar `deleted_from_drive = TRUE`
- Registrar evento de auditoría
- Opción: `--dry-run` para ver qué se marcaría

#### 4.3 Agregar a cron (opcional)
- Ejecutar semanalmente (domingos 2 AM)
- O ejecutar manualmente cuando sea necesario

#### 4.4 Filtrar en queries (opcional)
- Modificar queries de reportes para excluir `deleted_from_drive = TRUE`
- O crear vista que filtre automáticamente

### Pruebas

#### Test 4.1: Archivo existe en Drive
```bash
# Ejecutar reconciliación
python scripts/reconcile_deleted_files.py
# Esperado: No marca nada como eliminado
```

#### Test 4.2: Archivo eliminado de Drive
```bash
# 1. Crear factura en BD
# 2. Eliminar archivo de Drive manualmente
# 3. Ejecutar reconciliación
python scripts/reconcile_deleted_files.py
# Esperado: 
# - Marca deleted_from_drive = TRUE
# - Registra evento de auditoría
# - Log claro
```

#### Test 4.3: Dry-run
```bash
python scripts/reconcile_deleted_files.py --dry-run
# Esperado: Muestra qué se marcaría sin ejecutar
```

#### Test 4.4: Performance con muchas facturas
```bash
# Ejecutar con 100+ facturas
# Esperado: 
# - No bloquea BD
# - Procesa en lotes si es necesario
# - Tiempo razonable (< 5 min para 1000 facturas)
```

#### Test 4.5: Verificar en BD
```sql
-- Verificar facturas marcadas como eliminadas
SELECT COUNT(*) FROM facturas WHERE deleted_from_drive = TRUE;
-- Esperado: Solo las que realmente fueron eliminadas
```

### Criterios de Éxito
- ✅ Detecta correctamente archivos eliminados
- ✅ Marca correctamente en BD
- ✅ Registra eventos de auditoría
- ✅ Dry-run funciona
- ✅ Performance aceptable (no bloquea sistema)
- ✅ No marca incorrectamente archivos que existen

### Archivos a Crear/Modificar
- `migrations/005_add_deleted_flag.sql` (NUEVO)
- `src/db/models.py`
- `scripts/reconcile_deleted_files.py` (NUEVO)
- `README.md` (documentar job)

---

## FASE 5: Limpieza Automática de Facturas "Pendiente" (6.2)

**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** Bajo  
**Riesgo de implementación:** Bajo

### Objetivo
Cambiar automáticamente facturas en estado "pendiente" > 24 horas a "error" para evitar facturas stuck indefinidamente.

### Implementación

#### 5.1 Crear función de limpieza
**Archivo:** `src/db/repositories.py`
- Método: `cleanup_stuck_pending_invoices(hours: int = 24)`
- Query: facturas con `estado = 'pendiente'` y `actualizado_en < ahora - hours`
- Actualizar: `estado = 'error'`, `error_msg = 'Factura en pendiente > 24h, marcada como error'`
- Retornar: número de facturas actualizadas

#### 5.2 Integrar en job incremental
**Archivo:** `src/pipeline/ingest_incremental.py`
- Al inicio de `run()`, antes de procesar archivos
- Ejecutar limpieza
- Log: número de facturas limpiadas

#### 5.3 Variable de entorno
```env
CLEANUP_PENDING_HOURS=24  # Horas antes de marcar como error
```

### Pruebas

#### Test 5.1: Factura pendiente < 24h
```bash
# Crear factura en estado "pendiente" hace 12 horas
# Ejecutar job
# Esperado: No cambia estado
```

#### Test 5.2: Factura pendiente > 24h
```bash
# Crear factura en estado "pendiente" hace 30 horas
# Ejecutar job
# Esperado: 
# - Estado cambia a "error"
# - error_msg indica razón
# - Log muestra factura limpiada
```

#### Test 5.3: Múltiples facturas
```bash
# Crear 5 facturas pendientes > 24h
# Ejecutar job
# Esperado: Todas se actualizan
```

#### Test 5.4: Configuración de horas
```bash
# Configurar CLEANUP_PENDING_HOURS=12
# Crear factura pendiente hace 15 horas
# Ejecutar job
# Esperado: Se marca como error
```

### Criterios de Éxito
- ✅ Facturas > 24h se marcan como error
- ✅ Facturas < 24h no se afectan
- ✅ Logs claros de limpieza
- ✅ Configurable vía variable de entorno
- ✅ No afecta otras facturas

### Archivos a Modificar
- `src/db/repositories.py`
- `src/pipeline/ingest_incremental.py`
- `.env.example` (documentar CLEANUP_PENDING_HOURS)

---

## FASE 6: Validación de Espacio en Disco (9.4)

**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** Bajo  
**Riesgo de implementación:** Bajo

### Objetivo
Validar espacio en disco antes de procesar para evitar fallos por falta de espacio.

### Implementación

#### 6.1 Crear función de validación
**Archivo:** `src/utils/disk_space.py` (NUEVO)
- Función: `check_disk_space(min_percent: int = 10, critical_percent: int = 5)`
- Usar `shutil.disk_usage()` para obtener espacio disponible
- Retornar: `(has_space, is_critical, available_gb, total_gb)`
- Log: advertencia si < 10%, error si < 5%

#### 6.2 Integrar en pipeline
**Archivo:** `src/pipeline/ingest_incremental.py`
- Al inicio de `run()`, verificar espacio
- Si < 5% → salir con error, no procesar
- Si < 10% → advertencia pero continuar
- Log: espacio disponible y porcentaje

#### 6.3 Variables de entorno
```env
DISK_SPACE_WARNING_PERCENT=10  # Advertencia si < X%
DISK_SPACE_CRITICAL_PERCENT=5  # Error si < X%
```

### Pruebas

#### Test 6.1: Espacio suficiente
```bash
# Ejecutar job con espacio > 10%
# Esperado: Se ejecuta normalmente
```

#### Test 6.2: Espacio bajo (advertencia)
```bash
# Simular espacio < 10% (o configurar límite alto)
# Ejecutar job
# Esperado: 
# - Advertencia en logs
# - Continúa ejecutándose
```

#### Test 6.3: Espacio crítico (error)
```bash
# Simular espacio < 5%
# Ejecutar job
# Esperado: 
# - Error en logs
# - Job sale sin procesar
# - Código de salida != 0
```

#### Test 6.4: Configuración personalizada
```bash
# Configurar DISK_SPACE_CRITICAL_PERCENT=15
# Simular espacio < 15%
# Esperado: Sale con error
```

### Criterios de Éxito
- ✅ Detecta espacio bajo correctamente
- ✅ Advertencia si < 10%
- ✅ Error y salida si < 5%
- ✅ Configurable vía variables de entorno
- ✅ Logs claros con espacio disponible

### Archivos a Crear/Modificar
- `src/utils/disk_space.py` (NUEVO)
- `src/pipeline/ingest_incremental.py`
- `.env.example` (documentar variables)

---

## FASE 7: Detección de Cambios en Archivos en Cuarentena (8.3)

**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** Medio  
**Riesgo de implementación:** Medio

### Objetivo
Detectar cuando archivos en cuarentena se corrigen en Drive y reprocesarlos automáticamente.

### Implementación

#### 7.1 Extender sistema de reprocesamiento
**Archivo:** `src/pipeline/ingest_incremental.py`
- Modificar `_reprocess_review_invoices()` para incluir archivos en cuarentena
- Consultar facturas con `estado IN ('revisar', 'error')` que tienen archivo en cuarentena
- Verificar si archivo fue modificado en Drive (`modifiedTime`)
- Si fue modificado → reprocesar

#### 7.2 Consultar cuarentena
**Archivo:** `src/db/repositories.py`
- Método: `get_facturas_en_cuarentena_para_reprocesar()`
- Query: facturas con estado problemático que tienen archivo en `data/quarantine/`
- Filtrar por `modifiedTime` en Drive > `actualizado_en` en BD

#### 7.3 Integrar con reprocesamiento existente
- Reutilizar lógica de `_reprocess_review_invoices()`
- Agregar flag: `include_quarantine=True` (configurable)

### Pruebas

#### Test 7.1: Archivo en cuarentena sin cambios
```bash
# Archivo en cuarentena, no modificado en Drive
# Ejecutar job
# Esperado: No se reprocesa
```

#### Test 7.2: Archivo en cuarentena con cambios
```bash
# 1. Archivo en cuarentena
# 2. Modificar archivo en Drive
# 3. Ejecutar job
# Esperado: 
# - Detecta cambio
# - Reprocesa
# - Si pasa validación → estado cambia a "procesado"
```

#### Test 7.3: Múltiples archivos en cuarentena
```bash
# Varios archivos en cuarentena, algunos modificados
# Ejecutar job
# Esperado: Solo reprocesa los modificados
```

#### Test 7.4: Deshabilitar reprocesamiento de cuarentena
```bash
# Configurar REPROCESS_INCLUDE_QUARANTINE=false
# Ejecutar job
# Esperado: No reprocesa archivos en cuarentena
```

### Criterios de Éxito
- ✅ Detecta cambios en archivos en cuarentena
- ✅ Reprocesa solo los modificados
- ✅ No reprocesa si no hay cambios
- ✅ Configurable (habilitar/deshabilitar)
- ✅ Performance aceptable

### Archivos a Modificar
- `src/db/repositories.py`
- `src/pipeline/ingest_incremental.py`
- `.env.example` (documentar REPROCESS_INCLUDE_QUARANTINE)

---

## FASE 8: Manejo de Fechas en Texto Natural (3.3)

**Prioridad:** 🟡 MEDIA  
**Esfuerzo:** Medio  
**Riesgo de implementación:** Bajo

### Objetivo
Manejar fechas extraídas en formato texto natural ("10 de enero 2025") que actualmente fallan en validación.

### Implementación

#### 8.1 Instalar dependencia
```bash
pip install dateparser
```

#### 8.2 Extender normalización de fechas
**Archivo:** `src/parser_normalizer.py`
- Modificar `normalize_date()` para incluir fallback
- Si formatos estándar fallan → usar `dateparser.parse()`
- Configurar `dateparser` para español/español de España
- Si `dateparser` también falla → retornar `None`

#### 8.3 Agregar tests
**Archivo:** `tests/test_date_normalization.py` (NUEVO)
- Test: "10 de enero 2025" → 2025-01-10
- Test: "veinte de marzo de dos mil veinticinco" → 2025-03-20
- Test: Formatos estándar siguen funcionando

### Pruebas

#### Test 8.1: Fecha en texto natural
```bash
# Procesar factura con fecha "10 de enero 2025"
# Esperado: 
# - Se parsea correctamente
# - Se guarda como 2025-01-10
# - Pasa validación
```

#### Test 8.2: Formatos estándar siguen funcionando
```bash
# Procesar facturas con formatos estándar (DD/MM/YYYY, etc.)
# Esperado: Siguen funcionando como antes
```

#### Test 8.3: Fecha inválida
```bash
# Procesar factura con fecha "fecha inválida"
# Esperado: 
# - Retorna None
# - Factura va a "revisar" (no error)
```

#### Test 8.4: Múltiples idiomas
```bash
# Procesar factura con fecha en inglés "January 10, 2025"
# Esperado: Se parsea correctamente
```

### Criterios de Éxito
- ✅ Parsea fechas en texto natural en español
- ✅ Formatos estándar siguen funcionando
- ✅ Maneja errores gracefully (None si no puede parsear)
- ✅ No rompe funcionalidad existente
- ✅ Performance aceptable (dateparser es rápido)

### Archivos a Modificar
- `src/parser_normalizer.py`
- `requirements.txt` (agregar dateparser)
- `tests/test_date_normalization.py` (NUEVO)

---

## ORDEN DE EJECUCIÓN

1. **Fase 1** → Pruebas → ✅ OK → Avanzar
2. **Fase 2** → Pruebas → ✅ OK → Avanzar
3. **Fase 3** → Pruebas → ✅ OK → Avanzar
4. **Fase 4** → Pruebas → ✅ OK → Avanzar
5. **Fase 5** → Pruebas → ✅ OK → Avanzar
6. **Fase 6** → Pruebas → ✅ OK → Avanzar
7. **Fase 7** → Pruebas → ✅ OK → Avanzar
8. **Fase 8** → Pruebas → ✅ OK → Completado

---

## CHECKLIST DE PRUEBAS GENERALES

Después de cada fase, ejecutar:

- [ ] Pruebas específicas de la fase (ver sección de pruebas)
- [ ] Ejecutar job incremental completo sin errores
- [ ] Verificar logs no tienen errores inesperados
- [ ] Verificar que funcionalidad existente no se rompe
- [ ] Verificar estadísticas se generan correctamente
- [ ] Verificar que no hay regresiones

---

## NOTAS IMPORTANTES

1. **Backup antes de cada fase:** Hacer backup de BD antes de migraciones
2. **Variables de entorno:** Documentar todas las nuevas variables en `.env.example`
3. **Logs:** Asegurar que todos los cambios tienen logging adecuado
4. **Documentación:** Actualizar README.md con nuevas funcionalidades
5. **Rollback:** Cada fase debe ser reversible (especialmente migraciones de BD)

---

## ESTIMACIÓN TOTAL

- **Fases ALTA prioridad (1-4):** ~8-12 horas
- **Fases MEDIA prioridad (5-8):** ~6-10 horas
- **Total estimado:** 14-22 horas

---

**Estado:** ⏳ Pendiente de inicio  
**Última actualización:** 9 de noviembre de 2025

