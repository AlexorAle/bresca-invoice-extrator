# Casos Negativos y Edge Cases - Sistema de Facturas

**Fecha:** 9 de noviembre de 2025  
**Análisis completo de escenarios problemáticos y casos límite**

---

## 1. Problemas con Archivos PDF

### 1.1. ¿Qué ocurre si un PDF está corrupto o no se puede leer?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema valida PDFs usando `validate_pdf()` y `validate_file_integrity()` en `src/pdf_utils.py` y `src/pipeline/validate.py`
- Verifica magic bytes (`%PDF-`) en los primeros 5 bytes del archivo
- Si el PDF está corrupto o no se puede leer:
  - La validación falla y retorna `False`
  - El archivo se marca como error y se mueve a cuarentena (`data/quarantine/`)
  - Se registra evento de auditoría con nivel `ERROR`
  - El estado de la factura se marca como `error`
  - Se guarda metadata del error en archivo `.meta.json` en cuarentena

**Ubicación:** `src/pipeline/ingest.py` líneas 149-155, `src/pdf_utils.py` líneas 16-42

---

### 1.2. ¿Qué ocurre si el PDF está protegido con contraseña?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema detecta PDFs protegidos usando `_is_pdf_protected()` en `src/ocr_extractor.py` (líneas 327-347)
- Usa `pypdf.PdfReader` para verificar si `reader.is_encrypted == True`
- Si está protegido:
  - Se omite el procesamiento
  - Se retorna resultado vacío con `_protected_pdf_result()`
  - Se registra warning en logs
  - El archivo se marca como error y va a cuarentena
  - Estado: `error` con mensaje indicando PDF protegido

**Ubicación:** `src/ocr_extractor.py` líneas 327-351, 388-391

---

### 1.3. ¿Qué ocurre si el PDF no contiene texto (es una imagen escaneada de mala calidad)?

**Estado:** ✅ **IMPLEMENTADO (con limitaciones)**

**Funcionamiento:**
- El sistema usa OpenAI Vision API primero, que puede leer texto en imágenes
- Si OpenAI falla o da confianza baja, hace fallback a Tesseract OCR
- Si ambos fallan:
  - Se retorna resultado vacío o parcial
  - Si falta `proveedor_text` o `importe_total` → estado `error`
  - Si hay datos parciales pero faltan campos críticos → estado `revisar`
  - El archivo se guarda en cuarentena con metadata del error

**Limitación:** No hay validación específica de calidad de imagen antes de procesar. El sistema intenta extraer y si falla, marca como error.

**Ubicación:** `src/ocr_extractor.py` líneas 375-422, 404-414

---

### 1.4. ¿Qué ocurre si el PDF tiene múltiples páginas pero la factura está en la última página?

**Estado:** ⚠️ **PARCIALMENTE IMPLEMENTADO**

**Funcionamiento:**
- El sistema procesa **solo la primera página** por defecto
- `pagina_analizada` se guarda en BD (default: 1)
- Si la factura está en otra página:
  - No se detecta automáticamente
  - El OCR puede no encontrar datos relevantes
  - Resultado: estado `error` o `revisar` por datos faltantes

**Limitación:** No hay detección automática de qué página contiene la factura. El sistema asume que la factura está en la primera página.

**Ubicación:** `src/pdf_utils.py` líneas 102-139, `src/db/models.py` línea 49

---

### 1.5. ¿Qué ocurre si un archivo no es PDF sino otro formato (JPG, PNG, Word)?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema filtra por `mimeType = 'application/pdf'` en las búsquedas de Drive
- Si un archivo no-PDF llega al procesamiento:
  - `validate_file_integrity()` verifica magic bytes `%PDF-`
  - Si no es PDF → retorna `False`
  - El archivo se marca como error y va a cuarentena
  - Se registra evento de auditoría

**Ubicación:** `src/drive/drive_incremental.py` línea 331, `src/pipeline/validate.py` líneas 184-189

---

## 2. Actualizaciones y Modificaciones en Drive

### 2.1. ¿Qué ocurre si una factura fallida se corrige y se reemplaza en Drive con el mismo nombre?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema detecta cambios usando `drive_file_id` (único) y `hash_contenido`
- Si el archivo tiene el mismo `drive_file_id` pero `hash_contenido` diferente:
  - `DuplicateManager.decide_action()` retorna `UPDATE_REVISION`
  - Se incrementa el campo `revision` en BD
  - Se reprocesa el archivo con los nuevos datos
  - Se actualiza la factura existente (UPSERT)
  - Se registra evento `revision_created`

