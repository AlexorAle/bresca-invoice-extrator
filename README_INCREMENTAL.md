# 📦 Sistema de Ingesta Incremental - Invoice Extractor

## 🎯 Descripción

Sistema **idempotente**, **tolerante a fallos** y **de bajo impacto** que detecta y procesa **solo las facturas nuevas o modificadas** desde Google Drive, evitando duplicados y reprocesamiento innecesario.

### Características Principales

✅ **Incremental**: Solo procesa archivos nuevos/modificados desde última sincronización  
✅ **Idempotente**: No reprocesa facturas ya ingresadas (deduplicación por hash)  
✅ **Tolerante a fallos**: Reintentos automáticos, quarantine para errores  
✅ **Bajo impacto**: Procesamiento en lotes con pausas configurables  
✅ **Monitoreable**: Logs JSON estructurados, métricas detalladas, auditoría completa  
✅ **Automático**: Compatible con cron para ejecución desatendida  

---

## 📊 Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                     Google Drive (Source)                        │
│                   Carpeta con PDFs de facturas                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ (1) Query incremental
                             │     modifiedTime > last_sync
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              DriveIncrementalClient                              │
│  • Paginación automática                                         │
│  • Reintentos con backoff exponencial                            │
│  • Rate limiting handling (429)                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ (2) Lotes de archivos
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           IncrementalIngestPipeline (Orchestrator)               │
│  • Descarga en lotes (BATCH_SIZE)                                │
│  • Pausa entre lotes (SLEEP_BETWEEN_BATCH_SEC)                   │
│  • Tracking de max_modified_time                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ (3) Procesamiento
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Ingest Pipeline (Existing)                    │
│  • OCR híbrido (Tesseract + LLM)                                 │
│  • Normalización de datos                                        │
│  • Deduplicación (hash_contenido + drive_file_id)                │
│  • Validación de reglas de negocio                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ (4) Persistencia
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PostgreSQL Database                        │
│  • facturas: datos extraídos                                     │
│  • ingest_events: auditoría completa                             │
│  • sync_state: último timestamp procesado                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ (5) Actualizar estado
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    StateStore (DB o File)                        │
│  • Guardar max_modified_time de archivos OK                      │
│  • Estrategia MAX_OK_TIME (segura)                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Aplicar Migración

```bash
bash scripts/apply_incremental_migration.sh
```

### 2. Configurar Variables

Agregar a `.env` (ver [ENV_CONFIG_INCREMENTAL.md](ENV_CONFIG_INCREMENTAL.md)):

```bash
# Mínimo requerido
SYNC_WINDOW_MINUTES=1440
BATCH_SIZE=10
STATE_BACKEND=db
ADVANCE_STRATEGY=MAX_OK_TIME
```

### 3. Validar (Dry Run)

```bash
python scripts/run_ingest_incremental.py --dry-run
```

### 4. Primera Ejecución

```bash
python scripts/run_ingest_incremental.py
```

### 5. Configurar Cron

```bash
crontab -e

# Ejecutar cada 30 minutos
*/30 * * * * cd /path/to/project && /path/to/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1
```

---

## 📁 Componentes Implementados

### Nuevos Módulos

| Archivo | Descripción |
|---------|-------------|
| `src/db/models.py` | Modelo `SyncState` agregado |
| `src/db/repositories.py` | `SyncStateRepository` para estado persistente |
| `src/sync/state_store.py` | Abstracción de almacenamiento (DB/File) |
| `src/drive/drive_incremental.py` | Cliente Drive con búsqueda incremental |
| `src/pipeline/ingest_incremental.py` | Pipeline orquestador principal |
| `scripts/run_ingest_incremental.py` | Script ejecutable (CLI) |
| `migrations/001_add_sync_state_table.sql` | Migración para tabla sync_state |

### Scripts Auxiliares

| Script | Uso |
|--------|-----|
| `scripts/apply_incremental_migration.sh` | Aplicar migración SQL |
| `scripts/run_ingest_incremental.py` | Ejecutar ingesta (manual o cron) |

### Documentación

| Documento | Contenido |
|-----------|-----------|
| `README_INCREMENTAL.md` | Este documento (overview) |
| `INCREMENTAL_SETUP_GUIDE.md` | Guía paso a paso de setup |
| `ENV_CONFIG_INCREMENTAL.md` | Configuración de variables de entorno |

