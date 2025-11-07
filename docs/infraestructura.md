# Documentación de Infraestructura - Invoice Extractor

**Fecha de creación:** 29 de octubre de 2025  
**Versión:** 1.0  
**Entorno:** VPS Hostinger - Ubuntu 24.04

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Servicios Instalados](#servicios-instalados)
4. [Base de Datos PostgreSQL](#base-de-datos-postgresql)
5. [Estructura de Carpetas](#estructura-de-carpetas)
6. [Scripts de Infraestructura](#scripts-de-infraestructura)
7. [Configuración de Servicios](#configuración-de-servicios)
8. [Variables de Entorno](#variables-de-entorno)
9. [Comandos Útiles](#comandos-útiles)
10. [Monitoreo y Logs](#monitoreo-y-logs)
11. [Troubleshooting](#troubleshooting)
12. [Mantenimiento](#mantenimiento)

---

## 🎯 Resumen Ejecutivo

Sistema de infraestructura para extracción automática de facturas desde Google Drive, utilizando OCR local (Ollama Vision) y almacenamiento en PostgreSQL.

### Características Principales

- **OCR Local**: Ollama 3.2 Vision (modelo llama3.2-vision:latest, 7.8 GB)
- **Base de Datos**: PostgreSQL 14+ con schema completo
- **Fallback OCR**: Tesseract OCR con soporte español
- **Procesamiento PDF**: Poppler para conversión a imágenes
- **Entorno Python**: Virtual environment aislado
- **Automatización**: Scripts idempotentes para setup y verificación

### Estado del Sistema

✅ **24/24 verificaciones exitosas** (smoke_test.sh)

---

## 🛠 Stack Tecnológico

| Componente | Versión | Propósito |
|-----------|---------|-----------|
| **Sistema Operativo** | Ubuntu 24.04 | Base del servidor |
| **Python** | 3.12.3 | Runtime principal |
| **PostgreSQL** | 14+ | Base de datos relacional |
| **Ollama** | Latest | Servicio OCR (Vision LLM) |
| **Modelo OCR** | llama3.2-vision:latest | Extracción de texto desde imágenes |
| **Tesseract OCR** | 5.3.4 | OCR fallback |
| **Poppler** | Latest | Conversión PDF → PNG |
| **Pip** | Latest | Gestión de paquetes Python |

### Dependencias Python

Ver `requirements.txt` para lista completa. Principales:

- `google-api-python-client==2.108.0` - Google Drive API
- `pdf2image==1.17.0` - Procesamiento PDF
- `psycopg2-binary==2.9.9` - Cliente PostgreSQL
- `SQLAlchemy==2.0.23` - ORM
- `streamlit==1.28.0` - Dashboard web (Fase 2)
- `pytesseract==0.3.10` - Tesseract OCR wrapper

---

## 🔧 Servicios Instalados

### 1. PostgreSQL

**Ubicación del servicio:** Systemd  
**Puerto:** 5432 (solo localhost)  
**Usuario de sistema:** postgres  
**Estado:** `active (running)`

**Configuración:**
- Base de datos: `negocio_db`
- Usuario: `extractor_user`
- Contraseña inicial: `changeme_produccion` ⚠️ **DEBE CAMBIARSE**

**Comandos útiles:**
```bash
# Estado del servicio
sudo systemctl status postgresql

# Iniciar/Detener/Reiniciar
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql

# Logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Conexión como superusuario
sudo -u postgres psql

# Conexión como usuario de la aplicación
psql -U extractor_user -h localhost -d negocio_db
```

### 2. Ollama

**Ubicación del servicio:** Systemd  
**Puerto:** 11434 (HTTP API)  
**Usuario de sistema:** alex  
**Estado:** `active (running)`

**Configuración:**
- Modelo instalado: `llama3.2-vision:latest`
- Tamaño del modelo: ~7.8 GB
- API: `http://localhost:11434`

**Service file:** `/etc/systemd/system/ollama.service`

**Comandos útiles:**
```bash
# Estado del servicio
sudo systemctl status ollama

# Reiniciar servicio
sudo systemctl restart ollama

# Logs
sudo journalctl -u ollama -f

# Listar modelos disponibles
ollama list

# Descargar otro modelo (si necesario)
ollama pull nombre-modelo

# Probar API
curl http://localhost:11434/api/tags
```

**Variables de entorno del servicio:**
- `OLLAMA_HOST=0.0.0.0:11434`
- `MemoryLimit=8G`
- `CPUQuota=200%`

---

## 🗄️ Base de Datos PostgreSQL

### Schema: negocio_db

#### Tablas Principales

##### 1. `proveedores`
Catálogo de proveedores/clientes identificados en facturas.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | SERIAL | Primary key |
| `nombre` | TEXT | Nombre único del proveedor |
| `nif_cif` | TEXT | Identificador fiscal |
| `email_contacto` | TEXT | Email de contacto |
| `creado_en` | TIMESTAMPTZ | Timestamp de creación |

##### 2. `facturas`
Facturas procesadas desde Google Drive.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `drive_file_id` | TEXT | ID único del archivo en Google Drive (UNIQUE) |
| `drive_file_name` | TEXT | Nombre del archivo |
| `drive_folder_name` | TEXT | Carpeta origen |
| `proveedor_id` | BIGINT | FK a proveedores |
| `proveedor_text` | TEXT | Nombre del proveedor (extraído) |
| `numero_factura` | TEXT | Número de factura |
| `moneda` | TEXT | Código ISO (default: 'EUR') |
| `fecha_emision` | DATE | Fecha de emisión |
| `fecha_recepcion` | TIMESTAMPTZ | Fecha de procesamiento |
| `base_imponible` | NUMERIC(18,2) | Base imponible |
| `impuestos_total` | NUMERIC(18,2) | Total de impuestos |
| `iva_porcentaje` | NUMERIC(5,2) | Porcentaje IVA |
| `importe_total` | NUMERIC(18,2) | Total de la factura |
| `conceptos_json` | JSONB | Conceptos en formato JSON |
| `metadatos_json` | JSONB | Metadatos adicionales |
| `pagina_analizada` | INT | Página procesada (default: 1) |
| `extractor` | TEXT | Método usado ('ollama', 'tesseract') |
| `confianza` | TEXT | Nivel: 'alta', 'media', 'baja' |
| `hash_contenido` | TEXT | Hash para detección de duplicados |
| `estado` | TEXT | 'procesado', 'pendiente', 'error', 'revisar' |
| `error_msg` | TEXT | Mensaje de error (si aplica) |
| `creado_en` | TIMESTAMPTZ | Timestamp de creación |
| `actualizado_en` | TIMESTAMPTZ | Timestamp de actualización (auto) |

##### 3. `ingest_events`
Eventos de auditoría del proceso de ingestión.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `drive_file_id` | TEXT | ID del archivo relacionado |
| `etapa` | TEXT | Etapa: 'descarga', 'ocr', 'extracción', 'guardado', 'error' |
| `nivel` | TEXT | Nivel: 'info', 'warning', 'error' |
| `detalle` | TEXT | Detalle del evento |
| `ts` | TIMESTAMPTZ | Timestamp del evento |

#### Índices Creados

```sql
-- Índices principales
idx_facturas_fecha_emision     ON facturas (fecha_emision)
idx_facturas_proveedor_id      ON facturas (proveedor_id)
idx_facturas_drive_folder      ON facturas (drive_folder_name)
idx_facturas_estado            ON facturas (estado)
idx_facturas_conceptos_gin     ON facturas USING GIN (conceptos_json)
idx_facturas_metadatos_gin     ON facturas USING GIN (metadatos_json)
idx_ingest_events_file_id      ON ingest_events (drive_file_id)
idx_ingest_events_ts           ON ingest_events (ts)
```

#### Triggers

**`trg_facturas_updated`**
- Función: `set_updated_at()`
- Tabla: `facturas`
- Evento: `BEFORE UPDATE`
- Acción: Actualiza automáticamente `actualizado_en` a `now()`

#### Vistas

##### `v_totales_por_proveedor_mes`
Resumen mensual de facturas por proveedor.

```sql
SELECT
  p.nombre AS proveedor,
  date_trunc('month', f.fecha_emision)::date AS mes,
  sum(f.importe_total) AS total_mes,
  count(*) AS cantidad_facturas
FROM facturas f
LEFT JOIN proveedores p ON p.id = f.proveedor_id
WHERE f.fecha_emision IS NOT NULL
GROUP BY 1, 2
ORDER BY 2 DESC, 1;
```

##### `v_impuestos_mensuales`
Resumen mensual de impuestos y totales.

```sql
SELECT
  date_trunc('month', fecha_emision)::date AS mes,
  sum(impuestos_total) AS impuestos,
  sum(base_imponible) AS base_imponible,
  sum(importe_total) AS total
FROM facturas
WHERE fecha_emision IS NOT NULL
GROUP BY 1
ORDER BY 1 DESC;
```

### Scripts de Base de Datos

**Ubicación:** `infra/database_init.sql`

Este script contiene:
- Creación de usuario `extractor_user`
- Creación de base de datos `negocio_db`
- Todas las tablas, índices, triggers y vistas
- Permisos y grants necesarios

**Ejecución:**
```bash
sudo -u postgres psql < infra/database_init.sql
```

---

## 📁 Estructura de Carpetas

```
/home/alex/proyectos/invoice-extractor/
│
├── infra/                          # Scripts de infraestructura
│   ├── setup.sh                    # Script maestro de instalación
│   ├── database_init.sql           # Schema PostgreSQL
│   ├── ollama.service              # Systemd service para Ollama
│   ├── smoke_test.sh              # Verificaciones post-install
│   ├── README_INFRA.md             # Documentación de infra
│   └── setup.log                   # Log del setup
│
├── src/                            # Código fuente Python (Fase 2)
│   ├── db/                         # Conexión y modelos SQLAlchemy
│   ├── pipeline/                   # Pipeline de extracción
│   ├── dashboard/                  # Dashboard Streamlit
│   └── security/                   # Autenticación y autorización
│
├── data/                           # Datos persistentes
│   ├── quarantine/                 # Archivos en cuarentena (.gitkeep)
│   ├── pending/                    # Pendientes de procesar (.gitkeep)
│   └── backups/                    # Backups de base de datos (.gitkeep)
│
├── temp/                           # Archivos temporales (.gitkeep)
├── logs/                           # Logs de aplicación (.gitkeep)
├── scripts/                        # Utilidades y scripts auxiliares
│
├── venv/                           # Virtual environment Python
│
├── .env.example                    # Template de variables de entorno
├── .env                            # Variables de entorno (NO comitear)
├── .gitignore                      # Exclusiones de Git
├── requirements.txt                # Dependencias Python
└── README.md                       # Documentación principal
```

### Permisos y Seguridad

- `service_account.json`: Permisos `600` (solo propietario)
- Scripts ejecutables: Permisos `755`
- `.env`: Excluido de Git (ver `.gitignore`)
- Logs: Permisos `644`

---

## 🔨 Scripts de Infraestructura

### 1. `infra/setup.sh`

Script maestro de instalación y configuración.

**Características:**
- ✅ Idempotente (se puede ejecutar múltiples veces)
- ✅ Logging detallado en `infra/setup.log`
- ✅ Validaciones previas
- ✅ Manejo de errores robusto

**Funciones principales:**
1. Validaciones iniciales (usuario, kinternet, sistema operativo)
2. Actualización del sistema (apt update/upgrade)
3. Instalación de dependencias base
4. Instalación y configuración de Ollama
5. Configuración de PostgreSQL
6. Creación de estructura de carpetas
7. Configuración de Python venv
8. Configuración de permisos

**Ejecución:**
```bash
chmod +x infra/setup.sh
./infra/setup.sh
```

**Duración estimada:** ~10-15 minutos (primera vez, incluye descarga de Ollama)

### 2. `infra/smoke_test.sh`

Script de verificación post-instalación.

**Verifica:**
- ✅ Python 3.9+ instalado
- ✅ PostgreSQL activo y accesible
- ✅ Base de datos `negocio_db` con tablas
- ✅ Ollama activo y modelo disponible
- ✅ Tesseract OCR instalado (con español)
- ✅ Poppler instalado
- ✅ Estructura de carpetas completa
- ✅ Python venv configurado
- ✅ Archivos de configuración presentes

**Ejecución:**
```bash
./infra/smoke_test.sh
```

**Salida esperada:**
```
✓ Exitosos: 24
✓ Fallidos: 0
¡Todos los checks pasaron! El sistema está listo.
```

### 3. `infra/database_init.sql`

Script SQL de inicialización de base de datos.

**Contenido:**
- Creación de usuario `extractor_user`
- Creación de base de datos `negocio_db`
- Schema completo (tablas, índices, triggers, vistas)
- Permisos y grants

**Ejecución manual:**
```bash
sudo -u postgres psql < infra/database_init.sql
```

---

## ⚙️ Configuración de Servicios

### Systemd Service: Ollama

**Archivo:** `/etc/systemd/system/ollama.service`

```ini
[Unit]
Description=Ollama Service - Invoice Extractor OCR
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=alex
Group=alex
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0:11434"
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ollama
MemoryLimit=8G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

**Configuración:**
- Usuario: Se reemplaza dinámicamente por `setup.sh`
- Auto-restart: Habilitado
- Límites: 8GB RAM, 200% CPU
- Puerto: 11434 (escucha en todas las interfaces)

**Comandos:**
```bash
# Habilitar en boot
sudo systemctl enable ollama

# Ver estado
sudo systemctl status ollama

# Ver logs
sudo journalctl -u ollama -f
```

### PostgreSQL Service

**Archivo:** `/etc/systemd/system/postgresql.service` (provisto por el paquete)

**Configuración por defecto:**
- Usuario: postgres
- Puerto: 5432
- Datos: `/var/lib/postgresql/`
- Configuración: `/etc/postgresql/*/main/postgresql.conf`

---

## 🔐 Variables de Entorno

**Template:** `.env.example`  
**Archivo real:** `.env` (NO se commitea)

### Variables Principales

```env
# Google Drive API
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here

# Ollama (OCR Primario)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2-vision:latest

# PostgreSQL
DATABASE_URL=postgresql://extractor_user:changeme_produccion@localhost/negocio_db
PROJECT_ROOT=/home/alex/proyectos/invoice-extractor

# Paths
TEMP_PATH=/home/alex/proyectos/invoice-extractor/temp
LOG_PATH=/home/alex/proyectos/invoice-extractor/logs/extractor.log
BACKUP_PATH=/home/alex/proyectos/invoice-extractor/data/backups
QUARANTINE_PATH=/home/alex/proyectos/invoice-extractor/data/quarantine

# Configuración de extracción
MONTHS_TO_SCAN=agosto,septiembre,octubre
OCR_TIMEOUT=30
OCR_RETRY_ATTEMPTS=3

# Tesseract (OCR Fallback)
TESSERACT_LANG=spa
TESSERACT_CMD=/usr/bin/tesseract

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Dashboard Streamlit (Fase 2)
DASHBOARD_PORT=8501
DASHBOARD_HOST=127.0.0.1
```

**⚠️ IMPORTANTE:** Después del setup, cambiar la contraseña en `.env`:

```bash
sudo -u postgres psql
ALTER USER extractor_user WITH PASSWORD 'nueva_password_segura';
\q
```

Luego actualizar `DATABASE_URL` en `.env`.

---

## 🎮 Comandos Útiles

### Base de Datos

```bash
# Conectar a la base de datos
psql -U extractor_user -h localhost -d negocio_db

# Listar tablas
\dt

# Describir tabla
\d facturas

# Ver vistas
\dv

# Consulta rápida
psql -U extractor_user -h localhost -d negocio_db -c "SELECT COUNT(*) FROM facturas;"

# Backup
pg_dump -U extractor_user -h localhost negocio_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U extractor_user -h localhost -d negocio_db < backup_20251029.sql
```

### Ollama

```bash
# Listar modelos
ollama list

# Probar modelo (via API)
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2-vision:latest",
  "prompt": "test"
}'

# Ver uso de memoria
ollama ps

# Verificar API
curl http://localhost:11434/api/tags
```

### Python Virtual Environment

```bash
# Activar venv
source venv/bin/activate

# Desactivar
deactivate

# Instalar dependencias
pip install -r requirements.txt

# Actualizar pip
pip install --upgrade pip

# Listar paquetes instalados
pip list
```

### Sistema

```bash
# Ver estado de servicios
systemctl status postgresql ollama

# Ver uso de recursos
htop
df -h  # Espacio en disco
free -h  # Memoria

# Ver logs de aplicación
tail -f logs/extractor.log

# Ver logs de setup
tail -f infra/setup.log
```

---

## 📊 Monitoreo y Logs

### Logs del Sistema

| Servicio | Ubicación |
|----------|-----------|
| **PostgreSQL** | `/var/log/postgresql/postgresql-*.log` |
| **Ollama** | `sudo journalctl -u ollama` |
| **Setup** | `infra/setup.log` |
| **Aplicación** | `logs/extractor.log` (Fase 2) |

### Ver Logs en Tiempo Real

```bash
# PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log

# Ollama
sudo journalctl -u ollama -f

# Setup
tail -f infra/setup.log
```

### Monitoreo de Recursos

```bash
# Uso de CPU y memoria
htop

# Espacio en disco
df -h

# Uso de Ollama (memoria del modelo)
ollama ps

# Conexiones PostgreSQL
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 🔧 Troubleshooting

### Problema: PostgreSQL no conecta

**Síntomas:**
```
psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Soluciones:**

1. Verificar que el servicio está corriendo:
   ```bash
   sudo systemctl status postgresql
   ```

2. Verificar autenticación en `pg_hba.conf`:
   ```bash
   sudo cat /etc/postgresql/*/main/pg_hba.conf
   ```
   Debe incluir: `local all all md5`

3. Verificar que el usuario existe:
   ```bash
   sudo -u postgres psql -c "\du"
   ```

4. Reiniciar PostgreSQL:
   ```bash
   sudo systemctl restart postgresql
   ```

### Problema: Ollama no responde

**Síntomas:**
```
curl: (7) Failed to connect to localhost port 11434
```

**Soluciones:**

1. Verificar servicio:
   ```bash
   sudo systemctl status ollama
   ```

2. Reiniciar servicio:
   ```bash
   sudo systemctl restart ollama
   sleep 5
   curl http://localhost:11434/api/tags
   ```

3. Ver logs:
   ```bash
   sudo journalctl -u ollama -n 50
   ```

4. Verificar permisos del usuario:
   ```bash
   sudo systemctl edit ollama.service
   # Verificar User=alex
   ```

### Problema: Modelo Ollama no encontrado

**Síntomas:**
```
llama3.2-vision no encontrado
```

**Solución:**
```bash
ollama pull llama3.2-vision:latest
```

### Problema: Base de datos no inicializada

**Síntomas:**
```
✗ Conexión a PostgreSQL: No se pudo conectar con extractor_user
```

**Solución:**
```bash
sudo -u postgres psql < infra/database_init.sql
```

### Problema: Permisos de archivos

**Síntomas:**
```
Permission denied al ejecutar scripts
```

**Solución:**
```bash
chmod +x infra/*.sh
chmod 600 service_account.json  # Si existe
```

---

## 🔄 Mantenimiento

### Backups de Base de Datos

**Manual:**
```bash
pg_dump -U extractor_user -h localhost negocio_db > \
  data/backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

**Automatizado (cron):**
```bash
# Editar crontab
crontab -e

# Agregar línea (diario a las 2 AM)
0 2 * * * pg_dump -U extractor_user -h localhost negocio_db > \
  /home/alex/proyectos/invoice-extractor/data/backups/backup_$(date +\%Y\%m\%d).sql
```

### Actualización de Dependencias

```bash
# Activar venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Actualizar paquetes
pip install --upgrade -r requirements.txt
```

### Actualización de Ollama

```bash
# Descargar versión más reciente
curl -fsSL https://ollama.com/install.sh | sh

# Reiniciar servicio
sudo systemctl restart ollama
```

### Limpieza de Archivos Temporales

```bash
# Limpiar carpeta temp
rm -rf temp/*

# Limpiar logs antiguos (mantener últimos 7 días)
find logs -name "*.log" -mtime +7 -delete
```

### Verificación Periódica

Ejecutar smoke test periódicamente:
```bash
./infra/smoke_test.sh
```

---

## 📝 Notas Adicionales

### Seguridad

- ⚠️ **Cambiar contraseña de PostgreSQL** antes de producción
- ⚠️ **No commitees** `.env` ni `service_account.json`
- ⚠️ **Permisos restrictivos** en archivos sensibles (600)
- ⚠️ **Firewall**: Considerar UFW si se expone al exterior (Fase 2: Streamlit)

### Performance

- **Ollama**: Modelo ocupa ~7.8 GB en memoria (ajustar `MemoryLimit` si necesario)
- **PostgreSQL**: Índices GIN para búsquedas en JSONB
- **Tesseract**: Más lento que Ollama pero útil como fallback

### Escalabilidad

- **Actual**: Sistema diseñado para ~100 facturas/mes
- **Expansión futura**: Considerar particionado de tablas si >1000 facturas/mes
- **Ollama**: CPU-only mode (GPU opcional para mejor performance)

---

## 📚 Referencias

- [Documentación PostgreSQL](https://www.postgresql.org/docs/)
- [Documentación Ollama](https://github.com/ollama/ollama)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Setup Infraestructura](infra/README_INFRA.md)
- [Arquitectura del Sistema](arquitectura.md)

---

**Última actualización:** 29 de octubre de 2025  
**Mantenido por:** Equipo de Infraestructura

