# Propuesta de Mejora: Sistema de Reprocesamiento Automático de Facturas

**Fecha:** 9 de noviembre de 2025  
**Contexto:** Sistema de extracción de facturas desde Google Drive con OCR (OpenAI GPT-4o-mini)

---

## 1. SITUACIÓN ACTUAL DEL SISTEMA

### 1.1 Arquitectura General

- **Fuente de datos:** Google Drive (PDFs organizados por carpetas/meses)
- **Procesamiento:** Pipeline incremental que se ejecuta cada 6 horas vía cron
- **OCR:** OpenAI GPT-4o-mini Vision API (extracción estructurada)
- **Base de datos:** PostgreSQL con SQLAlchemy ORM
- **Estados de facturas:** `procesado`, `pendiente`, `error`, `revisar`, `duplicado`

### 1.2 Flujo de Procesamiento Actual

```
1. Job incremental busca archivos nuevos/modificados en Drive (desde último sync_time)
2. Descarga PDFs a directorio temporal (temp/)
3. Extrae datos con OpenAI OCR
4. Normaliza datos (fechas, importes, etc.)
5. Valida reglas de negocio
6. Detecta duplicados
7. Inserta/actualiza en BD (UPSERT por drive_file_id)
8. Elimina archivos temporales (cleanup)
```

### 1.3 Gestión de Archivos

- **PDFs:** Se descargan temporalmente a `temp/` y se eliminan después del procesamiento
- **No se almacenan localmente:** Los PDFs solo existen en Google Drive
- **Cuarentena:** Archivos problemáticos se mueven a `data/quarantine/` con metadata JSON
- **Pending:** Facturas que requieren revisión se guardan en `data/pending/` como JSON

### 1.4 Sistema de Detección de Duplicados

El sistema usa `DuplicateManager` que decide acciones basándose en:

1. **Por drive_file_id:** Si existe → `IGNORE` (no procesa)
2. **Por hash_contenido:** Si existe → `DUPLICATE` (mover a cuarentena)
3. **Por proveedor + número:** Si existe con distinto importe → `REVIEW` (marcar revisar)
4. **Sin duplicados:** → `INSERT` (nueva factura)

**Problema actual:** Si una factura ya está en BD (incluso en estado "revisar"), el sistema la ignora completamente en ejecuciones futuras.

---

## 2. PROBLEMA IDENTIFICADO

### 2.1 Bug en Validación

**Ubicación:** `src/pipeline/validate.py` línea 83

**Problema:** La función `validate_business_rules()` intentaba parsear `fecha_emision` como string usando `datetime.fromisoformat()`, pero el campo ya llega como objeto `date` desde `parser_normalizer.py` (línea 225).

**Impacto:**
- 73 facturas quedaron en estado `revisar` incorrectamente
- Todas tienen datos válidos de OpenAI (proveedor, fecha, importe)
- La validación fallaba por tipo incorrecto, no por datos inválidos

**Corrección aplicada:**
```python
# ANTES (línea 83):
fecha_obj = datetime.fromisoformat(fecha_emision)  # ❌ Falla si es date object

# DESPUÉS:
if isinstance(fecha_emision, date):
    fecha_obj = datetime.combine(fecha_emision, datetime.min.time())
elif isinstance(fecha_emision, datetime):
    fecha_obj = fecha_emision
elif isinstance(fecha_emision, str):
    fecha_obj = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
```

### 2.2 Falta de Reprocesamiento

**Problema:** No existe mecanismo para reprocesar facturas en estado `revisar`:

- El job incremental solo busca archivos nuevos/modificados en Drive
- Si una factura ya está en BD (cualquier estado), se ignora por `drive_file_id`
- Las 73 facturas afectadas por el bug permanecerán en "revisar" indefinidamente
- No hay forma automática de reintentar procesamiento después de corregir bugs

---

## 3. REQUERIMIENTOS Y RESTRICCIONES

### 3.1 Restricciones Técnicas

- **No almacenar PDFs localmente:** Los PDFs solo existen en Google Drive
- **Drive es fuente de verdad:** Siempre descargar desde Drive cuando se necesite reprocesar
- **UPSERT en BD:** El sistema usa `INSERT ON CONFLICT UPDATE` por `drive_file_id`
- **Validación corregida:** El bug ya está corregido, solo falta reprocesar

