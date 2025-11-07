# 🚀 Guía de Inicio Rápido

Esta guía te llevará desde cero hasta tener el sistema funcionando en **30 minutos**.

---

## ✅ Pre-requisitos

Antes de comenzar, asegúrate de tener:

1. ✅ VPS con Ubuntu 22.04+ (ya configurado con scripts de `infra/`)
2. ✅ Archivo `.env` configurado
3. ✅ Service Account de Google Drive (`service_account.json`)
4. ✅ Ollama corriendo con modelo llama3.2-vision

Si NO has ejecutado los scripts de infraestructura, ve primero a: `infra/README_INFRA.md`

---

## 📝 Pasos de Configuración

### Paso 1: Verificar Infraestructura

```bash
cd /home/alex/proyectos/invoice-extractor

# Verificar que todos los componentes están OK
python scripts/test_connection.py
```

**Resultado esperado**: ✅ en todos los componentes.

Si algo falla, revisar la sección de troubleshooting al final.

---

### Paso 2: Instalar Dependencias Python

```bash
# Activar entorno virtual (si no está activo)
source venv/bin/activate

# Instalar todas las dependencias
pip install -r requirements.txt

# Verificar instalación
pip list | grep -E "streamlit|sqlalchemy|google"
```

---

### Paso 3: Configurar Variables de Entorno

Si no tienes un `.env`, créalo desde el template:

```bash
# Copiar template
cp .env.example .env

# Editar con tus valores
nano .env
```

**Variables OBLIGATORIAS que debes configurar:**

```env
# PostgreSQL (cambiar password)
DATABASE_URL=postgresql://extractor_user:TU_PASSWORD_AQUI@localhost/negocio_db

# Google Drive (ruta a tu service account JSON)
GOOGLE_SERVICE_ACCOUNT_FILE=/home/alex/proyectos/invoice-extractor/service_account.json

# Opcional: ID de carpeta base en Drive
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here

# Meses a procesar
MONTHS_TO_SCAN=agosto,septiembre,octubre
```

**Guardar y salir** (Ctrl+X, Y, Enter en nano)

---

### Paso 4: Configurar Service Account de Google

1. **Descargar credenciales** de Google Cloud Console
2. **Copiar al servidor**:

```bash
# Desde tu máquina local
scp service_account.json alex@tu-vps:/home/alex/proyectos/invoice-extractor/

# En el servidor, configurar permisos
chmod 600 service_account.json
```

3. **Compartir carpeta de Drive**:
   - Ve a Google Drive
   - Click derecho en la carpeta "Facturas"
   - Compartir
   - Agregar el email del service account (está en el JSON)
   - Dar permiso de "Viewer"

---

### Paso 5: Generar Configuración del Dashboard

```bash
python scripts/generate_config.py
```

Sigue las instrucciones:
- **Usuario**: admin (o el que prefieras)
- **Nombre**: Tu nombre
- **Email**: tu@email.com
- **Contraseña**: mínimo 8 caracteres

**Guarda estas credenciales en un lugar seguro** - las necesitarás para acceder al dashboard.

---

### Paso 6: Primera Ejecución (Dry-Run)

Antes de procesar archivos reales, hagamos una simulación:

```bash
python src/main.py --dry-run
```

**Qué hace**:
- ✅ Conecta a Google Drive
- ✅ Lista archivos PDF de los meses configurados
- ✅ Muestra cuántos archivos procesaría
- ❌ NO descarga ni procesa nada

**Resultado esperado**:
```
============================================================
Iniciando proceso de extracción de facturas
Meses a procesar: agosto, septiembre, octubre
Modo dry-run: True
...
[DRY-RUN] Se procesarían X archivos
```

---

### Paso 7: Procesar Facturas (Primera Vez)

```bash
# Procesar solo un mes para probar
python src/main.py --months agosto

# O procesar todos los meses configurados
python src/main.py
```

**Qué sucede**:
1. Descarga PDFs de Google Drive
2. Extrae datos con Ollama Vision
3. Guarda en PostgreSQL
4. Muestra estadísticas al final

**Duración**: ~30-60 segundos por factura (depende de Ollama)

---

### Paso 8: Verificar Resultados

```bash
# Ver estadísticas
python src/main.py --stats
```

**Resultado esperado**:
```
============================================================
ESTADÍSTICAS DE BASE DE DATOS
============================================================
Total facturas:     5
Importe total:      €1,234.56
Importe promedio:   €246.91

Por estado:
  procesado       5

Por confianza:
  alta            3
  media           2
```