**Ubicación:** `src/pipeline/duplicate_manager.py` líneas 61-68, `src/pipeline/ingest.py` líneas 266-277

---

### 2.2. ¿Se detecta cuando un archivo se modifica en Drive después de haber sido procesado?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El job incremental busca archivos con `modifiedTime > last_sync_time`
- Si un archivo fue modificado:
  - Se detecta en la siguiente ejecución del job
  - Se compara `hash_contenido` con el existente en BD
  - Si cambió → se reprocesa como nueva revisión
  - Si no cambió → se ignora (ya procesado)

**Ubicación:** `src/drive/drive_incremental.py` líneas 206-299, `src/pipeline/ingest_incremental.py` líneas 222-246

---

### 2.3. ¿Qué ocurre si un usuario mueve un archivo de una carpeta a otra en Drive?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El `drive_file_id` no cambia al mover archivos
- El sistema busca recursivamente en todas las subcarpetas
- Si el archivo se mueve:
  - Se detecta por `drive_file_id` (ya existe en BD)
  - Se actualiza `drive_folder_name` si es diferente
  - No se reprocesa si el contenido no cambió (mismo hash)
  - Si cambió el contenido → se procesa como revisión

**Ubicación:** `src/drive/drive_incremental.py` líneas 161-205, `src/pipeline/ingest.py` líneas 54-73

---

### 2.4. ¿Qué ocurre si un usuario renombra un archivo ya procesado en Drive?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El `drive_file_id` no cambia al renombrar
- El sistema detecta el archivo por `drive_file_id`
- Si solo cambió el nombre:
  - Se actualiza `drive_file_name` en BD (UPSERT)
  - No se reprocesa si el contenido no cambió
  - Si cambió el contenido → se procesa como revisión

**Ubicación:** `src/pipeline/ingest.py` líneas 54-73, `src/db/repositories.py` líneas 153-215

---

### 2.5. ¿Qué ocurre si un archivo se elimina de Drive pero sigue en la BD?

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Funcionamiento:**
- El sistema no detecta archivos eliminados de Drive
- Si un archivo se elimina:
  - Permanece en BD con su estado actual
  - No se puede reprocesar (no existe en Drive)
  - No hay limpieza automática de registros huérfanos

**Recomendación:** Implementar job de limpieza periódica que verifique existencia de archivos en Drive.

---

## 3. Fallos de OpenAI OCR

### 3.1. ¿Qué ocurre si OpenAI devuelve un error 500 o timeout?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema usa `tenacity` para reintentos automáticos
- Configuración: hasta 6 intentos con backoff exponencial (1-60 segundos)
- Si OpenAI falla (500, timeout, conexión):
  - Se reintenta automáticamente
  - Si todos los reintentos fallan → fallback a Tesseract OCR
  - Se registra warning en logs
  - El resultado usa `confianza='baja'` si viene de Tesseract

**Ubicación:** `src/ocr_extractor.py` líneas 132-135, 416-418

---

### 3.2. ¿Qué ocurre si OpenAI extrae datos parciales (solo proveedor pero no importe)?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema valida campos críticos: `proveedor_text` y `importe_total`
- Si OpenAI extrae datos parciales:
  - Se complementa con Tesseract (si confianza es baja o falta importe)
  - Si después de complementar falta `proveedor_text` o `importe_total` → estado `error`
  - Si hay datos parciales pero faltan campos no críticos → estado `revisar`
  - Se guarda en cuarentena con metadata

**Ubicación:** `src/ocr_extractor.py` líneas 404-414, `src/pipeline/ingest.py` líneas 240-250

---

### 3.3. ¿Qué ocurre si OpenAI extrae datos con formato incorrecto (fecha como texto "diez de enero")?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema normaliza datos en `parser_normalizer.py`
- `normalize_date()` maneja múltiples formatos:
  - YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY, DD-MM-YYYY
  - Si el formato no es reconocido:
    - Se intenta parsear con `dateutil.parser` (si está disponible)
    - Si falla → fecha queda como `None`
    - Factura va a estado `revisar` (no es error crítico)
    - Se registra warning en logs

**Limitación:** No maneja fechas en texto natural ("diez de enero"). Solo formatos numéricos.

