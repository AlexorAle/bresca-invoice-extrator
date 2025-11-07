# ⚡ Quick Reference - Ingesta Incremental

## 🚀 Setup Inicial (Hacer una sola vez)

```bash
# 1. Aplicar migración SQL
bash scripts/apply_incremental_migration.sh

# 2. Agregar variables a .env
cat >> .env << 'EOF'
SYNC_WINDOW_MINUTES=1440
BATCH_SIZE=10
SLEEP_BETWEEN_BATCH_SEC=10
MAX_PAGES_PER_RUN=10
ADVANCE_STRATEGY=MAX_OK_TIME
STATE_BACKEND=db
DRIVE_PAGE_SIZE=100
DRIVE_RETRY_MAX=5
DRIVE_RETRY_BASE_MS=500
QUARANTINE_DIR=data/quarantine
PENDING_DIR=data/pending
EOF

# 3. Crear directorios
mkdir -p data/quarantine data/pending state logs

# 4. Validar setup
python scripts/test_incremental_system.py
```

---

## 📋 Comandos Comunes

### Validar sin ejecutar (dry-run)
```bash
python scripts/run_ingest_incremental.py --dry-run
```

### Ejecutar manualmente
```bash
python scripts/run_ingest_incremental.py
```

### Ejecutar con opciones
```bash
# Procesar solo 5 páginas (testing)
python scripts/run_ingest_incremental.py --max-pages 5

# Lotes de 20 archivos
python scripts/run_ingest_incremental.py --batch-size 20

# Guardar estadísticas en JSON
python scripts/run_ingest_incremental.py --output-json results.json
```

### Configurar cron (automático)
```bash
crontab -e

# Agregar (ajustar rutas):
*/30 * * * * cd /home/user/invoice-extractor && /home/user/invoice-extractor/venv/bin/python scripts/run_ingest_incremental.py >> logs/cron.log 2>&1
```

---

## 🔍 Monitoreo

### Ver logs en tiempo real
```bash
tail -f logs/extractor.log
tail -f logs/cron.log
```

### Ver solo errores
```bash
tail -f logs/extractor.log | grep ERROR
```

### Ver último timestamp
```bash
# Si STATE_BACKEND=db
psql $DATABASE_URL -c "SELECT * FROM sync_state WHERE key = 'drive_last_sync_time';"

# Si STATE_BACKEND=file
cat state/last_sync.json
```

### Estadísticas de facturas
```bash
# Por estado
psql $DATABASE_URL -c "SELECT estado, COUNT(*) FROM facturas GROUP BY estado;"

# Últimas procesadas
psql $DATABASE_URL -c "SELECT drive_file_name, estado, creado_en FROM facturas ORDER BY creado_en DESC LIMIT 10;"
```

---

## 🛠️ Troubleshooting

### Resetear timestamp (reprocesar todo)
```bash
# ⚠️ CUIDADO: Reprocesará archivos en ventana de SYNC_WINDOW_MINUTES
python scripts/run_ingest_incremental.py --reset-state
```

### Verificar acceso a Drive
```bash
python scripts/test_incremental_system.py
```

### Ver archivos en cuarentena
```bash
ls -lh data/quarantine/
cat data/quarantine/*.meta.json | jq .
```

### Ver archivos pendientes de revisión
```bash
ls -lh data/pending/
cat data/pending/*.json | jq .
```

### Limpiar cuarentena/pending
```bash
# ⚠️ Solo si ya revisaste los errores
rm -rf data/quarantine/*
rm -rf data/pending/*
```

---

## 📊 Queries Útiles

### Eventos recientes
```sql
SELECT etapa, nivel, detalle, ts 
FROM ingest_events 
ORDER BY ts DESC 
LIMIT 20;
```

### Facturas por día (últimos 7 días)
```sql
SELECT DATE(creado_en) as fecha, COUNT(*) 
FROM facturas 
WHERE creado_en > NOW() - INTERVAL '7 days' 
GROUP BY fecha 
ORDER BY fecha;
```

### Facturas con problemas
```sql
SELECT drive_file_name, estado, error_msg 
FROM facturas 
WHERE estado IN ('error', 'revisar') 
ORDER BY creado_en DESC;
```

### Duplicados detectados
```sql
SELECT drive_file_name, hash_contenido 
FROM facturas 
WHERE estado = 'duplicado' 
ORDER BY creado_en DESC;
```

---

## ⚙️ Ajustes Comunes

### Si muchos errores 429 (rate limit)
```bash
# En .env:
DRIVE_RETRY_BASE_MS=1000
SLEEP_BETWEEN_BATCH_SEC=20
DRIVE_PAGE_SIZE=50
```

### Si consume mucha RAM
```bash
# En .env:
BATCH_SIZE=5
MAX_PAGES_PER_RUN=5
```

### Si quieres procesar más rápido
```bash
# En .env:
BATCH_SIZE=20
SLEEP_BETWEEN_BATCH_SEC=5
MAX_PAGES_PER_RUN=20
```

### Primera carga (muchos archivos históricos)
```bash
# En .env:
SYNC_WINDOW_MINUTES=43200  # 30 días
MAX_PAGES_PER_RUN=50
BATCH_SIZE=5
```

---

## 📁 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `README_INCREMENTAL.md` | Overview completo del sistema |
| `INCREMENTAL_SETUP_GUIDE.md` | Guía paso a paso de setup |
| `ENV_CONFIG_INCREMENTAL.md` | Variables de entorno detalladas |
| `scripts/run_ingest_incremental.py` | Script principal ejecutable |
| `scripts/test_incremental_system.py` | Tests de validación |

---

## 🆘 Ayuda Rápida

```bash
# Ver ayuda del script
python scripts/run_ingest_incremental.py --help

# Validar configuración
python scripts/test_incremental_system.py

# Dry run (no procesa)
python scripts/run_ingest_incremental.py --dry-run

# Ver logs
tail -f logs/extractor.log
```

---

## ✅ Checklist Post-Setup

- [ ] Migración aplicada
- [ ] Variables en `.env`
- [ ] Tests pasando (`test_incremental_system.py`)
- [ ] Dry-run exitoso
- [ ] Primera ejecución manual OK
- [ ] Cron configurado (si producción)
- [ ] Monitoreo configurado

---

**Para más detalles, ver [README_INCREMENTAL.md](README_INCREMENTAL.md)**