---

## ⚙️ Configuración

### Variables Clave

#### Control de Flujo

- **`SYNC_WINDOW_MINUTES`** (default: 1440): Ventana de seguridad en minutos para retroceder el timestamp (evita pérdida de archivos por desfase de relojes)
- **`BATCH_SIZE`** (default: 10): Número de PDFs procesados simultáneamente en memoria
- **`SLEEP_BETWEEN_BATCH_SEC`** (default: 10): Pausa en segundos entre lotes (previene calentamiento)
- **`MAX_PAGES_PER_RUN`** (default: 10): Límite de páginas Drive API por ejecución

#### Estrategia de Avance

- **`ADVANCE_STRATEGY`** (default: MAX_OK_TIME):
  - **`MAX_OK_TIME`** ✅ Recomendado: Avanza al máximo modifiedTime de archivos procesados exitosamente
  - **`CURRENT_TIME`**: Avanza al timestamp actual (puede saltar archivos con errores)

#### Almacenamiento de Estado

- **`STATE_BACKEND`** (default: db):
  - **`db`** ✅ Recomendado: Usa tabla `sync_state` en PostgreSQL
  - **`file`**: Usa archivo JSON local (`STATE_FILE`)

#### Drive API

- **`DRIVE_PAGE_SIZE`** (default: 100): Archivos por página en resultados Drive
- **`DRIVE_RETRY_MAX`** (default: 5): Reintentos en caso de error
- **`DRIVE_RETRY_BASE_MS`** (default: 500): Tiempo base para backoff exponencial

Ver todas las variables en [ENV_CONFIG_INCREMENTAL.md](ENV_CONFIG_INCREMENTAL.md).

---

## 🔄 Flujo de Ejecución

### Secuencia Detallada

1. **Inicialización**
   - Cargar configuración desde `.env`
   - Validar acceso a Drive y DB
   - Obtener `last_sync_time` desde StateStore

2. **Búsqueda Incremental**
   - Calcular `adjusted_since_time = last_sync_time - SYNC_WINDOW_MINUTES`
   - Query Drive: `modifiedTime > adjusted_since_time`
   - Iterar páginas (máximo `MAX_PAGES_PER_RUN`)

3. **Procesamiento en Lotes**
   - Dividir archivos en lotes de `BATCH_SIZE`
   - Por cada lote:
     - Descargar a temp/
     - Extraer con OCR híbrido
     - Aplicar deduplicación
     - UPSERT en BD
     - Registrar en `ingest_events`
   - Pausa de `SLEEP_BETWEEN_BATCH_SEC` entre lotes

4. **Tracking de Progreso**
   - Mantener `max_modified_time_processed`
   - Solo actualizar con archivos procesados **exitosamente**

5. **Actualización de Estado**
   - Si hay archivos OK: `last_sync_time = max_modified_time_processed`
   - Si todos fallaron: NO actualizar (reintentar en próxima ejecución)

6. **Limpieza y Logs**
   - Eliminar archivos temporales
   - Generar resumen con métricas
   - Retornar exit code (0=ok, 2=errores parciales, 1=error crítico)

---

## 🛡️ Tolerancia a Fallos

### Reintentos Automáticos

- **Drive API**: Hasta `DRIVE_RETRY_MAX` reintentos con backoff exponencial
- **429 (Rate Limit)**: Espera automática con jitter
- **5xx (Server Error)**: Reintento con backoff

### Quarantine System

Archivos con errores se mueven a `data/quarantine/` con metadata:

```json
{
  "file_info": {...},
  "error": "ValueError: Invalid PDF format",
  "timestamp": "20251102_143022",
  "quarantined_at": "2025-11-02T14:30:22Z"
}
```

### Pending Queue

Facturas que requieren revisión manual → `data/pending/`:
- Duplicados ambiguos
- Validación de negocio fallida
- Campos críticos faltantes

### Estrategia MAX_OK_TIME

Solo avanza el timestamp con archivos **confirmados OK**. Archivos con error se reintentarán en la próxima ejecución.

**Ejemplo:**