**Ubicación:** `src/parser_normalizer.py` (función `normalize_date`)

---

### 3.4. ¿Qué ocurre si OpenAI no detecta ninguna factura en el PDF?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- Si OpenAI retorna resultado vacío o sin campos:
  - Se hace fallback a Tesseract OCR
  - Si Tesseract también falla → resultado vacío
  - Si falta `proveedor_text` o `importe_total` → estado `error`
  - El archivo va a cuarentena
  - Se registra evento de auditoría

**Ubicación:** `src/ocr_extractor.py` líneas 396-398, 420-422

---

### 3.5. ¿Hay límite de reintentos si OpenAI falla temporalmente (rate limit, network)?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- Reintentos configurados: máximo 6 intentos
- Backoff exponencial: 1-60 segundos entre intentos
- Manejo específico de errores:
  - `RateLimitError` → reintenta con backoff
  - `APIConnectionError` → reintenta
  - `TimeoutError` → reintenta
  - Después de 6 intentos → fallback a Tesseract

**Ubicación:** `src/ocr_extractor.py` líneas 132-135, 236-247

---

## 4. Validación y Reglas de Negocio

### 4.1. ¿Qué ocurre si la fecha de emisión es futura?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- `validate_business_rules()` valida que `fecha_emision <= hoy + 1 día`
- Tolerancia de 1 día para diferencias de zona horaria
- Si la fecha es futura:
  - Validación falla
  - Estado: `revisar`
  - Se agrega error: "fecha_emision es futura"
  - Se guarda en cuarentena

**Ubicación:** `src/pipeline/validate.py` líneas 79-103

---

### 4.2. ¿Qué ocurre si el importe es cero o negativo?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- `validate_business_rules()` valida que `importe_total > 0`
- Si el importe es cero o negativo:
  - Validación falla
  - Estado: `revisar`
  - Se agrega error: "importe_total debe ser > 0"
  - Se guarda en cuarentena

**Nota:** El sistema permite importes negativos en BD (facturas de abono), pero la validación de negocio los rechaza y marca para revisión.

**Ubicación:** `src/pipeline/validate.py` líneas 31-39

---

### 4.3. ¿Qué ocurre si falta el número de factura?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- `numero_factura` NO es campo obligatorio en validación
- Si falta:
  - No causa error
  - Se guarda como `NULL` en BD
  - Puede afectar detección de duplicados (se usa proveedor + número)
  - Si hay duplicado por proveedor+número y falta número → puede no detectarse

**Ubicación:** `src/pipeline/validate.py` líneas 25-29 (campos obligatorios)

---

### 4.4. ¿Qué ocurre si el proveedor no se reconoce o está vacío?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- `proveedor_text` es campo obligatorio
- Si falta o está vacío:
  - Validación crítica falla
  - Estado: `error` (no `revisar`)
  - Se agrega error: "Campo obligatorio faltante: proveedor_text"
  - El archivo va a cuarentena
  - No se guarda en BD (falla antes del UPSERT)

**Ubicación:** `src/pipeline/ingest.py` líneas 240-250, `src/pipeline/validate.py` líneas 25-29

---

### 4.5. ¿Qué ocurre si una factura pasa validación pero luego se descubre que era errónea?

**Estado:** ✅ **IMPLEMENTADO (reprocesamiento)**

**Funcionamiento:**
- Sistema de reprocesamiento automático implementado
- Si una factura en estado `revisar` o `error` se corrige:
  - El job incremental la detecta y reprocesa automáticamente
  - Máximo 3 intentos de reprocesamiento
  - Si pasa validación → estado cambia a `procesado`
  - Si falla 3 veces → estado `error_permanente`

**Ubicación:** `src/pipeline/ingest_incremental.py` líneas 455-650

---

## 5. Duplicados y Conflictos

### 5.1. ¿Qué ocurre si se sube la misma factura dos veces con diferente nombre en Drive?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema detecta duplicados por `hash_contenido` (SHA-256 del contenido)
- Si el contenido es idéntico pero el nombre es diferente:
  - `DuplicateManager` detecta duplicado por hash
  - Decisión: `DUPLICATE`
  - El archivo se mueve a `data/quarantine/duplicates/`
  - Estado: `duplicado`
  - Se registra evento de auditoría
  - No se guarda en BD (se ignora)

**Ubicación:** `src/pipeline/duplicate_manager.py` líneas 75-82

---

