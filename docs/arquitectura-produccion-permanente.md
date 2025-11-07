# Arquitectura para Producción Permanente

**Fecha:** 6 de noviembre de 2025  
**Objetivo:** Explicar cómo funciona el sistema en producción y cuándo se necesita rebuild

---

## 🏗️ Arquitectura del Sistema

### Componentes

```
┌─────────────┐      HTTP      ┌─────────────┐      SQL      ┌─────────────┐
│   Browser   │ ────────────→  │     API     │ ───────────→  │     BD      │
│  (Frontend) │ ←────────────  │  (FastAPI)  │ ←───────────  │ (PostgreSQL)│
└─────────────┘                └─────────────┘               └─────────────┘
     React                          Python                        Datos
```

### Flujo de Datos

1. **Usuario abre el dashboard** → Frontend se carga en el browser
2. **Frontend hace petición HTTP** → `GET /api/facturas/summary?month=7&year=2025`
3. **API consulta la BD** → Ejecuta query SQL en tiempo real
4. **API devuelve JSON** → Datos actualizados de la BD
5. **Frontend renderiza** → Muestra los datos en el dashboard

---

## ❓ ¿Cuándo se necesita rebuild?

### ✅ NO se necesita rebuild cuando:

- ✅ **Se cargan nuevas facturas en la BD**
  - El frontend consulta el API en tiempo real
  - El API consulta la BD cada vez que se hace una petición
  - Los datos se actualizan automáticamente al refrescar el dashboard

- ✅ **Se procesan facturas nuevas**
  - El script `monitorear_drive.sh` procesa facturas
  - Se guardan en la BD
  - El dashboard muestra los datos nuevos al refrescar

- ✅ **Se actualizan datos en la BD**
  - Cualquier cambio en la BD se refleja inmediatamente
  - No requiere rebuild del frontend

**Razón:** El frontend es una aplicación cliente que hace llamadas HTTP al API. El API consulta la BD en tiempo real cada vez que recibe una petición.

---

### ❌ SÍ se necesita rebuild cuando:

- ❌ **Cambias código del frontend**
  - Componentes React
  - Estilos CSS
  - Lógica de negocio
  - Nuevas funcionalidades

- ❌ **Cambias variables de entorno**
  - `VITE_API_BASE_URL`
  - Otras variables de configuración

- ❌ **Cambias la estructura de datos**
  - Si el API devuelve un formato diferente
  - Si el frontend espera campos nuevos/eliminados

- ❌ **Cambias endpoints del API**
  - Si eliminas o renombras endpoints que el frontend usa
  - Si cambias la estructura de las respuestas

---

## 🎯 Configuración para Producción Permanente

### 1. Build del Frontend (Una vez)

```bash
# Crear archivo de configuración para producción
cd frontend
echo "VITE_API_BASE_URL=http://82.25.101.32/api" > .env.production

# Compilar para producción
npm run build

# El build queda en frontend/dist/
```

**Nota:** Este build se hace UNA VEZ (o cuando cambies código del frontend). Los datos se actualizan automáticamente sin rebuild.

---

### 2. Configuración de Nginx (Una vez)

```nginx
# /etc/nginx/sites-available/invoice-dashboard
server {
    listen 80;
    server_name 82.25.101.32;

    # Servir frontend estático
    location /invoice-dashboard {
        alias /var/www/invoice-dashboard;
        try_files $uri $uri/ /invoice-dashboard/index.html;
    }

    # Reverse proxy para API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Nota:** Esta configuración se hace UNA VEZ. Permite que el frontend acceda al API desde fuera.

---

### 3. API como Servicio Systemd (Permanente)

```ini
# /etc/systemd/system/invoice-api.service
[Unit]
Description=Invoice Extractor API
After=network.target postgresql.service

[Service]
Type=simple
User=alex
WorkingDirectory=/home/alex/proyectos/invoice-extractor
Environment="PATH=/home/alex/proyectos/invoice-extractor/venv/bin"
ExecStart=/home/alex/proyectos/invoice-extractor/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Comandos:**
```bash
sudo systemctl enable invoice-api
sudo systemctl start invoice-api
sudo systemctl status invoice-api
```

**Nota:** El API se inicia automáticamente al reiniciar el servidor. No requiere intervención manual.

---

### 4. Monitoreo Automático de Drive (Permanente)

```bash
# Agregar a crontab
crontab -e

# Ejecutar cada hora
0 * * * * /home/alex/proyectos/invoice-extractor/scripts/monitorear_drive.sh
```

**Nota:** El script procesa facturas automáticamente. Los datos se actualizan en la BD sin necesidad de rebuild.

---

## 📊 Flujo Completo en Producción

### Inicialización (Una vez)

1. ✅ Build del frontend con URL correcta
2. ✅ Copiar build a `/var/www/invoice-dashboard/`
3. ✅ Configurar nginx como reverse proxy
4. ✅ Configurar API como servicio systemd
5. ✅ Configurar cron para monitoreo automático

### Operación Diaria (Automático)

1. 🔄 **Cron ejecuta `monitorear_drive.sh`** (cada hora)
2. 🔄 **Script descarga facturas de Drive**
3. 🔄 **Script procesa facturas con OCR**
4. 🔄 **Script guarda en BD**
5. 🔄 **Usuario refresca dashboard** → Ve datos nuevos automáticamente

**No se requiere rebuild en este flujo.**

---

## 🔄 Comparación: Rebuild vs No Rebuild

| Acción | ¿Requiere Rebuild? | Razón |
|--------|-------------------|-------|
| Cargar nuevas facturas | ❌ NO | API consulta BD en tiempo real |
| Procesar facturas nuevas | ❌ NO | Datos se guardan en BD, API los sirve |
| Actualizar datos en BD | ❌ NO | API consulta BD en tiempo real |
| Cambiar código frontend | ✅ SÍ | Código compilado cambió |
| Cambiar URL del API | ✅ SÍ | Variable de entorno cambió |
| Cambiar estructura de datos | ✅ SÍ | Frontend espera formato diferente |

---

## ✅ Resumen

### Para Producción Permanente:

1. **Build del frontend** → UNA VEZ (o cuando cambies código)
2. **Configuración de nginx** → UNA VEZ
3. **API como servicio** → UNA VEZ (se inicia automáticamente)
4. **Cron para monitoreo** → UNA VEZ (se ejecuta automáticamente)

### Operación Diaria:

- ✅ **Cron procesa facturas automáticamente**
- ✅ **Datos se guardan en BD**
- ✅ **Dashboard muestra datos nuevos al refrescar**
- ❌ **NO se requiere rebuild**

---

## 🎯 Conclusión

**Una vez configurado correctamente, el sistema funciona de forma permanente:**

- ✅ Las facturas se procesan automáticamente (cron)
- ✅ Los datos se actualizan en la BD
- ✅ El dashboard muestra datos nuevos sin rebuild
- ✅ Solo necesitas rebuild si cambias código del frontend

**El sistema está diseñado para funcionar en producción sin intervención manual diaria.**

---

**Estado:** 📋 Documentación completa - Listo para producción permanente