### 3.2 Requerimientos Funcionales

1. **Reprocesamiento automático:** El job debe detectar y reprocesar facturas en "revisar"
2. **Límite temporal:** Solo reprocesar facturas recientes (ej: últimos 30 días) para evitar loops infinitos
3. **Reutilizar código existente:** Usar `process_batch()` y componentes actuales
4. **No duplicar lógica:** Integrar en el flujo existente del job incremental
5. **Eficiencia:** No descargar/reprocesar facturas que ya están correctas

### 3.3 Consideraciones de Negocio

- **Facturas antiguas:** Pueden estar en "revisar" por razones legítimas (no solo bugs)
- **Rate limiting:** OpenAI tiene límites (200,000 TPM), no sobrecargar
- **Costo:** Cada reprocesamiento consume tokens de OpenAI
- **Auditoría:** Mantener trazabilidad de reprocesamientos

---

## 4. PROPUESTA DE IMPLEMENTACIÓN

### 4.1 Enfoque Propuesto

**Integrar reprocesamiento en el job incremental existente:**

1. **Al inicio del job** (después de buscar archivos nuevos en Drive):
   - Consultar BD por facturas en estado `revisar` de los últimos N días
   - Obtener sus `drive_file_id` y metadata

2. **Para cada factura a reprocesar:**
   - Descargar PDF desde Drive usando `drive_file_id`
   - Reprocesar con `process_batch()` (reutiliza código existente)
   - El UPSERT actualizará el estado si pasa validación

3. **Límites y controles:**
   - Configurable: `REPROCESS_REVIEW_MAX_DAYS=30` (solo últimas 30 días)
   - Configurable: `REPROCESS_REVIEW_MAX_COUNT=50` (máximo por ejecución)
   - Registrar evento de auditoría: `reprocess_attempt`

### 4.2 Cambios Necesarios

#### 4.2.1 Nuevo método en `FacturaRepository`

```python
def get_facturas_para_reprocesar(
    self, 
    estado: str = 'revisar',
    max_dias: int = 30,
    limite: int = 50
) -> List[dict]:
    """
    Obtener facturas que requieren reprocesamiento
    
    Args:
        estado: Estado de facturas a buscar
        max_dias: Solo facturas de últimos N días
        limite: Máximo de facturas a retornar
    
    Returns:
        Lista de facturas con drive_file_id y metadata necesaria
    """
```

#### 4.2.2 Modificación en `DriveClient`

```python
def get_file_by_id(self, file_id: str) -> dict:
    """
    Obtener metadata de archivo por ID (para reprocesamiento)
    
    Args:
        file_id: drive_file_id de la factura
    
    Returns:
        Diccionario con metadata del archivo (compatible con process_batch)
    """
```

#### 4.2.3 Integración en `IncrementalIngestPipeline`

```python
def _reprocess_review_invoices(self, db: Database, drive_client: DriveClient):
    """
    Reprocesar facturas en estado 'revisar'
    
    Lógica:
    1. Consultar BD por facturas en 'revisar' (últimos 30 días)
    2. Para cada una, descargar desde Drive
    3. Reprocesar con process_batch()
    4. El UPSERT actualizará estado si pasa validación
    """
```

### 4.3 Flujo Propuesto

```
Job Incremental:
├─ 1. Buscar archivos nuevos/modificados en Drive (actual)
├─ 2. Reprocesar facturas en "revisar" (NUEVO)
│   ├─ Consultar BD: facturas en "revisar" (últimos 30 días)
│   ├─ Para cada factura:
│   │   ├─ Descargar PDF desde Drive (drive_file_id)
│   │   ├─ Reprocesar con process_batch()
│   │   └─ UPSERT actualiza estado si pasa validación
│   └─ Registrar estadísticas de reprocesamiento
└─ 3. Procesar archivos nuevos (actual)
```

### 4.4 Ventajas de Esta Propuesta

✅ **Automático:** Se ejecuta en cada run del job  
✅ **Eficiente:** Solo reprocesa facturas recientes  
✅ **Reutiliza código:** Usa `process_batch()` existente  
✅ **No guarda PDFs:** Descarga desde Drive cuando se necesita  
✅ **Configurable:** Límites ajustables vía variables de entorno  
✅ **Auditable:** Registra eventos de reprocesamiento  
✅ **Seguro:** Límites previenen loops infinitos  