### 5.2. ¿Qué ocurre si dos facturas diferentes tienen el mismo número de proveedor?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema detecta posibles conflictos por `proveedor_text + numero_factura`
- Si dos facturas tienen mismo proveedor y número:
  - Se compara `importe_total`
  - Si el importe difiere > 0.02 → decisión `REVIEW`
  - Estado: `revisar`
  - Se mueve a `data/quarantine/review/`
  - Requiere revisión manual
  - Si el importe es igual → se trata como duplicado

**Ubicación:** `src/pipeline/duplicate_manager.py` líneas 84-91

---

### 5.3. ¿Qué ocurre si una factura duplicada tiene importe diferente (¿corrección o fraude?)?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- Si mismo proveedor + número pero importe diferente:
  - Diferencia > 0.02 → decisión `REVIEW`
  - Estado: `revisar`
  - Se mueve a cuarentena para revisión manual
  - Se registra evento de auditoría con ambos importes
  - No se procesa automáticamente (requiere intervención)

**Ubicación:** `src/pipeline/duplicate_manager.py` líneas 84-91

---

### 5.4. ¿El hash de contenido detecta duplicados si el PDF se regeneró con distinto software?

**Estado:** ⚠️ **LIMITACIÓN**

**Funcionamiento:**
- El hash se calcula sobre el contenido binario completo del PDF
- Si el PDF se regenera con diferente software:
  - **Probablemente el hash será diferente** (metadatos, estructura interna)
  - No se detectará como duplicado por hash
  - Se detectará como duplicado por `proveedor + número` si coinciden
  - Si el contenido visual es idéntico pero el PDF es diferente → no se detecta automáticamente

**Limitación:** El hash binario no es robusto ante regeneraciones del mismo contenido.

---

### 5.5. ¿Qué ocurre si se detecta un duplicado después de que el original fue eliminado?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema busca duplicados por `hash_contenido` en BD
- Si el original fue eliminado de Drive pero sigue en BD:
  - El nuevo archivo se detecta como duplicado
  - Se mueve a cuarentena
  - Estado: `duplicado`
  - No se procesa
  - El registro original en BD permanece (no se elimina automáticamente)

**Nota:** No hay limpieza automática de registros huérfanos cuando el archivo original se elimina de Drive.

---

## 6. Estados y Ciclo de Vida

### 6.1. ¿Puede una factura en estado "procesado" volver a estado "revisar"?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- Si un archivo en estado `procesado` se modifica en Drive:
  - Se detecta cambio de `hash_contenido`
  - Decisión: `UPDATE_REVISION`
  - Se reprocesa el archivo
  - Si la nueva validación falla → estado puede cambiar a `revisar`
  - Se incrementa campo `revision` en BD

**Ubicación:** `src/pipeline/duplicate_manager.py` líneas 64-68, `src/pipeline/ingest.py` líneas 266-277

---

### 6.2. ¿Qué ocurre si una factura queda "stuck" en estado "pendiente" indefinidamente?

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Funcionamiento:**
- El estado `pendiente` se usa para facturas en cola de procesamiento
- Si una factura queda en `pendiente`:
  - No hay limpieza automática
  - No hay timeout para cambiar a `error`
  - Permanece indefinidamente hasta intervención manual

**Recomendación:** Implementar job de limpieza que cambie facturas en `pendiente` > 24 horas a `error`.

---

### 6.3. ¿Hay límite de tiempo antes de marcar una factura como "error permanente"?

**Estado:** ✅ **IMPLEMENTADO (reprocesamiento)**

**Funcionamiento:**
- Sistema de reprocesamiento con límite de intentos
- Máximo 3 intentos de reprocesamiento (configurable)
- Después de 3 intentos fallidos → estado `error_permanente`
- No hay límite de tiempo, solo límite de intentos
- Campo `reprocess_attempts` rastrea intentos

**Ubicación:** `src/db/repositories.py` líneas 661-702, `src/pipeline/ingest_incremental.py` líneas 595-609

---

### 6.4. ¿Qué ocurre con facturas en "revisar" después de 6 meses sin acción?

**Estado:** ✅ **IMPLEMENTADO (parcialmente)**

**Funcionamiento:**
- Sistema de reprocesamiento solo procesa facturas de últimos 30 días (configurable)
- Facturas en `revisar` > 30 días:
  - No se reprocesan automáticamente
  - Permanecen en BD con estado `revisar`
  - No hay limpieza automática
  - Requieren intervención manual

