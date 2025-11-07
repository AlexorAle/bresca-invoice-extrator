# CONTEXTO
Estoy en un Hostinger VPS limpio (Ubuntu 22.04) conectado vía SSH desde Cursor.
Necesito preparar el servidor para un proyecto de extracción de facturas con Python.
Utiliza el archivo "arquitectura.md" en la carpeta "docs" para entender la arquitectura del proyecto.

Estoy en: /home/user/invoice-extractor/ (carpeta vacía)

# OBJETIVO
Genera TODOS los archivos necesarios para el setup inicial del VPS.
Voy a ejecutar los scripts directamente desde esta carpeta.

---

# ARQUITECTURA DEL PROYECTO

## Estructura de Carpetas Completa
````
invoice-extractor/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── infra/
│   ├── setup.sh                  # Setup completo del sistema
│   ├── database_init.sql         # Schema PostgreSQL
│   ├── ollama.service            # Systemd service
│   ├── smoke_test.sh             # Verificaciones post-install
│   └── README_INFRA.md           # Instrucciones de infra
├── src/
│   ├── db/
│   ├── pipeline/
│   ├── dashboard/
│   └── security/
├── data/
│   ├── quarantine/
│   ├── pending/
│   └── backups/
├── temp/
├── logs/
└── scripts/
````

## Esquema de Base de Datos
````sql
-- Proveedores
CREATE TABLE proveedores (
  id               SERIAL PRIMARY KEY,
  nombre           TEXT NOT NULL UNIQUE,
  nif_cif          TEXT,
  email_contacto   TEXT,
  creado_en        TIMESTAMPTZ DEFAULT now()
);

-- Facturas
CREATE TABLE facturas (
  id                   BIGSERIAL PRIMARY KEY,
  drive_file_id        TEXT NOT NULL UNIQUE,
  drive_file_name      TEXT NOT NULL,
  drive_folder_name    TEXT NOT NULL,
  proveedor_id         BIGINT REFERENCES proveedores(id),
  proveedor_text       TEXT,
  numero_factura       TEXT,
  moneda               TEXT DEFAULT 'EUR' CHECK (char_length(moneda)=3),
  fecha_emision        DATE,
  fecha_recepcion      TIMESTAMPTZ,
  base_imponible       NUMERIC(18,2) CHECK (base_imponible >= 0),
  impuestos_total      NUMERIC(18,2) CHECK (impuestos_total >= 0),
  iva_porcentaje       NUMERIC(5,2),
  importe_total        NUMERIC(18,2) NOT NULL CHECK (importe_total >= 0),
  conceptos_json       JSONB,
  metadatos_json       JSONB,
  pagina_analizada     INT DEFAULT 1,
  extractor            TEXT NOT NULL,
  confianza            TEXT CHECK (confianza IN ('alta','media','baja')),
  hash_contenido       TEXT,
  estado               TEXT DEFAULT 'procesado' CHECK (estado IN ('procesado','pendiente','error','revisar')),
  error_msg            TEXT,
  creado_en            TIMESTAMPTZ DEFAULT now(),
  actualizado_en       TIMESTAMPTZ DEFAULT now()
);

-- Índices
CREATE INDEX idx_facturas_fecha_emision ON facturas (fecha_emision);
CREATE INDEX idx_facturas_proveedor_id ON facturas (proveedor_id);
CREATE INDEX idx_facturas_drive_folder ON facturas (drive_folder_name);
CREATE INDEX idx_facturas_estado ON facturas (estado);
CREATE INDEX idx_facturas_conceptos_gin ON facturas USING GIN (conceptos_json);
CREATE INDEX idx_facturas_metadatos_gin ON facturas USING GIN (metadatos_json);

-- Eventos de auditoría
CREATE TABLE ingest_events (
  id            BIGSERIAL PRIMARY KEY,
  drive_file_id TEXT NOT NULL,
  etapa         TEXT NOT NULL,
  nivel         TEXT NOT NULL,
  detalle       TEXT,
  ts            TIMESTAMPTZ DEFAULT now()
);

