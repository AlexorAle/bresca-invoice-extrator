# Sistema de Extracción Automática de Facturas

Sistema automatizado para extraer datos de facturas PDF usando Ollama Vision (Llama 3.2) y almacenarlos en PostgreSQL, con dashboard web interactivo.

## 🚀 Características

- ✅ Extracción automática de datos de facturas PDF usando IA (Ollama Vision)
- ✅ Fallback a Tesseract OCR si falla la IA
- ✅ Almacenamiento en PostgreSQL con validaciones fiscales
- ✅ Dashboard web con Streamlit (autenticación, KPIs, gráficos, exportación)
- ✅ Integración con Google Drive (Service Account)
- ✅ Logging estructurado en JSON con rotación
- ✅ Manejo robusto de errores con cuarentena
- ✅ Sistema de validación y auditoría completo
- ✅ Backups automáticos de base de datos

## 📋 Requisitos Previos

- Ubuntu 22.04+ o Debian 11+ (VPS/local)
- Python 3.9+
- PostgreSQL 14+
- Ollama instalado con modelo llama3.2-vision
- Tesseract OCR
- Poppler utils
- Service Account de Google Cloud (para Drive API)

## 🛠️ Instalación

### 1. Configuración de Infraestructura

Si ya ejecutaste los scripts de `infra/`, continúa al paso 2. Si no:

```bash
# Dar permisos
chmod +x infra/setup.sh infra/smoke_test.sh

# Ejecutar setup (instala PostgreSQL, Ollama, Tesseract, etc.)
./infra/setup.sh

# Verificar instalación
./infra/smoke_test.sh
```

### 2. Instalar Dependencias Python

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar con tus credenciales
nano .env
```

Variables importantes:
- `DATABASE_URL`: Conexión a PostgreSQL
- `GOOGLE_SERVICE_ACCOUNT_FILE`: Ruta a credenciales de Google
- `GOOGLE_DRIVE_FOLDER_ID`: ID de carpeta base en Drive (opcional)
- `OLLAMA_BASE_URL`: URL de Ollama API (default: http://localhost:11434)
- `MONTHS_TO_SCAN`: Meses a procesar (ej: agosto,septiembre,octubre)

### 4. Configurar Google Drive Service Account

1. Crear proyecto en Google Cloud Console
2. Habilitar Google Drive API
3. Crear Service Account y descargar JSON
4. Compartir carpeta de Drive con el email del service account
5. Colocar archivo JSON en el proyecto y actualizar `.env`

```bash
# Configurar permisos seguros
chmod 600 service_account.json
```

### 5. Verificar Componentes

```bash
python scripts/test_connection.py
```

Debe mostrar ✅ en todos los componentes.

### 6. Generar Configuración del Dashboard

```bash
python scripts/generate_config.py
```

Sigue las instrucciones interactivas para crear usuario/contraseña.

## 📦 Uso

### Procesamiento de Facturas

```bash
# Procesar facturas de meses configurados en .env
python src/main.py

# Procesar meses específicos
python src/main.py --months agosto,septiembre

# Modo dry-run (simulación sin procesar)
python src/main.py --dry-run

# Forzar reprocesamiento de archivos ya procesados
python src/main.py --force

# Ver estadísticas de la base de datos
python src/main.py --stats
```

### Dashboard Web

```bash
# Iniciar dashboard
streamlit run src/dashboard/app.py