```
Archivos procesados:
  - archivo1.pdf (modifiedTime: 10:00) → OK
  - archivo2.pdf (modifiedTime: 10:05) → ERROR
  - archivo3.pdf (modifiedTime: 10:10) → OK

Resultado:
  last_sync_time = 10:10  ← máximo de archivos OK
  archivo2.pdf se reintentará en próxima ejecución
```

---

## 📊 Métricas y Monitoreo

### Métricas en Logs JSON

```json
{
  "drive_items_listed_total": 47,
  "drive_pages_fetched_total": 1,
  "files_downloaded": 47,
  "download_errors": 0,
  "batch_errors": 0,
  "invoices_processed_ok_total": 42,
  "invoices_duplicate_total": 1,
  "invoices_revision_total": 2,
  "invoices_ignored_total": 0,
  "invoices_review_total": 1,
  "invoices_error_total": 1,
  "last_sync_time_before": "2025-11-01T10:00:00Z",
  "last_sync_time_after": "2025-11-02T09:45:23Z",
  "duration_seconds": 245.67
}
```

### Auditoría Completa

Tabla `ingest_events` registra cada paso:

```sql
SELECT 
  drive_file_id,
  etapa,
  nivel,
  decision,
  ts
FROM ingest_events
WHERE drive_file_id = 'abc123'
ORDER BY ts;
```

**Etapas trackeadas:**
- `ingest_start`, `download`, `validate`, `ocr`, `parse`
- `duplicate_check`, `db_upsert`, `ingest_complete`
- `ingest_error`, `revision_created`

---

## 🎛️ Opciones de CLI

```bash
python scripts/run_ingest_incremental.py [OPTIONS]
```

| Opción | Descripción |
|--------|-------------|
| `--dry-run` | Validar sin procesar archivos |
| `--folder-id ID` | Override de carpeta Drive |
| `--batch-size N` | Override de tamaño de lote |
| `--max-pages N` | Override de límite de páginas |
| `--sleep-between-batch N` | Override de pausa entre lotes |
| `--advance-strategy S` | Override de estrategia (MAX_OK_TIME\|CURRENT_TIME) |
| `--output-json FILE` | Guardar estadísticas en JSON |
| `--reset-state` | ⚠️ Resetear timestamp (forzar rescan) |

### Ejemplos

```bash
# Validar configuración
./scripts/run_ingest_incremental.py --dry-run

# Procesar solo 5 páginas (testing)
./scripts/run_ingest_incremental.py --max-pages 5

# Guardar métricas
./scripts/run_ingest_incremental.py --output-json results.json

# Resetear (reprocesar todo)
./scripts/run_ingest_incremental.py --reset-state
```

---

## 🔍 Deduplicación Multi-nivel

Sistema usa **3 estrategias** de deduplicación (ya existentes, no cambian):

### 1. Por `drive_file_id` (Constraint único)

Previene reprocesar mismo archivo Drive.

```sql
UNIQUE INDEX ON facturas(drive_file_id)
```

### 2. Por `hash_contenido` (Semantic hash)

Detecta facturas duplicadas con diferente `drive_file_id`:

```python
hash_contenido = sha256(
  f"{proveedor}|{numero_factura}|{fecha_emision}|{importe_total}"
)
```

```sql
UNIQUE INDEX ON facturas(hash_contenido) WHERE hash_contenido IS NOT NULL
```

### 3. Por lógica de negocio

Detecta conflictos:
- Mismo proveedor + número pero diferente importe
- Misma factura en diferentes carpetas

---

## 📈 Casos de Uso

### Ejecución Desatendida (Cron)

**Setup típico en producción:**

```bash
# Cada 30 minutos
*/30 * * * * cd /path/to/project && /path/to/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1
```

**Ventajas:**
- Latencia baja (facturas disponibles ~30 min después de subir a Drive)
- Sin intervención manual
- Recuperación automática de errores transitorios

### Ejecución Manual

**Para testing, debugging o cargas puntuales:**

```bash
# Seca (sin procesar)
python scripts/run_ingest_incremental.py --dry-run

# Real con límite
python scripts/run_ingest_incremental.py --max-pages 3

# Con output JSON
python scripts/run_ingest_incremental.py --output-json results.json
```

### Carga Inicial (Primera Vez)

**Si tienes muchos archivos históricos:**