-- Trigger de updated_at
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.actualizado_en = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_facturas_updated
BEFORE UPDATE ON facturas
FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- Vistas útiles
CREATE VIEW v_totales_por_proveedor_mes AS
SELECT
  p.nombre AS proveedor,
  date_trunc('month', f.fecha_emision)::date AS mes,
  sum(f.importe_total) AS total_mes
FROM facturas f
LEFT JOIN proveedores p ON p.id = f.proveedor_id
GROUP BY 1, 2
ORDER BY 2 DESC, 1;

CREATE VIEW v_impuestos_mensuales AS
SELECT
  date_trunc('month', fecha_emision)::date AS mes,
  sum(impuestos_total) AS impuestos
FROM facturas
GROUP BY 1
ORDER BY 1 DESC;
````

---

# LO QUE NECESITO QUE GENERES

## 1. infra/setup.sh - Script Maestro de Instalación

**Debe hacer (en orden):**

### A. Validaciones Iniciales
- Verificar que corre como usuario normal (no root)
- Verificar Ubuntu/Debian
- Verificar conexión a internet
- Crear log: infra/setup.log

### B. Actualizar Sistema
````bash
sudo apt update
sudo apt upgrade -y
````

### C. Instalar Dependencias Base
````bash
sudo apt install -y \
  python3 python3-venv python3-pip \
  postgresql postgresql-contrib \
  tesseract-ocr tesseract-ocr-spa \
  poppler-utils \
  curl git htop vim \
  build-essential \
  libpq-dev
````

### D. Instalar Ollama
````bash
# Verificar si ya está instalado
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Descargar modelo (si no existe)
ollama pull llama3.2-vision:3b

# Copiar systemd service
sudo cp infra/ollama.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama

# Verificar que arrancó
sleep 5
curl -s http://localhost:11434/api/tags || echo "⚠ Ollama no responde"
````

### E. Configurar PostgreSQL
````bash
# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Ejecutar script de DB
sudo -u postgres psql -f infra/database_init.sql

# Verificar conexión
psql -U extractor_user -h localhost -d negocio_db -c "SELECT 1;" || echo "⚠ PostgreSQL no responde"
````

### F. Crear Estructura de Carpetas
````bash
mkdir -p src/{db,pipeline,dashboard,security}
mkdir -p data/{quarantine,pending,backups}
mkdir -p temp logs scripts
touch data/quarantine/.gitkeep
touch data/pending/.gitkeep
touch data/backups/.gitkeep
touch temp/.gitkeep
touch logs/.gitkeep
````

### G. Configurar Python Virtual Environment
````bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
# requirements.txt se instalará después con el código
````