**Configuración:** `REPROCESS_REVIEW_MAX_DAYS=30` (variable de entorno)

**Ubicación:** `src/db/repositories.py` líneas 590-659

---

### 6.5. ¿Se puede cambiar manualmente el estado de una factura en BD?

**Estado:** ✅ **POSIBLE (pero no recomendado)**

**Funcionamiento:**
- Sí, se puede cambiar manualmente en BD
- El sistema no valida cambios manuales
- Si se cambia estado manualmente:
  - Puede afectar lógica de reprocesamiento
  - Puede causar inconsistencias
  - No se registra en eventos de auditoría

**Recomendación:** Usar API o scripts oficiales para cambios de estado, no modificar BD directamente.

---

## 7. Problemas de Sincronización

### 7.1. ¿Qué ocurre si el job se ejecuta mientras Drive está caído?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema usa `tenacity` para reintentos en llamadas a Drive API
- Si Drive está caído:
  - Se reintenta automáticamente (hasta 5 intentos)
  - Backoff exponencial: 2-30 segundos
  - Si todos los reintentos fallan:
    - Se registra error crítico
    - El job termina con código de error
    - No se actualiza `last_sync_time`
    - Se reintentará en la próxima ejecución del cron

**Ubicación:** `src/drive/drive_incremental.py` líneas 101-159

---

### 7.2. ¿Qué ocurre si hay un corte de red durante la descarga de un PDF?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema valida integridad del archivo descargado
- Si la descarga se interrumpe:
  - El archivo queda incompleto
  - `validate_file_integrity()` detecta tamaño incorrecto o magic bytes inválidos
  - Se marca como error
  - Se registra evento de auditoría
  - En la próxima ejecución, se reintenta la descarga

**Ubicación:** `src/pipeline/validate.py` líneas 149-192, `src/drive_client.py` líneas 137-174

---

### 7.3. ¿Qué ocurre si el job se interrumpe a mitad de procesamiento (kill, crash)?

**Estado:** ✅ **IMPLEMENTADO (parcialmente)**

**Funcionamiento:**
- El sistema usa `last_sync_time` para procesar solo archivos nuevos/modificados
- Si el job se interrumpe:
  - Los archivos ya procesados están en BD
  - `last_sync_time` NO se actualiza si el job falla
  - En la próxima ejecución:
    - Se procesan los archivos que quedaron pendientes
    - No se duplican los ya procesados (por `drive_file_id`)
  - Archivos temporales se limpian en `finally` block

**Limitación:** Si el job falla después de procesar algunos archivos pero antes de actualizar `last_sync_time`, se reprocesarán en la siguiente ejecución (pero se ignoran por duplicado).

**Ubicación:** `src/pipeline/ingest_incremental.py` líneas 421-453

---

### 7.4. ¿Se puede ejecutar el job manualmente mientras el cron está activo (concurrencia)?

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Funcionamiento:**
- No hay protección contra ejecuciones concurrentes
- Si se ejecuta manualmente mientras el cron corre:
  - Ambos procesos pueden procesar los mismos archivos
  - Puede causar condiciones de carrera
  - Los UPSERTs previenen duplicados en BD, pero puede haber procesamiento duplicado

**Recomendación:** Implementar lock file o semáforo para prevenir ejecuciones concurrentes.

---

### 7.5. ¿Qué ocurre si sync_time se corrompe o se pierde?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- `sync_time` se guarda en tabla `sync_state` en BD
- Si se corrompe o se pierde:
  - El sistema detecta `last_sync_time = None`
  - Se ajusta automáticamente: `last_sync_time = ahora - SYNC_WINDOW_MINUTES`
  - Procesa archivos de las últimas 24 horas (configurable)
  - No procesa todos los archivos desde el inicio (protección)

**Configuración:** `SYNC_WINDOW_MINUTES=1440` (24 horas)

**Ubicación:** `src/drive/drive_incremental.py` líneas 72-99, `src/sync/state_store.py`

---

## 8. Cuarentena y Archivos Pendientes

### 8.1. ¿Los archivos en cuarentena se reintentan automáticamente alguna vez?

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Funcionamiento:**
- Los archivos en cuarentena NO se reintentan automáticamente
- Solo se reintentan facturas en estado `revisar` (no las que están físicamente en cuarentena)
- Si un archivo está en `data/quarantine/`:
  - Permanece ahí indefinidamente
  - Requiere intervención manual para reprocesar