```bash
# 1. Configurar ventana amplia (30 días)
# En .env:
SYNC_WINDOW_MINUTES=43200

# 2. Ejecutar con límites conservadores
python scripts/run_ingest_incremental.py --batch-size 5 --max-pages 10

# 3. Repetir hasta procesar todos (o dejar en cron)
```

### Re-procesamiento Selectivo

**Si necesitas reprocesar todo:**

```bash
# CUIDADO: Esto forzará reprocesar archivos en SYNC_WINDOW
python scripts/run_ingest_incremental.py --reset-state
```

---

## 🧪 Testing

### Test de Configuración

```bash
# Validar sin ejecutar
./scripts/run_ingest_incremental.py --dry-run
```

### Test de Conexión Drive

```bash
# Script existente
python scripts/test_connection.py
```

### Test de Base de Datos

```bash
# Verificar tabla sync_state
psql $DATABASE_URL -c "\d sync_state"
psql $DATABASE_URL -c "SELECT * FROM sync_state;"
```

### Test End-to-End

```bash
# Procesar solo 1 página (máx ~100 archivos)
python scripts/run_ingest_incremental.py --max-pages 1

# Verificar resultados
psql $DATABASE_URL -c "SELECT estado, COUNT(*) FROM facturas GROUP BY estado;"
```

---

## 📚 Documentación Completa

| Documento | Descripción |
|-----------|-------------|
| **[INCREMENTAL_SETUP_GUIDE.md](INCREMENTAL_SETUP_GUIDE.md)** | Guía paso a paso de instalación y setup |
| **[ENV_CONFIG_INCREMENTAL.md](ENV_CONFIG_INCREMENTAL.md)** | Todas las variables de entorno con ejemplos |
| **[migrations/001_add_sync_state_table.sql](migrations/001_add_sync_state_table.sql)** | Script SQL de migración |

---

## 🤝 Integración con Sistema Existente

El sistema incremental **no modifica** componentes existentes:

✅ **Reutiliza:**
- `ocr_extractor.py`: Arquitectura híbrida (Tesseract + LLM)
- `parser_normalizer.py`: Normalización de datos
- `duplicate_manager.py`: Detección de duplicados
- `pipeline/ingest.py`: Procesamiento batch
- Toda la lógica de validación y BD

✅ **Agrega:**
- Búsqueda incremental en Drive (solo nuevos/modificados)
- Tracking de último timestamp procesado
- Orquestación para ejecución desatendida

---

## 🎓 Mejores Prácticas

### Configuración Recomendada

```bash
# Producción (servidor con buenos recursos)
BATCH_SIZE=10
SLEEP_BETWEEN_BATCH_SEC=10
MAX_PAGES_PER_RUN=10
ADVANCE_STRATEGY=MAX_OK_TIME
STATE_BACKEND=db
```

### Monitoreo

1. **Logs**: Revisar `logs/extractor.log` y `logs/cron.log` periódicamente
2. **Métricas**: Trackear tasa de errores, duración, throughput
3. **Alertas**: Configurar alertas si `invoices_error_total` > 10%
4. **Auditoría**: Consultar `ingest_events` para investigar issues

### Mantenimiento

- **Cuarentena**: Revisar `data/quarantine/` semanalmente
- **Pending**: Procesar manualmente archivos en `data/pending/`
- **Logs**: Rotación automática (configurable en `logging_conf.py`)
- **Estado**: Backup periódico de tabla `sync_state`

---

## 🚨 Troubleshooting

Ver [INCREMENTAL_SETUP_GUIDE.md § Troubleshooting](INCREMENTAL_SETUP_GUIDE.md#-troubleshooting) para:

- Error: "No se puede acceder a carpeta Drive"
- Error: "Rate limit exceeded (429)"
- Archivos no se procesan (siempre 0)
- Consumo alto de RAM/CPU
- Y más...

---

## 📄 Licencia

Este componente forma parte del sistema Invoice Extractor.

---

## 👥 Contribuciones

Ver documento principal `README.md` del proyecto.

---

**¡Sistema incremental listo para producción! 🚀**

Para cualquier duda, consultar la [Guía de Setup](INCREMENTAL_SETUP_GUIDE.md) o los logs del sistema.