### H. Configurar Permisos
````bash
chmod 755 infra/*.sh
chmod 755 scripts/*.sh 2>/dev/null || true
````

### I. Resumen Final
````bash
echo "================================"
echo "✓ Setup completado"
echo "================================"
echo "PostgreSQL: $(systemctl is-active postgresql)"
echo "Ollama: $(systemctl is-active ollama)"
echo ""
echo "Siguiente paso:"
echo "  ./infra/smoke_test.sh"
````

**IMPORTANTE:**
- Debe ser idempotente (ejecutable múltiples veces)
- Logging detallado a infra/setup.log
- Exit codes: 0=éxito, 1=error
- Comentarios en español

---

## 2. infra/database_init.sql

**Contenido:**
- Todo el schema SQL de arriba
- Crear usuario extractor_user con contraseña
- Crear base de datos negocio_db
- GRANT permisos mínimos necesarios
- Comentarios explicativos

**Template de usuario:**
````sql
-- Crear usuario (cambiar contraseña en producción)
CREATE USER extractor_user WITH ENCRYPTED PASSWORD 'changeme_produccion';

-- Crear base de datos
CREATE DATABASE negocio_db OWNER extractor_user;

-- Conectar a la DB
\c negocio_db

-- [AQUÍ VA TODO EL SCHEMA DE ARRIBA]

-- Permisos finales
GRANT ALL PRIVILEGES ON DATABASE negocio_db TO extractor_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO extractor_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO extractor_user;
````

---

## 3. infra/ollama.service

**Systemd service para Ollama:**
````ini
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
Type=simple
User=user
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0:11434"

[Install]
WantedBy=multi-user.target
````

---

## 4. infra/smoke_test.sh

**Verificar que todo está instalado correctamente:**

### Verificaciones:
1. **Python 3.9+**
````bash
   python3 --version | grep -E "3\.(9|1[0-9])"
````

2. **PostgreSQL**
````bash
   systemctl is-active postgresql
   psql -U extractor_user -h localhost -d negocio_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
   # Debe retornar >= 3 (facturas, proveedores, ingest_events)
````

3. **Ollama**
````bash
   systemctl is-active ollama
   curl -s http://localhost:11434/api/tags | grep "llama3.2-vision"
````

4. **Tesseract**
````bash
   tesseract --version
   tesseract --list-langs | grep spa
````

5. **Poppler**
````bash
   pdftoppm -v
````

6. **Estructura de carpetas**
````bash
   [ -d src/db ] && [ -d data/backups ] && [ -d logs ]
````

7. **Virtual environment**
````bash
   [ -d venv ] && [ -f venv/bin/activate ]
````

**Output:**
- ✓ para cada check exitoso
- ✗ con mensaje de error si falla
- Exit code 0 si todo OK, 1 si algo falla

---

## 5. .env.example

**Template de variables de entorno:**
````env
# Google Drive
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# PostgreSQL
DATABASE_URL=postgresql://extractor_user:changeme_produccion@localhost/negocio_db

# Paths
TEMP_PATH=/home/user/invoice-extractor/temp
LOG_PATH=/home/user/invoice-extractor/logs/extractor.log
BACKUP_PATH=/home/user/invoice-extractor/data/backups

# Configuración
MONTHS_TO_SCAN=agosto,septiembre,octubre
````

---

## 6. .gitignore
````
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# Secrets
.env
service_account.json
src/dashboard/config.yaml

# Data
data/
temp/
logs/
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Backups
*.sql
*.backup
````

---

## 7. requirements.txt
````txt
# Google Drive
google-api-python-client==2.108.0
google-auth==2.23.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0

# PDF Processing
pdf2image==1.17.0
Pillow==10.2.0
pytesseract==0.3.10

# Database
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23

# Utilities
python-dotenv==1.0.1
requests==2.31.0
tenacity==8.2.3

# Dashboard
streamlit==1.28.0
streamlit-authenticator==0.2.3
pandas==2.1.3

# Logging
python-json-logger==2.0.7
````

---

## 8. infra/README_INFRA.md

**Documentación de la fase de infraestructura:**
````markdown
# Fase 1: Setup de Infraestructura

## Requisitos Previos
- VPS con Ubuntu 22.04 o Debian 11+
- Acceso SSH con sudo
- Mínimo 8GB RAM, 20GB disco
- Conexión a internet

## Instalación

### 1. Conectar al VPS
```bash
ssh user@tu-vps-ip
cd /home/user/invoice-extractor
```

### 2. Ejecutar Setup
```bash
chmod +x infra/setup.sh
./infra/setup.sh
```

Duración: ~10-15 minutos (depende de descarga de Ollama)

### 3. Verificar Instalación
```bash
./infra/smoke_test.sh
```

Debe mostrar ✓ en todos los checks.

## Componentes Instalados

- **PostgreSQL 14+**: Base de datos
- **Ollama + Llama 3.2 Vision 3B**: OCR primario
- **Tesseract OCR**: OCR fallback
- **Python 3.9+**: Runtime
- **Poppler**: Conversión PDF a imagen

## Estructura Creada
````
invoice-extractor/
├── infra/          # Scripts de infraestructura
├── src/            # Código fuente (vacío, fase 2)
├── data/           # Datos persistentes
├── temp/           # Archivos temporales
├── logs/           # Logs de aplicación
└── venv/           # Virtual environment Python
Base de Datos

Nombre: negocio_db
Usuario: extractor_user
Password: changeme_produccion (⚠ CAMBIAR)
Tablas: facturas, proveedores, ingest_events
Puerto: 5432 (solo localhost)

Servicios Systemd
Ollama
bashsudo systemctl status ollama
sudo systemctl restart ollama
sudo journalctl -u ollama -f
PostgreSQL
bashsudo systemctl status postgresql
sudo systemctl restart postgresql
Troubleshooting
Ollama no responde
bashcurl http://localhost:11434/api/tags
# Si falla:
sudo systemctl restart ollama
ollama pull llama3.2-vision:3b
PostgreSQL no conecta
bashsudo -u postgres psql
\l  # Listar bases de datos
\c negocio_db
\dt  # Listar tablas
Python packages faltan
bashsource venv/bin/activate
pip install -r requirements.txt
````

## Próximos Pasos

1. Subir código Python (Fase 2)
2. Configurar .env con credenciales
3. Subir service_account.json
4. Ejecutar tests de código

## Logs

- Setup: `infra/setup.log`
- Ollama: `sudo journalctl -u ollama`
- PostgreSQL: `/var/log/postgresql/`
````

---

## 9. README.md (Principal del Proyecto)
````markdown
# Sistema de Extracción Automática de Facturas

Automatización para extraer datos de facturas PDF usando Ollama Vision + PostgreSQL.

## Estado del Proyecto

- [x] Fase 1: Setup de infraestructura
- [ ] Fase 2: Implementación de código
- [ ] Fase 3: Automatización (cron, systemd)

## Quick Start

Ver: [infra/README_INFRA.md](infra/README_INFRA.md)

## Arquitectura

- **OCR**: Ollama 3.2 Vision (primario) + Tesseract (fallback)
- **Storage**: PostgreSQL
- **Source**: Google Drive (Service Account)
- **Dashboard**: Streamlit
- **Deploy**: Hostinger VPS

## Estructura
````
invoice-extractor/
├── infra/          # Scripts de infraestructura
├── src/            # Código fuente Python
├── data/           # Datos y backups
├── logs/           # Logs de aplicación
└── scripts/        # Utilities
````

## Documentación

- [Setup Infraestructura](infra/README_INFRA.md)
- [Desarrollo](docs/DEVELOPMENT.md) (próximamente)
- [Deployment](docs/DEPLOYMENT.md) (próximamente)
````

---

# REQUISITOS IMPORTANTES

1. **Todos los scripts deben ser ejecutables** (#!/bin/bash al inicio)
2. **Logging detallado** en cada paso importante
3. **Idempotencia**: Se puede ejecutar múltiples veces sin romper
4. **Validaciones**: Verificar éxito antes de continuar
5. **Comentarios en español** en partes críticas
6. **Exit codes apropiados**: 0=éxito, 1=error
7. **No hardcodear paths**: Usar PWD o variables
8. **Compatible con Ubuntu 22.04 y Debian 11**

---

# OUTPUT ESPERADO

Genera TODOS estos archivos listos para usar:

**Archivos de infraestructura:**
- infra/setup.sh
- infra/database_init.sql
- infra/ollama.service
- infra/smoke_test.sh
- infra/README_INFRA.md

**Configuración del proyecto:**
- .env.example
- .gitignore
- requirements.txt
- README.md

**Estructura de carpetas:**
Crea los directorios con .gitkeep donde sea necesario

---

# ORDEN DE EJECUCIÓN PARA MÍ

Después de que generes los archivos:
````bash
# 1. Dar permisos
chmod +x infra/setup.sh infra/smoke_test.sh

# 2. Ejecutar setup
./infra/setup.sh

# 3. Verificar
./infra/smoke_test.sh

# 4. Cambiar password de DB
sudo -u postgres psql
ALTER USER extractor_user WITH PASSWORD 'nueva_password_segura';
````

¿Listo para generar todos los archivos?

✅ Resumen
Lo que hace este prompt:

✅ Crea estructura completa de carpetas
✅ Genera script setup.sh automatizado
✅ Crea schema PostgreSQL completo
✅ Configura Ollama como servicio
✅ Genera smoke tests
✅ Crea templates (.env, .gitignore, requirements.txt)
✅ Documenta todo (READMEs)