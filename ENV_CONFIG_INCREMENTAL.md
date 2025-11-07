# Configuración de Variables de Entorno - Ingesta Incremental

Este documento describe las nuevas variables de entorno necesarias para el sistema de **ingesta incremental** (Pull) desde Google Drive.

## Variables Requeridas (ya existentes)

Estas variables ya deberían estar configuradas en tu archivo `.env`:

```bash
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/invoice_db

# Google Drive
GOOGLE_SERVICE_ACCOUNT_FILE=/ruta/absoluta/keys/service_account.json
GOOGLE_DRIVE_FOLDER_ID=1abc123xyz456...
```

## Nuevas Variables - Ingesta Incremental

Agregar estas variables al archivo `.env`:

### Control de Ingesta

```bash
# Ventana de seguridad al retroceder (minutos)
# Buffer para evitar perder cambios por desfase de relojes entre sistemas
# Default: 1440 (24 horas)
SYNC_WINDOW_MINUTES=1440

# Archivos PDF por lote en memoria
# Valores muy altos pueden consumir mucha RAM durante OCR
# Default: 10
BATCH_SIZE=10

# Pausa entre lotes (segundos)
# Previene saturación de CPU/OCR y calentamiento del sistema
# Default: 10
SLEEP_BETWEEN_BATCH_SEC=10

# Límite de páginas de Drive API por ejecución
# Cada página contiene hasta DRIVE_PAGE_SIZE archivos
# Útil para limitar ejecuciones largas en cron
# Default: 10
MAX_PAGES_PER_RUN=10

# Estrategia para avanzar last_sync_time
# - MAX_OK_TIME: usar máximo modifiedTime de archivos procesados OK (RECOMENDADO)
# - CURRENT_TIME: usar tiempo actual (menos segura, puede saltar archivos con errores)
# Default: MAX_OK_TIME
ADVANCE_STRATEGY=MAX_OK_TIME
```

### Almacenamiento de Estado

```bash
# Backend para guardar estado de sincronización
# - db: base de datos (RECOMENDADO, requiere tabla sync_state)
# - file: archivo JSON local (útil para desarrollo/testing)
# Default: db
STATE_BACKEND=db

# Ruta del archivo de estado (solo si STATE_BACKEND=file)
# Se creará automáticamente si no existe
# Default: state/last_sync.json
STATE_FILE=state/last_sync.json
```

### Google Drive API - Límites y Reintentos

```bash
# Tamaño de página para consultas Drive API
# Número de archivos por página en resultados
# Default: 100
DRIVE_PAGE_SIZE=100

# Máximo de reintentos para llamadas Drive (en caso de rate limits o errores)
# Default: 5
DRIVE_RETRY_MAX=5

# Base de tiempo para backoff exponencial (milisegundos)
# Tiempo de espera inicial antes de reintentar (crece exponencialmente)
# Default: 500
DRIVE_RETRY_BASE_MS=500
```

### Directorios

```bash
# Directorio de cuarentena para archivos problemáticos
# Se crearán subdirectorios por tipo de error
# Default: data/quarantine
QUARANTINE_DIR=data/quarantine

# Directorio de archivos pendientes de revisión manual
# Default: data/pending
PENDING_DIR=data/pending
```

### Logging

```bash
# Nivel de logging: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Para debugging usar DEBUG, para producción INFO o WARNING
# Default: INFO
LOG_LEVEL=INFO

# Ruta del archivo de log (con rotación automática)
# Default: logs/extractor.log
LOG_PATH=logs/extractor.log

# Formato de logs: true para JSON, false para texto
# JSON es mejor para parsing/análisis automático
# Default: true
LOG_JSON=true
```

## Archivo .env Completo - Ejemplo

