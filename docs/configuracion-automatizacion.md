# Configuración de Automatización para Monitoreo de Google Drive

**Fecha:** 5 de noviembre de 2025  
**Objetivo:** Configurar monitoreo automático de Google Drive para procesar nuevas facturas

---

## 📋 Cómo Funciona el Sistema

### Detección de Archivos Procesados

El sistema utiliza **dos métodos** para detectar si un archivo ya fue procesado:

1. **Hash de Contenido** (`hash_contenido`):
   - Calcula SHA256 del contenido del PDF
   - Si el hash existe en BD → archivo ya procesado (ignorado)
   - Si el hash no existe → archivo nuevo (procesado)

2. **Drive File ID** (`drive_file_id`):
   - Identificador único de Google Drive
   - Si el ID existe en BD → archivo ya procesado
   - Si el ID no existe → archivo nuevo

### Proceso Automático

1. **Búsqueda**: Busca todos los PDFs en Google Drive (recursivo)
2. **Comparación**: Compara cada archivo con la BD usando hash e ID
3. **Procesamiento**: Solo procesa archivos nuevos
4. **Almacenamiento**: Guarda en BD con hash para futuras comparaciones

---

## 🚀 Primera Carga (Una Sola Vez)

### Ejecutar Primera Carga

```bash
# Dar permisos de ejecución
chmod +x scripts/primera_carga.sh

# Ejecutar primera carga
./scripts/primera_carga.sh
```

**Qué hace:**
- Procesa TODOS los PDFs actuales en Google Drive
- Solo procesa archivos que NO estén ya en BD
- Calcula y guarda hash para cada archivo
- Procesa con espera de 3 segundos entre facturas (rate limiting)

---

## 🔄 Automatización Continua

### Opción 1: Cron Job (Recomendado)

**Ventajas:**
- ✅ Simple de configurar
- ✅ No requiere servicio adicional
- ✅ Ejecución periódica automática

**Configuración:**

1. Editar crontab:
```bash
crontab -e
```

2. Agregar línea (ejecutar cada hora):
```bash
# Monitorear Google Drive cada hora
0 * * * * /home/alex/proyectos/invoice-extractor/scripts/monitorear_drive.sh
```

3. O cada 30 minutos:
```bash
# Monitorear Google Drive cada 30 minutos
*/30 * * * * /home/alex/proyectos/invoice-extractor/scripts/monitorear_drive.sh
```

4. O diariamente a las 9 AM:
```bash
# Monitorear Google Drive diariamente a las 9 AM
0 9 * * * /home/alex/proyectos/invoice-extractor/scripts/monitorear_drive.sh
```

**Verificar logs:**
```bash
tail -f logs/monitoreo_drive.log
```

---

### Opción 2: Systemd Service (Más Robusto)

**Ventajas:**
- ✅ Mejor manejo de errores
- ✅ Reinicio automático si falla
- ✅ Logs integrados con systemd

**Crear servicio:**

1. Crear archivo de servicio:
```bash
sudo nano /etc/systemd/system/invoice-extractor-monitor.service
```

2. Contenido:
```ini
[Unit]
Description=Invoice Extractor - Google Drive Monitor
After=network.target

[Service]
Type=oneshot
User=alex
WorkingDirectory=/home/alex/proyectos/invoice-extractor
Environment="PATH=/home/alex/proyectos/invoice-extractor/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/alex/proyectos/invoice-extractor/scripts/monitorear_drive.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

3. Crear timer:
```bash
sudo nano /etc/systemd/system/invoice-extractor-monitor.timer
```

4. Contenido del timer:
```ini
[Unit]
Description=Invoice Extractor Monitor Timer
Requires=invoice-extractor-monitor.service

[Timer]
OnCalendar=hourly
# O cada 30 minutos: OnCalendar=*:0/30
# O diario a las 9 AM: OnCalendar=daily 09:00:00

[Install]
WantedBy=timers.target
```

5. Activar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable invoice-extractor-monitor.timer
sudo systemctl start invoice-extractor-monitor.timer
```

6. Verificar:
```bash
sudo systemctl status invoice-extractor-monitor.timer
sudo journalctl -u invoice-extractor-monitor.service -f
```

---

## 📊 Monitoreo y Logs

### Logs del Sistema

**Ubicación:**
- Script de monitoreo: `logs/monitoreo_drive.log`
- Logs de aplicación: Configurados en `src/logging_conf.py`

**Ver logs en tiempo real:**
```bash
tail -f logs/monitoreo_drive.log
```

**Ver últimas 50 líneas:**
```bash
tail -n 50 logs/monitoreo_drive.log
```

### Verificar Estado

**Consultar facturas procesadas:**
```bash
# Desde el dashboard web
http://localhost:5173
```

**Consultar API directamente:**
```bash
curl http://localhost:8001/api/facturas/summary?month=11&year=2025
```

---

## ⚙️ Configuración Recomendada

### Frecuencia de Monitoreo

**Recomendaciones según volumen:**

- **Volumen bajo (< 10 facturas/día)**: 1 vez al día (9 AM)
- **Volumen medio (10-50 facturas/día)**: Cada 6 horas
- **Volumen alto (> 50 facturas/día)**: Cada hora o 30 minutos

### Variables de Entorno

Asegurar que `.env` tenga:
```bash
GOOGLE_DRIVE_FOLDER_ID=tu_folder_id
OPENAI_API_KEY=tu_api_key
DATABASE_URL=postgresql://...
```

---

## 🔍 Troubleshooting

### El script no encuentra archivos nuevos

1. Verificar conexión a Google Drive:
```bash
python3 -c "from src.drive_client import DriveClient; d = DriveClient(); print('✅ Conectado')"
```

2. Verificar permisos de la cuenta de servicio

3. Verificar `GOOGLE_DRIVE_FOLDER_ID` en `.env`

### Archivos duplicados se procesan

1. Verificar que el hash se está calculando correctamente
2. Verificar que la BD tiene los registros anteriores
3. Revisar logs para ver por qué no detecta duplicados

### Rate Limiting de OpenAI

- ✅ Ya implementado: espera de 3 segundos entre facturas
- Si aún hay problemas, aumentar a 5 segundos en `src/pipeline/ingest.py`

---

## ✅ Checklist de Configuración

- [ ] Primera carga ejecutada exitosamente
- [ ] Cron job o systemd timer configurado
- [ ] Logs verificados
- [ ] Dashboard funcionando
- [ ] Variables de entorno configuradas
- [ ] Permisos de Google Drive verificados

---

**Estado:** Sistema listo para automatización  
**Próximo paso:** Ejecutar primera carga y configurar cron job

