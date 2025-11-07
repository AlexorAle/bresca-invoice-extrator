# 📦 Guía de Setup - Sistema de Ingesta Incremental

Esta guía te ayudará a configurar y poner en marcha el **sistema de ingesta incremental** desde Google Drive.

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación Paso a Paso](#instalación-paso-a-paso)
3. [Configuración](#configuración)
4. [Primera Ejecución](#primera-ejecución)
5. [Configurar Cron](#configurar-cron)
6. [Troubleshooting](#troubleshooting)
7. [Comandos Útiles](#comandos-útiles)

---

## ✅ Requisitos Previos

Antes de comenzar, asegúrate de tener:

- [x] PostgreSQL instalado y corriendo
- [x] Base de datos creada y `DATABASE_URL` configurada en `.env`
- [x] Google Service Account con acceso a Drive (archivo JSON)
- [x] Python 3.8+ con virtualenv activado
- [x] Dependencias instaladas (`pip install -r requirements.txt`)
- [x] Sistema OCR existente funcionando (Tesseract + Ollama)

---

## 🚀 Instalación Paso a Paso

### Paso 1: Aplicar Migración de Base de Datos

La ingesta incremental requiere una nueva tabla `sync_state` para trackear el último timestamp de sincronización.

```bash
# Opción A: Script automático (recomendado)
bash scripts/apply_incremental_migration.sh

# Opción B: Manual con psql
psql $DATABASE_URL -f migrations/001_add_sync_state_table.sql
```

**Verificar que la tabla fue creada:**

```bash
psql $DATABASE_URL -c "\d sync_state"
```

Deberías ver:

```
                Table "public.sync_state"
   Column    |           Type           | Modifiers
-------------+--------------------------+-----------
 key         | text                     | not null
 value       | text                     | not null
 updated_at  | timestamp with time zone | default now()
```

### Paso 2: Configurar Variables de Entorno

Agregar las nuevas variables al archivo `.env`. Ver [ENV_CONFIG_INCREMENTAL.md](ENV_CONFIG_INCREMENTAL.md) para detalles completos.

**Mínimo requerido:**

```bash
# Agregar a .env:

# Ingesta incremental
SYNC_WINDOW_MINUTES=1440
BATCH_SIZE=10
SLEEP_BETWEEN_BATCH_SEC=10
MAX_PAGES_PER_RUN=10
ADVANCE_STRATEGY=MAX_OK_TIME

# Estado
STATE_BACKEND=db

# Drive API
DRIVE_PAGE_SIZE=100
DRIVE_RETRY_MAX=5
DRIVE_RETRY_BASE_MS=500

# Directorios
QUARANTINE_DIR=data/quarantine
PENDING_DIR=data/pending
```

### Paso 3: Crear Directorios

```bash
mkdir -p data/quarantine data/pending state logs
```

### Paso 4: Hacer Script Ejecutable

```bash
chmod +x scripts/run_ingest_incremental.py
chmod +x scripts/apply_incremental_migration.sh
```

---

## ⚙️ Configuración

### Configuración por Defecto (Recomendada)

La configuración por defecto está optimizada para:
- Ejecuciones cada 30-60 minutos desde cron
- Servidor con recursos moderados (8GB RAM, 4 cores)
- Procesar ~100-500 facturas por día

### Ajustar para Alto Volumen

Si procesas **muchas facturas** (>1000/día):

```bash
BATCH_SIZE=20                # Más archivos por lote
MAX_PAGES_PER_RUN=20         # Más páginas por ejecución
SLEEP_BETWEEN_BATCH_SEC=5    # Menos pausa entre lotes
DRIVE_PAGE_SIZE=200          # Más archivos por página API
```

### Ajustar para Recursos Limitados

Si el servidor tiene **pocos recursos** (<4GB RAM):

```bash
BATCH_SIZE=5                 # Menos archivos en memoria
MAX_PAGES_PER_RUN=5          # Menos páginas por run
SLEEP_BETWEEN_BATCH_SEC=15   # Más pausa para CPU
```

### Ajustar para Primera Carga Masiva

Si es la **primera ejecución** con muchos archivos históricos:

```bash
SYNC_WINDOW_MINUTES=43200    # 30 días hacia atrás
MAX_PAGES_PER_RUN=50         # Procesar más archivos
BATCH_SIZE=5                 # Pero en lotes pequeños
```

---

## 🎯 Primera Ejecución

### 1. Validar Configuración (Dry Run)

**Siempre ejecutar primero en modo dry-run:**

```bash
python scripts/run_ingest_incremental.py --dry-run
```

Esto validará:
- ✅ Variables de entorno configuradas
- ✅ Acceso a Google Drive
- ✅ Conexión a base de datos
- ✅ Número de archivos a procesar

**Salida esperada:**

```
================================================================================
  🚀 INGESTA INCREMENTAL - GOOGLE DRIVE
================================================================================

⏰ Inicio: 2025-11-02T10:00:00Z
💻 Host: server-prod

================================================================================
  VALIDACIÓN DE CONFIGURACIÓN
================================================================================

✅ GOOGLE_SERVICE_ACCOUNT_FILE: /path/to/keys/service_account.json
✅ GOOGLE_DRIVE_FOLDER_ID: 1aBcDeFgHiJkLmNoPqRsTuV...
✅ DATABASE_URL: postgresql://invoice_user@localhost...
✅ STATE_BACKEND: db

✅ Configuración válida

================================================================================
  DRY RUN - INFORMACIÓN
================================================================================

📁 Carpeta objetivo: 1aBcDeFgHiJkLmNoPqRsTuV
⏰ Última sincronización: N/A (primera ejecución)
📦 Tamaño de lote: 10
📄 Máximo de páginas: 10
⏱️  Pausa entre lotes: 10s
🔄 Estrategia de avance: MAX_OK_TIME

🔍 Validando acceso a carpeta...
✅ Acceso validado

🔍 Contando archivos a procesar...
📊 Archivos a procesar: 47

ℹ️  Dry run completado. No se procesaron archivos.
```

### 2. Primera Ejecución Real

Si el dry-run fue exitoso:

```bash
python scripts/run_ingest_incremental.py
```

**Monitorear en tiempo real:**

```bash
# En otra terminal
tail -f logs/extractor.log | grep -E 'INFO|ERROR|WARNING'
```

### 3. Verificar Resultados

Al finalizar, verás un resumen:

```
================================================================================
  📊 RESUMEN DE EJECUCIÓN
================================================================================

⏱️  Duración: 245.67s
📄 Páginas consultadas: 1
📥 Archivos listados: 47
💾 Archivos descargados: 47

✅ Procesados OK: 42
🔄 Revisiones: 2
📋 Duplicados: 1
⚠️  Para revisión: 1
🚫 Ignorados: 0
❌ Errores: 1

🕐 Timestamp anterior: N/A
🕑 Timestamp nuevo: 2025-11-02T09:45:23Z

✅ Ejecución completada exitosamente
```

**Verificar en base de datos:**

```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM facturas WHERE estado = 'procesado';"
psql $DATABASE_URL -c "SELECT * FROM sync_state WHERE key = 'drive_last_sync_time';"
```

---

## ⏰ Configurar Cron

### Agregar al Crontab

```bash
# Editar crontab
crontab -e
```

### Ejemplos de Configuración

#### Cada 30 minutos (Recomendado)

```bash
*/30 * * * * cd /home/user/invoice-extractor && /home/user/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1
```

#### Cada hora

```bash
0 * * * * cd /home/user/invoice-extractor && /home/user/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1
```

#### Cada 4 horas

```bash
0 */4 * * * cd /home/user/invoice-extractor && /home/user/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1
```

#### Horarios específicos (días laborales)

```bash
# Lunes a Viernes a las 9 AM, 1 PM y 5 PM
0 9,13,17 * * 1-5 cd /home/user/invoice-extractor && /home/user/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1
```

### Verificar Cron Activo

```bash
# Listar jobs activos
crontab -l

# Ver logs de ejecuciones
tail -f logs/cron.log
```

---

## 🔧 Troubleshooting

### Error: "No se puede acceder a carpeta Drive"

**Causa:** Service Account no tiene permisos sobre la carpeta.

**Solución:**
1. Ir a Google Drive en web
2. Compartir la carpeta con el email del Service Account
3. Dar permisos de "Lector" o "Editor"

```bash
# Ver email del service account:
cat keys/service_account.json | grep client_email
```

### Error: "Rate limit exceeded (429)"

**Causa:** Demasiadas requests a Drive API.

**Solución:**
```bash
# En .env, aumentar delays:
DRIVE_RETRY_BASE_MS=1000
SLEEP_BETWEEN_BATCH_SEC=20
DRIVE_PAGE_SIZE=50
```

### Error: "Database connection failed"

**Causa:** PostgreSQL no accesible o credenciales incorrectas.

**Solución:**
```bash
# Verificar que PostgreSQL está corriendo
sudo systemctl status postgresql

# Test de conexión
psql $DATABASE_URL -c "SELECT 1;"
```

### Archivos no se procesan (siempre 0)

**Causa:** `last_sync_time` está muy adelantado.

**Solución:**
```bash
# Ver timestamp actual
psql $DATABASE_URL -c "SELECT * FROM sync_state WHERE key = 'drive_last_sync_time';"

# Resetear (CUIDADO: reprocesará todo en la ventana)
python scripts/run_ingest_incremental.py --reset-state
```

### Consumo alto de RAM/CPU

**Causa:** Lotes muy grandes o Ollama/Tesseract sin límites.

**Solución:**
```bash
# Reducir carga en .env:
BATCH_SIZE=3
SLEEP_BETWEEN_BATCH_SEC=20
MAX_PAGES_PER_RUN=5
```

---

## 🛠️ Comandos Útiles

### Ver Estado Actual

```bash
# Último timestamp de sincronización (DB)
psql $DATABASE_URL -c "SELECT key, value, updated_at FROM sync_state WHERE key = 'drive_last_sync_time';"

# Últimas facturas procesadas
psql $DATABASE_URL -c "SELECT drive_file_name, estado, creado_en FROM facturas ORDER BY creado_en DESC LIMIT 10;"

# Eventos recientes
psql $DATABASE_URL -c "SELECT etapa, nivel, detalle, ts FROM ingest_events ORDER BY ts DESC LIMIT 20;"
```

### Estadísticas

```bash
# Facturas por estado
psql $DATABASE_URL -c "SELECT estado, COUNT(*) FROM facturas GROUP BY estado;"

# Facturas por día (últimos 7 días)
psql $DATABASE_URL -c "SELECT DATE(creado_en) as fecha, COUNT(*) FROM facturas WHERE creado_en > NOW() - INTERVAL '7 days' GROUP BY fecha ORDER BY fecha;"
```

### Ejecutar con Opciones

```bash
# Procesar solo 5 páginas
python scripts/run_ingest_incremental.py --max-pages 5

# Usar lotes de 20
python scripts/run_ingest_incremental.py --batch-size 20

# Guardar estadísticas en JSON
python scripts/run_ingest_incremental.py --output-json results.json
```

### Logs

```bash
# Ver logs en tiempo real
tail -f logs/extractor.log

# Ver solo errores
tail -f logs/extractor.log | grep ERROR

# Ver métricas (si LOG_JSON=true)
tail -f logs/extractor.log | jq '.level, .message'

# Contar errores hoy
grep ERROR logs/extractor.log | grep $(date +%Y-%m-%d) | wc -l
```

### Resetear Sistema (CUIDADO)

```bash
# Resetear timestamp (reprocesará archivos en ventana)
python scripts/run_ingest_incremental.py --reset-state

# Limpiar cuarentena
rm -rf data/quarantine/*

# Limpiar pending
rm -rf data/pending/*
```

---

## 📊 Monitoreo y Métricas

### Métricas Clave

El sistema expone estas métricas en logs JSON:

```json
{
  "drive_items_listed_total": 47,
  "drive_pages_fetched_total": 1,
  "files_downloaded": 47,
  "invoices_processed_ok_total": 42,
  "invoices_duplicate_total": 1,
  "invoices_revision_total": 2,
  "invoices_error_total": 1,
  "duration_seconds": 245.67
}
```

### Alertas Recomendadas

Configurar alertas si:
- `invoices_error_total > 10%` del total
- `download_errors > 5`
- `duration_seconds > 600` (más de 10 min)
- Última ejecución hace más de 2 horas (si cron cada 30 min)

---

## 🎓 Mejores Prácticas

1. **Siempre usar dry-run primero** en nuevas configuraciones
2. **Monitorear los primeros días** después de poner en cron
3. **Revisar cuarentena** semanalmente para detectar patrones de error
4. **Backup de `sync_state`** antes de cambios mayores
5. **Logs con rotación** para no llenar disco
6. **Establecer límites** (`MAX_PAGES_PER_RUN`) para evitar ejecuciones muy largas

---

## 📞 Soporte

Si encuentras problemas:

1. Revisar logs: `logs/extractor.log` y `logs/cron.log`
2. Ejecutar con `--dry-run` para validar configuración
3. Verificar eventos en DB: `SELECT * FROM ingest_events ORDER BY ts DESC LIMIT 50;`
4. Consultar [ENV_CONFIG_INCREMENTAL.md](ENV_CONFIG_INCREMENTAL.md) para configuración detallada

---

## ✅ Checklist Post-Setup

Después de configurar, verificar:

- [ ] Migración aplicada: `psql $DATABASE_URL -c "\d sync_state"`
- [ ] Variables en `.env` configuradas
- [ ] Dry-run exitoso
- [ ] Primera ejecución manual exitosa
- [ ] Cron configurado y activo: `crontab -l`
- [ ] Logs rotando correctamente: `ls -lh logs/`
- [ ] Directorios creados: `ls -d data/*`

**¡Sistema listo para producción! 🚀**