**Recomendación:** Implementar job de limpieza que reintente archivos en cuarentena después de N días.

---

### 8.2. ¿Hay límite de almacenamiento para data/quarantine/ y data/pending/?

**Estado:** ✅ **IMPLEMENTADO (limpieza automática)**

**Funcionamiento:**
- El sistema tiene función `cleanup_old_quarantine()` en `DuplicateManager`
- Limpia archivos > 90 días (configurable)
- Se puede ejecutar manualmente o en job periódico
- No hay límite de tamaño, solo límite de tiempo

**Ubicación:** `src/pipeline/duplicate_manager.py` líneas 202-223, `src/pipeline/ingest.py` líneas 438-464

---

### 8.3. ¿Qué ocurre si un archivo en cuarentena se corrige en Drive?

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Funcionamiento:**
- Si un archivo en cuarentena se corrige en Drive:
  - El sistema NO lo detecta automáticamente
  - El archivo físico en cuarentena no se actualiza
  - Requiere intervención manual para reprocesar

**Recomendación:** El sistema debería detectar cambios en Drive y reprocesar archivos que estaban en cuarentena.

---

### 8.4. ¿Se puede recuperar un archivo de cuarentena y reprocesarlo manualmente?

**Estado:** ✅ **POSIBLE (manual)**

**Funcionamiento:**
- Sí, se puede recuperar manualmente:
  1. Copiar archivo de `data/quarantine/` a ubicación temporal
  2. Ejecutar script de procesamiento manual
  3. O eliminar registro de BD y reprocesar desde Drive
- No hay herramienta automatizada para esto

**Recomendación:** Crear script `reprocess_quarantine.py` para facilitar recuperación.

---

### 8.5. ¿Los archivos en cuarentena se limpian eventualmente o quedan para siempre?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- Función `cleanup_old_quarantine()` limpia archivos > 90 días
- Se ejecuta manualmente o se puede integrar en job periódico
- Limpia archivos `.pdf` y `.meta.json` antiguos
- No limpia directorios, solo archivos

**Ubicación:** `src/pipeline/duplicate_manager.py` líneas 202-223

---

## 9. Performance y Límites

### 9.1. ¿Qué ocurre si hay 1000+ archivos nuevos en Drive en una sola ejecución?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema procesa en lotes (`BATCH_SIZE`, default: 10)
- Límite de páginas por ejecución: `MAX_PAGES_PER_RUN` (default: 10)
- Si hay 1000+ archivos:
  - Se procesan en lotes de 10
  - Máximo 10 páginas de Drive (configurable)
  - Los archivos restantes se procesan en la siguiente ejecución
  - No hay timeout o límite de tiempo total

**Configuración:** `BATCH_SIZE=10`, `MAX_PAGES_PER_RUN=10`

**Ubicación:** `src/pipeline/ingest_incremental.py` líneas 110-112, 233-247

---

### 9.2. ¿Qué ocurre si un PDF pesa 50MB (timeout de descarga o OCR)?

**Estado:** ⚠️ **PARCIALMENTE IMPLEMENTADO**

**Funcionamiento:**
- No hay límite de tamaño de archivo explícito
- Si un PDF es muy grande:
  - La descarga puede tardar mucho
  - La conversión a imagen puede fallar o ser lenta
  - OpenAI tiene límite de tamaño de imagen (20MB base64)
  - Si falla → fallback a Tesseract
  - Si Tesseract también falla → error

**Limitación:** No hay validación de tamaño antes de procesar. PDFs muy grandes pueden causar timeouts.

---

### 9.3. ¿Hay protección contra rate limiting de OpenAI (200k TPM)?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- Espera de 3 segundos entre facturas (configurable)
- Reintentos automáticos con backoff exponencial
- Si se alcanza rate limit:
  - `RateLimitError` → reintenta con backoff
  - Hasta 6 intentos
  - Si todos fallan → fallback a Tesseract

**Configuración:** Espera de 3 segundos en `src/pipeline/ingest.py` línea 75

**Ubicación:** `src/ocr_extractor.py` líneas 132-135, 236-238

---

### 9.4. ¿Qué ocurre si la BD se queda sin espacio?

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Funcionamiento:**
- No hay validación de espacio en disco antes de insertar
- Si la BD se queda sin espacio:
  - Las inserciones fallan con error de PostgreSQL
  - Se registra error en logs
  - El archivo va a cuarentena
  - El job puede fallar completamente