# Especificar puerto
streamlit run src/dashboard/app.py --server.port 8501
```

Accede en: http://localhost:8501

### Automatización con Cron

Editar crontab:
```bash
crontab -e
```

Agregar línea para ejecución diaria a las 9 AM:
```cron
0 9 * * * cd /home/alex/proyectos/invoice-extractor && /home/alex/proyectos/invoice-extractor/venv/bin/python src/main.py >> logs/cron.log 2>&1
```

## 📊 Estructura del Proyecto

```
invoice-extractor/
├── .env                      # Variables de entorno (no commiteado)
├── .env.example              # Template de variables
├── requirements.txt          # Dependencias Python
├── README.md                 # Este archivo
├── infra/                    # Scripts de infraestructura
│   ├── setup.sh
│   ├── database_init.sql
│   ├── ollama.service
│   └── smoke_test.sh
├── src/                      # Código fuente
│   ├── __init__.py
│   ├── main.py               # Script principal
│   ├── drive_client.py       # Cliente Google Drive
│   ├── ocr_extractor.py      # Extractor OCR (Ollama + Tesseract)
│   ├── parser_normalizer.py # Normalización y validación
│   ├── pdf_utils.py          # Utilidades PDF
│   ├── logging_conf.py       # Configuración de logging
│   ├── security/
│   │   ├── __init__.py
│   │   └── secrets.py        # Gestión de secrets
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py         # Modelos SQLAlchemy
│   │   ├── database.py       # Conexión DB
│   │   └── repositories.py   # Operaciones DB
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── ingest.py         # Pipeline de ingestión
│   │   ├── validate.py       # Validaciones
│   │   └── reconcile.py      # Conciliación (stub)
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py            # Dashboard Streamlit
│       └── config.yaml       # Configuración auth (generado)
├── scripts/
│   ├── test_connection.py    # Verificar componentes
│   └── generate_config.py    # Generar config dashboard
├── data/
│   ├── backups/              # Backups automáticos
│   ├── quarantine/           # Archivos con error
│   └── pending/              # Facturas pendientes revisión
├── temp/                     # Archivos temporales
└── logs/                     # Logs de aplicación
```

## 🔍 Flujo de Procesamiento

1. **Conexión a Google Drive**: Lista PDFs de carpetas mensuales
2. **Descarga**: Descarga archivos a carpeta temporal
3. **Validación**: Verifica integridad del PDF
4. **Extracción OCR**:
   - Primario: Ollama Vision (llama3.2-vision)
   - Fallback: Tesseract OCR
5. **Normalización**: Normaliza fechas, importes, etc.
6. **Validación**: Valida reglas fiscales y de negocio
7. **Almacenamiento**: UPSERT en PostgreSQL
8. **Auditoría**: Registra evento en tabla ingest_events
9. **Limpieza**: Elimina archivos temporales
10. **Backup**: Genera backup de BD si hubo cambios

## 📈 Dashboard

El dashboard incluye:

- **KPIs**: Total facturas, importe total, promedio, confianza
- **Filtros**: Por mes, estado, confianza
- **Tablas**: Listado completo de facturas
- **Gráficos**:
  - Facturas por mes (barras)
  - Top 10 proveedores (pie)
  - Importes por mes (líneas)
  - Distribución por confianza
  - Distribución por extractor
- **Errores**: Vista de facturas que requieren revisión
- **Exportación**: CSV y Excel
- **Autenticación**: Login con bcrypt

## 🔧 Troubleshooting

### Ollama no responde

```bash
# Verificar servicio
systemctl status ollama

# Reiniciar
sudo systemctl restart ollama

# Verificar modelo
curl http://localhost:11434/api/tags
```

### PostgreSQL no conecta

```bash
# Verificar servicio
sudo systemctl status postgresql

# Conectar manualmente
psql -U extractor_user -h localhost -d negocio_db

# Verificar tablas
\dt
```

### Error de credenciales de Google Drive

```bash
# Verificar permisos
ls -la service_account.json

# Debe ser 600 (solo owner)
chmod 600 service_account.json

# Verificar que la carpeta está compartida con el service account
```

### Tesseract no encuentra idiomas

```bash
# Instalar idioma español
sudo apt install tesseract-ocr-spa

# Listar idiomas disponibles
tesseract --list-langs
```

### Dashboard no carga config.yaml

```bash
# Generar configuración
python scripts/generate_config.py

# Verificar que existe
ls -la src/dashboard/config.yaml
```

## 📝 Logs

Ubicación de logs:
- **Aplicación**: `logs/extractor.log` (JSON format, rotación 10MB)
- **Cron**: `logs/cron.log`
- **Ollama**: `sudo journalctl -u ollama`
- **PostgreSQL**: `/var/log/postgresql/`

Ver logs en tiempo real:
```bash
tail -f logs/extractor.log | jq .
```

## 🔐 Seguridad

- ✅ Contraseñas hasheadas con bcrypt
- ✅ Service account con permisos mínimos
- ✅ Variables sensibles en .env (no commiteado)
- ✅ Validación de permisos de archivos
- ✅ SQL injection prevention (ORM)
- ✅ Input validation en todos los endpoints
- ✅ Logging de auditoría

## 🚀 Deployment

### Producción en VPS

1. Ejecutar setup de infraestructura
2. Configurar firewall (solo SSH + dashboard port)
3. Configurar HTTPS con nginx reverse proxy
4. Configurar backup automático de BD
5. Monitoreo con logs estructurados

### Docker (opcional)

```bash
# Build
docker build -t invoice-extractor .

# Run
docker run -d \
  --name invoice-extractor \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  invoice-extractor
```

## 📚 Documentación Adicional

- [Arquitectura del Sistema](docs/arquitectura.md)
- [Setup de Infraestructura](infra/README_INFRA.md)
- [Guía de Desarrollo](docs/developer.md)

## 🤝 Contribuir

Este es un proyecto privado, pero pull requests son bienvenidos.

## 📄 Licencia

Propietario: Alex
Todos los derechos reservados.

## 🆘 Soporte

Para problemas o preguntas, revisar:
1. Esta documentación
2. Logs de aplicación
3. Script de test_connection.py
4. Documentación de arquitectura

---

**Versión**: 1.0.0  
**Última actualización**: Octubre 2025