```bash
# =============================================================================
# BASE DE DATOS
# =============================================================================
DATABASE_URL=postgresql://invoice_user:SecurePass123@localhost:5432/invoice_db

# =============================================================================
# GOOGLE DRIVE
# =============================================================================
GOOGLE_SERVICE_ACCOUNT_FILE=/home/user/proyectos/invoice-extractor/keys/service_account.json
GOOGLE_DRIVE_FOLDER_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ123456

# =============================================================================
# INGESTA INCREMENTAL
# =============================================================================
SYNC_WINDOW_MINUTES=1440
BATCH_SIZE=10
SLEEP_BETWEEN_BATCH_SEC=10
MAX_PAGES_PER_RUN=10
ADVANCE_STRATEGY=MAX_OK_TIME

STATE_BACKEND=db
STATE_FILE=state/last_sync.json

DRIVE_PAGE_SIZE=100
DRIVE_RETRY_MAX=5
DRIVE_RETRY_BASE_MS=500

# =============================================================================
# DIRECTORIOS
# =============================================================================
QUARANTINE_DIR=data/quarantine
PENDING_DIR=data/pending

# =============================================================================
# LOGGING
# =============================================================================
LOG_LEVEL=INFO
LOG_PATH=logs/extractor.log
LOG_JSON=true

# =============================================================================
# OCR (ya existentes)
# =============================================================================
OLLAMA_MODEL=llama3.2
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_TIMEOUT=60
TESSERACT_LANG=spa
EXTRACTION_STRATEGY=hybrid
```

## Configuración de Cron

Para ejecutar la ingesta incremental automáticamente, agregar a crontab:

```bash
# Editar crontab
crontab -e

# Ejecutar cada 30 minutos
*/30 * * * * cd /home/user/proyectos/invoice-extractor && /home/user/proyectos/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1

# Ejecutar cada hora (minuto 0)
0 * * * * cd /home/user/proyectos/invoice-extractor && /home/user/proyectos/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1

# Ejecutar cada 4 horas
0 */4 * * * cd /home/user/proyectos/invoice-extractor && /home/user/proyectos/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1

# Ejecutar una vez al día a las 2 AM
0 2 * * * cd /home/user/proyectos/invoice-extractor && /home/user/proyectos/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1
```

## Verificar Configuración

Antes de ejecutar, verificar que todo esté configurado correctamente:

```bash
# Ejecutar en modo dry-run (no procesa, solo valida)
python scripts/run_ingest_incremental.py --dry-run
```

## Troubleshooting

### Error: "GOOGLE_DRIVE_FOLDER_ID no configurado"
- Verificar que la variable esté en `.env` y sea el ID correcto de la carpeta
- El ID se ve en la URL de Drive: `https://drive.google.com/drive/folders/[ESTE_ES_EL_ID]`

### Error: "DATABASE_URL no configurada"
- Verificar conexión a PostgreSQL
- Formato correcto: `postgresql://user:pass@host:port/dbname`

### Error: "Archivo de service account no encontrado"
- Verificar que `GOOGLE_SERVICE_ACCOUNT_FILE` apunte a la ruta correcta
- Usar **ruta absoluta**, no relativa

### Reintentos constantes (429 errors)
- Drive está limitando tus requests (rate limit)
- Aumentar `DRIVE_RETRY_BASE_MS` a 1000 o más
- Reducir `DRIVE_PAGE_SIZE` a 50
- Aumentar `SLEEP_BETWEEN_BATCH_SEC` a 15-20

### Consumo alto de RAM
- Reducir `BATCH_SIZE` a 5 o menos
- Reducir `MAX_PAGES_PER_RUN` para ejecuciones más cortas

## Monitoreo

Ver logs en tiempo real:

```bash
# Logs generales
tail -f logs/extractor.log

# Logs de cron
tail -f logs/cron.log

# Ver último timestamp de sincronización (si STATE_BACKEND=file)
cat state/last_sync.json

# Ver último timestamp de sincronización (si STATE_BACKEND=db)
psql $DATABASE_URL -c "SELECT * FROM sync_state WHERE key = 'drive_last_sync_time';"
```