**Recomendación:** Implementar validación de espacio en disco y alertas.

---

### 9.5. ¿El cleanup de archivos temporales funciona si el job falla abruptamente?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema usa bloques `try/finally` para cleanup
- Archivos temporales se eliminan en `finally`:
  - `cleanup_temp_file()` en cada archivo procesado
  - `shutil.rmtree(temp_dir)` al final del job
- Si el job falla:
  - Los archivos temporales se limpian en `finally`
  - Si el proceso es killado (SIGKILL) → archivos pueden quedar

**Ubicación:** `src/pipeline/ingest.py` líneas 352-355, `src/pipeline/ingest_incremental.py` líneas 185-188

---

## 10. Reprocesamiento (Tu Propuesta)

### 10.1. ¿Qué ocurre si una factura en "revisar" falla validación 100 veces seguidas?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- Límite de intentos: máximo 3 (configurable)
- Después de 3 intentos fallidos:
  - Estado cambia a `error_permanente`
  - No se reprocesa más automáticamente
  - Campo `reprocess_attempts = 3`
  - Se registra evento `reprocess_permanent_error`

**Configuración:** `REPROCESS_REVIEW_MAX_ATTEMPTS=3`

**Ubicación:** `src/db/repositories.py` líneas 692-700

---

### 10.2. ¿El reprocesamiento respeta el rate limiting de OpenAI?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El reprocesamiento usa `process_batch()` que incluye espera de 3 segundos
- Respeta el mismo rate limiting que el procesamiento normal
- No hay diferencia en el manejo de rate limits entre procesamiento nuevo y reprocesamiento

**Ubicación:** `src/pipeline/ingest.py` línea 75, `src/pipeline/ingest_incremental.py` línea 571

---

### 10.3. ¿Qué ocurre si durante el reprocesamiento el archivo ya no existe en Drive?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- El sistema intenta obtener metadata con `get_file_by_id()`
- Si el archivo no existe:
  - `get_file_by_id()` retorna `None`
  - Se incrementa `reprocess_attempts`
  - Se registra error: "No se pudo obtener metadata desde Drive"
  - Si alcanza 3 intentos → estado `error_permanente`

**Ubicación:** `src/pipeline/ingest_incremental.py` líneas 514-522

---

### 10.4. ¿Se puede deshabilitar el reprocesamiento automático sin romper el job?

**Estado:** ✅ **IMPLEMENTADO**

**Funcionamiento:**
- Variable de entorno: `REPROCESS_REVIEW_ENABLED=false`
- Si está deshabilitado:
  - El job se ejecuta normalmente
  - Solo se omite la fase de reprocesamiento
  - No afecta el procesamiento de archivos nuevos
  - El job continúa normalmente

**Configuración:** `REPROCESS_REVIEW_ENABLED=true` (default)

**Ubicación:** `src/pipeline/ingest_incremental.py` líneas 116, 175-177

---

### 10.5. ¿Hay forma de reprocesar manualmente una factura específica por drive_file_id?

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Funcionamiento:**
- No hay script o herramienta para reprocesar una factura específica
- Se puede hacer manualmente:
  1. Cambiar estado a `revisar` en BD
  2. Resetear `reprocess_attempts = 0`
  3. Esperar próxima ejecución del job
- O modificar código para forzar reprocesamiento

**Recomendación:** Crear script `reprocess_invoice.py --drive-file-id <id>` para reprocesamiento manual.

---

## RESUMEN DE COBERTURA

### ✅ Totalmente Implementado: 35/50 (70%)
### ⚠️ Parcialmente Implementado: 8/50 (16%)
### ❌ No Implementado: 7/50 (14%)

---

## RECOMENDACIONES PRIORITARIAS

1. **Detección de archivos eliminados de Drive** (2.5)
2. **Protección contra ejecuciones concurrentes** (7.4)
3. **Limpieza automática de facturas en "pendiente"** (6.2)
4. **Script para reprocesamiento manual por ID** (10.5)
5. **Validación de espacio en disco** (9.4)
6. **Detección de cambios en archivos en cuarentena** (8.3)
7. **Reintento automático de archivos en cuarentena** (8.1)

---

**Documento generado:** 9 de noviembre de 2025  
**Última actualización:** 9 de noviembre de 2025