### 4.5 Variables de Entorno Propuestas

```env
# Reprocesamiento de facturas en revisar
REPROCESS_REVIEW_ENABLED=true
REPROCESS_REVIEW_MAX_DAYS=30
REPROCESS_REVIEW_MAX_COUNT=50
REPROCESS_REVIEW_ONLY_RECENT=true  # Solo facturas procesadas recientemente
```

---

## 5. ALTERNATIVAS CONSIDERADAS

### 5.1 Opción A: Script Manual Separado

**Descripción:** Script independiente para reprocesar facturas manualmente

**Pros:**
- Control total sobre cuándo reprocesar
- No afecta el job automático

**Contras:**
- Requiere ejecución manual
- No se integra con el flujo automático
- Más mantenimiento

**Decisión:** ❌ No recomendado (requiere intervención manual)

---

### 5.2 Opción B: Guardar PDFs Localmente

**Descripción:** Mantener copia local de PDFs para reprocesamiento rápido

**Pros:**
- Reprocesamiento más rápido (sin descarga)
- Menos llamadas a Drive API

**Contras:**
- Consume espacio en disco
- Puede desincronizarse con Drive
- Duplicación de datos
- Complejidad de gestión de archivos

**Decisión:** ❌ No recomendado (Drive es fuente de verdad)

---

### 5.3 Opción C: Reprocesamiento Automático en Job (PROPUESTA)

**Descripción:** Integrar reprocesamiento en el job incremental

**Pros:**
- Automático y transparente
- Reutiliza código existente
- No requiere almacenamiento adicional
- Configurable y seguro

**Contras:**
- Aumenta tiempo de ejecución del job
- Consume más recursos (descargas, OCR)

**Decisión:** ✅ **RECOMENDADO**

---

## 6. DETALLES TÉCNICOS ADICIONALES

### 6.1 Estructura de Base de Datos

**Tabla `facturas`:**
- `drive_file_id` (TEXT, UNIQUE, NOT NULL) - ID único en Drive
- `estado` (TEXT) - Valores: 'procesado', 'pendiente', 'error', 'revisar', 'duplicado'
- `creado_en` (TIMESTAMPTZ) - Fecha de creación
- `actualizado_en` (TIMESTAMPTZ) - Última actualización
- `error_msg` (TEXT) - Mensaje de error si aplica

**Tabla `ingest_events`:**
- Registra todos los eventos del pipeline
- Incluye: `drive_file_id`, `etapa`, `nivel`, `detalle`, `ts`

### 6.2 Componentes Clave del Sistema

**`process_batch()`** (`src/pipeline/ingest.py`):
- Función principal de procesamiento
- Acepta lista de archivos con `local_path`
- Retorna estadísticas de procesamiento
- Maneja duplicados, validación, y UPSERT

**`DuplicateManager`** (`src/pipeline/duplicate_manager.py`):
- Decide acción basándose en duplicados
- Retorna: `INSERT`, `IGNORE`, `DUPLICATE`, `REVIEW`, `UPDATE_REVISION`

**`validate_business_rules()`** (`src/pipeline/validate.py`):
- Valida reglas de negocio
- Retorna `True` si pasa, `False` si falla
- **Ya corregido** para manejar tipos de fecha correctamente

### 6.3 Flujo de Datos

```
OpenAI OCR → string ISO (YYYY-MM-DD)
    ↓
parser_normalizer → date object
    ↓
validate_business_rules → valida date/datetime/string ✅ (corregido)
    ↓
UPSERT en BD → almacena como DATE
```

### 6.4 Consideraciones de Performance

- **Rate limiting OpenAI:** 200,000 TPM (tokens por minuto)
- **Tiempo por factura:** ~3-5 segundos (descarga + OCR + validación)
- **Límite propuesto:** 50 facturas por ejecución = ~4 minutos adicionales
- **Frecuencia job:** Cada 6 horas (suficiente para no saturar)

---

## 7. CASOS DE USO

### 7.1 Caso Actual (Bug Corregido)

**Situación:** 73 facturas en "revisar" por bug de validación