---

### Paso 9: Iniciar Dashboard

```bash
# Iniciar Streamlit dashboard
streamlit run src/dashboard/app.py
```

**Acceder**: 
- Abre tu navegador en `http://tu-vps-ip:8501`
- Login con las credenciales del Paso 5
- Explora el dashboard

**Funciones del dashboard**:
- 📊 Ver KPIs y estadísticas
- 🔍 Filtrar por mes, estado, confianza
- 📈 Ver gráficos
- ⚠️ Revisar errores
- 📥 Exportar a CSV/Excel

---

## 🔄 Automatización (Opcional)

### Configurar Cron Job para Ejecución Diaria

```bash
# Editar crontab
crontab -e

# Agregar esta línea (ejecuta diariamente a las 9 AM)
0 9 * * * cd /home/alex/proyectos/invoice-extractor && /home/alex/proyectos/invoice-extractor/venv/bin/python src/main.py >> logs/cron.log 2>&1
```

### Configurar Dashboard como Servicio

Crear archivo de servicio systemd:

```bash
sudo nano /etc/systemd/system/invoice-dashboard.service
```

Contenido:
```ini
[Unit]
Description=Invoice Extractor Dashboard
After=network.target

[Service]
Type=simple
User=alex
WorkingDirectory=/home/alex/proyectos/invoice-extractor
ExecStart=/home/alex/proyectos/invoice-extractor/venv/bin/streamlit run src/dashboard/app.py --server.port 8501 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
```

Activar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable invoice-dashboard
sudo systemctl start invoice-dashboard
sudo systemctl status invoice-dashboard
```

---

## 🐛 Troubleshooting

### Problema: "Ollama no responde"

```bash
# Verificar servicio
sudo systemctl status ollama

# Si no está corriendo, iniciarlo
sudo systemctl start ollama

# Verificar API
curl http://localhost:11434/api/tags

# Verificar modelo
ollama list
```

**Solución**: Si el modelo no está, ejecutar:
```bash
ollama pull llama3.2-vision:latest
```

---

### Problema: "PostgreSQL connection refused"

```bash
# Verificar servicio
sudo systemctl status postgresql

# Conectar manualmente
psql -U extractor_user -h localhost -d negocio_db

# Si pide password, verificar DATABASE_URL en .env
```

---

### Problema: "Google Drive API error"

```bash
# Verificar permisos del archivo
ls -la service_account.json

# Debe mostrar: -rw------- (600)
# Si no:
chmod 600 service_account.json

# Verificar que la carpeta está compartida con el service account
# Email del SA está en service_account.json: "client_email"
```

---

### Problema: "No se encuentran archivos en Drive"

**Verificar**:
1. La carpeta está compartida con el service account
2. Los nombres de carpetas coinciden exactamente (agosto, septiembre, etc.)
3. Hay PDFs en esas carpetas

**Debug**:
```bash
# Ver qué está buscando el sistema
python src/main.py --dry-run

# Revisar logs
tail -f logs/extractor.log
```

---

### Problema: "Dashboard no carga"

```bash
# Verificar que config.yaml existe
ls -la src/dashboard/config.yaml

# Si no existe, generar:
python scripts/generate_config.py

# Verificar puerto no está en uso
sudo netstat -tulpn | grep 8501

# Iniciar con otro puerto si es necesario
streamlit run src/dashboard/app.py --server.port 8502
```

---

## 📊 Próximos Pasos

Una vez que todo funciona:

1. ✅ **Procesar todos tus meses**: `python src/main.py`
2. ✅ **Revisar errores** en el dashboard (tab "Errores")
3. ✅ **Exportar datos** a Excel para análisis
4. ✅ **Configurar cron job** para automatización
5. ✅ **Configurar backup periódico** de PostgreSQL

---

## 📚 Documentación Adicional

- **Guía Completa**: Ver `README.md`
- **Troubleshooting Avanzado**: Ver `README.md` sección Troubleshooting
- **Arquitectura**: Ver `docs/arquitectura.md`
- **Desarrollo**: Ver `docs/developer.md`

---

## 🆘 ¿Necesitas Ayuda?

1. Revisar logs: `tail -f logs/extractor.log`
2. Ejecutar test: `python scripts/test_connection.py`
3. Revisar README completo
4. Verificar variables de entorno en `.env`

---

**¡Listo!** Si llegaste aquí sin errores, tu sistema está funcionando correctamente. 🎉

**Última actualización**: Octubre 29, 2025
