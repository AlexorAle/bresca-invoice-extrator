# 🔄 PROCESO INDEPENDIENTE DE CARGA MASIVA

## 📋 SITUACIÓN ACTUAL

El proceso de carga masiva se inició con:
```bash
nohup python3 src/main.py > logs/carga_masiva.log 2>&1 &
```

### ✅ **SÍ SOBREVIVE AL CIERRE DE SSH/CURSOR**

**Ventajas de `nohup`:**
- ✅ El proceso **NO se detiene** al cerrar la conexión SSH
- ✅ El proceso **NO se detiene** al cerrar Cursor local
- ✅ Sigue corriendo en background dentro del contenedor Docker
- ✅ Los logs se guardan en archivo (`logs/carga_masiva.log`)

### ⚠️ **PERO SE DETIENE SI:**

1. **El contenedor Docker se reinicia:**
   ```bash
   docker restart invoice-backend
   ```

2. **El servidor se reinicia:**
   - Reinicio del sistema
   - Apagado del servidor

3. **El contenedor se detiene:**
   ```bash
   docker stop invoice-backend
   ```

---

## 💡 OPCIONES PARA MÁXIMA INDEPENDENCIA

### Opción 1: **Usar `screen` o `tmux` (Recomendado para sesiones)**

```bash
# Dentro del contenedor
docker exec -it invoice-backend bash
screen -S carga_masiva
cd /app && PYTHONPATH=/app python3 src/main.py
# Presionar Ctrl+A luego D para desacoplar
```

**Ventajas:**
- Puedes reconectarte a la sesión después
- Puedes ver el output en tiempo real
- El proceso sobrevive al cierre de SSH

**Reconectar:**
```bash
docker exec -it invoice-backend bash
screen -r carga_masiva
```

### Opción 2: **Usar systemd (Recomendado para producción)**

Crear un servicio systemd que se inicie automáticamente:

```ini
[Unit]
Description=Invoice Extractor Mass Load
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/docker exec invoice-backend bash -c "cd /app && PYTHONPATH=/app python3 src/main.py"
StandardOutput=append:/var/log/invoice-carga.log
StandardError=append:/var/log/invoice-carga-error.log

[Install]
WantedBy=multi-user.target
```

### Opción 3: **Usar Docker restart policy**

Configurar el contenedor para reiniciarse automáticamente:

```yaml
# docker-compose.yml
services:
  backend:
    restart: unless-stopped
```

---

## 🔍 VERIFICAR SI EL PROCESO ESTÁ CORRIENDO

### Desde fuera del contenedor:
```bash
docker exec invoice-backend ps aux | grep "python3.*main.py"
```

### Verificar PID:
```bash
docker exec invoice-backend cat /app/invoice_processor.pid
```

### Ver logs:
```bash
docker exec invoice-backend tail -f /app/logs/carga_masiva.log
```

### Verificar progreso en BD:
```bash
docker exec invoice-backend bash /app/scripts/verificar_estado_carga.sh
```

---

## ✅ CONCLUSIÓN ACTUAL

**Tu proceso ACTUALMENTE:**
- ✅ **SÍ sobrevive** al cierre de SSH
- ✅ **SÍ sobrevive** al cierre de Cursor
- ⚠️ **NO sobrevive** al reinicio del contenedor o servidor

**Para máxima independencia:**
- Usa `screen` o `tmux` si quieres poder reconectarte
- Usa `systemd` si quieres que se reinicie automáticamente
- El método actual (`nohup`) es suficiente si no planeas reiniciar el servidor

---

## 📝 RECOMENDACIÓN

**Para esta carga masiva:**
- El método actual (`nohup`) es **suficiente**
- El proceso seguirá corriendo aunque cierres SSH/Cursor
- Solo asegúrate de no reiniciar el contenedor o servidor

**Para producción futura:**
- Considera usar `systemd` o `docker-compose` con `restart: unless-stopped`
- Esto asegurará que el proceso se reinicie automáticamente si el servidor se reinicia