**Con reprocesamiento automático:**
- Job siguiente ejecución detecta las 73 facturas
- Reprocesa automáticamente (límite: 50 por ejecución)
- Primera ejecución: 50 facturas → estado "procesado"
- Segunda ejecución: 23 facturas restantes → estado "procesado"
- Total: 2 ejecuciones del job (12 horas)

**Sin reprocesamiento automático:**
- Requiere intervención manual
- Script SQL para actualizar estado
- O reprocesamiento manual archivo por archivo

### 7.2 Caso Futuro (Nuevos Bugs)

**Situación:** Bug en validación detectado y corregido

**Con reprocesamiento automático:**
- Corregir código
- Job siguiente ejecución reprocesa automáticamente
- Sin intervención manual

**Sin reprocesamiento automático:**
- Requiere script manual o intervención DBA

### 7.3 Caso de Validaciones Legítimas

**Situación:** Factura en "revisar" por razón legítima (ej: datos faltantes)

**Comportamiento:**
- Reprocesamiento intenta validar nuevamente
- Si sigue fallando → permanece en "revisar"
- Si ahora pasa (ej: se corrigió bug) → cambia a "procesado"
- Límite de 30 días evita reprocesar facturas muy antiguas

---

## 8. PREGUNTAS PARA EVALUACIÓN

1. **¿Es correcto reprocesar automáticamente facturas en "revisar"?**
   - Considerar: facturas legítimamente problemáticas vs. bugs temporales

2. **¿Cuál es el límite temporal adecuado?**
   - Propuesta: 30 días
   - Alternativas: 7 días, 60 días, configurable

3. **¿Debe haber límite de cantidad por ejecución?**
   - Propuesta: 50 facturas
   - Alternativas: Sin límite, 100, 20

4. **¿Debe haber límite de intentos por factura?**
   - Propuesta: No (reprocesa hasta que pase o expire límite temporal)
   - Alternativa: Máximo 3 intentos, luego marcar como "error_permanente"

5. **¿Debe integrarse en job incremental o ser job separado?**
   - Propuesta: Integrado en job incremental
   - Alternativa: Job separado con frecuencia diferente

6. **¿Qué hacer con facturas que fallan validación legítimamente?**
   - Opción A: Reprocesar indefinidamente (riesgo de loop)
   - Opción B: Máximo N intentos, luego marcar como "error_permanente"
   - Opción C: Solo reprocesar si `error_msg` contiene ciertos patrones

---

## 9. INFORMACIÓN ADICIONAL

### 9.1 Estado Actual del Sistema

- **Total facturas en BD:** 73
- **Facturas en "revisar":** 73 (100%)
- **Facturas en "procesado":** 0
- **Facturas en "error":** 0
- **Última factura procesada:** 8 de noviembre de 2025
- **Job activo:** Sí (cron cada 6 horas)

### 9.2 Datos de Facturas en "revisar"

- **Todas tienen:** `proveedor_text`, `fecha_emision`, `importe_total`
- **Todas tienen:** `extractor='openai'`, `confianza='alta'`
- **Todas tienen:** `error_msg=' | Validación de negocio falló'`
- **Causa:** Bug en validación de fecha (ya corregido)

### 9.3 Configuración Actual

- **Job incremental:** `scripts/run_ingest_incremental.py`
- **Cron:** `0 */6 * * *` (cada 6 horas)
- **Variables relevantes:**
  - `SYNC_WINDOW_MINUTES=1440` (24 horas)
  - `BATCH_SIZE=10`
  - `MAX_PAGES_PER_RUN=10`

---

## 10. CONCLUSIÓN

**Problema:** 73 facturas en estado "revisar" por bug de validación (ya corregido). No existe mecanismo para reprocesarlas automáticamente.

**Propuesta:** Integrar reprocesamiento automático en el job incremental que:
- Detecta facturas en "revisar" de últimos 30 días
- Las descarga desde Drive y reprocesa
- Actualiza estado automáticamente si pasan validación
- Tiene límites configurables para evitar loops

**Ventajas:** Automático, eficiente, reutiliza código, no requiere almacenamiento adicional.

**Pregunta clave:** ¿Esta es la mejor práctica o hay alternativas mejores para este caso de uso?

---

**Documento preparado para evaluación por IA externa**  
**Fecha:** 9 de noviembre de 2025

