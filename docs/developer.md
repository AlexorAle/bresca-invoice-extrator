# CONTEXTO
Estoy en un VPS Hostinger con la infraestructura ya configurada:
- PostgreSQL con base de datos negocio_db (tablas creadas)
- Ollama con modelo llama3.2-vision corriendo
- Python 3.12 con venv
- Tesseract OCR instalado
- Estructura de carpetas lista

Ruta del proyecto: /home/alex/proyectos/invoice-extractor/

Necesito implementar TODO el código Python para el sistema de extracción automática de facturas.

---

# ARQUITECTURA YA IMPLEMENTADA

## Base de Datos (Ya existe)
```sql
-- Tablas:
- facturas (con todos los campos definidos en docs/arquitectura.md)
- proveedores
- ingest_events
- Vistas: v_totales_por_proveedor_mes, v_impuestos_mensuales
```

## Stack Tecnológico
- Python 3.12
- PostgreSQL (ya configurado)
- Ollama API: http://localhost:11434
- Modelo: llama3.2-vision:latest
- Tesseract OCR (fallback)

## Variables de Entorno (.env ya configurado)
```env
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2-vision:latest
DATABASE_URL=postgresql://extractor_user:password@localhost/negocio_db
TEMP_PATH=/home/alex/proyectos/invoice-extractor/temp
LOG_PATH=/home/alex/proyectos/invoice-extractor/logs/extractor.log
BACKUP_PATH=/home/alex/proyectos/invoice-extractor/data/backups
QUARANTINE_PATH=/home/alex/proyectos/invoice-extractor/data/quarantine
MONTHS_TO_SCAN=agosto,septiembre,octubre
OCR_TIMEOUT=30
OCR_RETRY_ATTEMPTS=3
TESSERACT_LANG=spa
TESSERACT_CMD=/usr/bin/tesseract
LOG_LEVEL=INFO
LOG_FORMAT=json
DASHBOARD_PORT=8501
DASHBOARD_HOST=127.0.0.1
```

---

# ESTRUCTURA DE CARPETAS EXISTENTE
```
invoice-extractor/
├── .env (configurado)
├── .gitignore
├── requirements.txt (existe pero vacío)
├── README.md
├── docs/
│   └── arquitectura.md
├── infra/ (scripts de setup ya ejecutados)
├── src/
│   ├── __init__.py
│   ├── main.py (crear)
│   ├── drive_client.py (crear)
│   ├── pdf_utils.py (crear)
│   ├── ocr_extractor.py (crear)
│   ├── parser_normalizer.py (crear)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py (crear)
│   │   ├── models.py (crear)
│   │   └── repositories.py (crear)
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── ingest.py (crear)
│   │   ├── validate.py (crear)
│   │   └── reconcile.py (crear - stub)
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── app.py (crear)
│   │   └── config.yaml (crear template)
│   ├── security/
│   │   ├── __init__.py
│   │   └── secrets.py (crear)
│   └── logging_conf.py (crear)
├── data/
│   ├── quarantine/
│   ├── pending/
│   └── backups/
├── temp/
├── logs/
└── scripts/
    ├── test_connection.py (crear)
    └── generate_config.py (crear)
```

---

# LO QUE NECESITO QUE IMPLEMENTES

## REQUISITOS CRÍTICOS

### 1. Ollama API Integration
**Endpoint**: `http://localhost:11434/api/generate`

**Payload format**:
```python
{
    "model": "llama3.2-vision:latest",
    "prompt": "tu_prompt_aqui",
    "images": ["base64_string"],
    "format": "json",
    "stream": False
}
```

**Response format**:
```python
{
    "response": "json_string_con_datos"
}
```

**Timeout**: 60 segundos
**Retries**: 3 intentos con backoff exponencial

### 2. Prompt para Ollama Vision
```
Analiza esta factura y responde SOLO en JSON con:
{
  "proveedor_text": "Nombre fiscal exacto del proveedor",
  "numero_factura": "string",
  "fecha_emision": "YYYY-MM-DD",
  "moneda": "EUR",
  "base_imponible": 0.0,
  "iva_porcentaje": 21.0,
  "impuestos_total": 0.0,
  "importe_total": 0.0,
  "confianza": "alta|media|baja"
}

REGLAS:
- Si no estás seguro de algún campo, deja null y baja la confianza
- No incluyas texto adicional fuera del JSON
- Responde SOLO el JSON, sin markdown
```

### 3. Google Drive API
- **Authentication**: Service Account
- **Scopes**: `['https://www.googleapis.com/auth/drive.readonly']`
- **Filtro**: `mimeType='application/pdf'`
- **Campos**: `id, name, mimeType, modifiedTime, size, parents`

### 4. PostgreSQL Connection
- **Engine**: SQLAlchemy con pool (min=2, max=10)
- **Timeout**: 30 segundos
- **UPSERT pattern**:
```python
from sqlalchemy.dialects.postgresql import insert
stmt = insert(Factura).values(**data)
stmt = stmt.on_conflict_do_update(
    index_elements=['drive_file_id'],
    set_=data
)
```

### 5. Tesseract Fallback
- **Idioma**: `lang='spa+eng'`
- **DPI**: 150
- **Comando**: `/usr/bin/tesseract`
- **Regex patterns**:
  * Cliente: `r'(Cliente|Bill to|Razón Social):?\s*([A-Z][^\n]{5,})'`
  * Total: `r'(Total|TOTAL|Importe Total):?\s*(\d+[.,]?\d*)'`
  * Fecha: `r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'`
  * Número: `r'(Factura|Invoice|Nº):?\s*([A-Z0-9\-/]+)'`

### 6. Logging
- **Formato**: JSON
- **Campos**: timestamp (ISO8601), level, module, function, message, drive_file_id, etapa, elapsed_ms
- **Rotación**: 10MB, mantener 5 backups
- **Niveles**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### 7. Validaciones Antes de DB Insert
```python
# Obligatorias:
- importe_total is not None and importe_total > 0
- drive_file_id is not None and drive_file_id.strip() != ''
- extractor in ['ollama', 'tesseract']
- confianza in ['alta', 'media', 'baja']

# Si existen base_imponible e impuestos_total:
- abs(base_imponible + impuestos_total - importe_total) < 0.02

# Fecha emisión:
- No puede ser > hoy + 1 día
```

---

# IMPLEMENTACIÓN DETALLADA POR ARCHIVO

## 1. requirements.txt
```txt
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
```

## 2. src/security/secrets.py
```python
"""
Gestión segura de variables de entorno y secrets
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import sys

def load_env():
    """Cargar variables de entorno desde .env"""
    env_path = Path(__file__).parents[2] / '.env'
    if not env_path.exists():
        print(f"ERROR: Archivo .env no encontrado en {env_path}")
        sys.exit(1)
    load_dotenv(env_path)

def validate_secrets():
    """Validar que existen las variables críticas"""
    required = [
        'DATABASE_URL',
        'OLLAMA_BASE_URL',
        'GOOGLE_SERVICE_ACCOUNT_FILE'
    ]
    
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"ERROR: Variables de entorno faltantes: {', '.join(missing)}")
        sys.exit(1)

def check_file_permissions(file_path: str):
    """Verificar permisos de archivos sensibles (debe ser 600)"""
    path = Path(file_path)
    if not path.exists():
        return False
    
    import stat
    st = path.stat()
    # Verificar que solo owner tiene permisos
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        print(f"⚠ ADVERTENCIA: {file_path} tiene permisos inseguros")
        return False
    return True

def get_secret(key: str, default=None):
    """Obtener secret de forma segura"""
    return os.getenv(key, default)
```

## 3. src/logging_conf.py
```python
"""
Configuración de logging estructurado con rotación
"""
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
import os

class JSONFormatter(logging.Formatter):
    """Formatter para logs en formato JSON"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Agregar campos adicionales si existen
        if hasattr(record, 'drive_file_id'):
            log_data['drive_file_id'] = record.drive_file_id
        if hasattr(record, 'etapa'):
            log_data['etapa'] = record.etapa
        if hasattr(record, 'elapsed_ms'):
            log_data['elapsed_ms'] = record.elapsed_ms
            
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(name: str, log_file: str = None, level: str = 'INFO'):
    """
    Configurar logger con rotación y formato JSON
    
    Args:
        name: Nombre del logger
        log_file: Ruta del archivo de log (opcional)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicados
    if logger.handlers:
        return logger
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # Handler para archivo con rotación
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str):
    """Obtener logger ya configurado"""
    log_file = os.getenv('LOG_PATH', 'logs/extractor.log')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    return setup_logger(name, log_file, log_level)
```

## 4. src/db/models.py
```python
"""
Modelos SQLAlchemy para las tablas de la base de datos
"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, DateTime, Text, ForeignKey, CheckConstraint, DECIMAL, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Proveedor(Base):
    """Tabla de proveedores/clientes"""
    __tablename__ = 'proveedores'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(Text, nullable=False, unique=True)
    nif_cif = Column(Text)
    email_contacto = Column(Text)
    creado_en = Column(DateTime, default=datetime.utcnow)
    
    # Relación con facturas
    facturas = relationship("Factura", back_populates="proveedor")

class Factura(Base):
    """Tabla principal de facturas"""
    __tablename__ = 'facturas'
    
    id = Column(BigInteger, primary_key=True)
    drive_file_id = Column(Text, nullable=False, unique=True)
    drive_file_name = Column(Text, nullable=False)
    drive_folder_name = Column(Text, nullable=False)
    
    proveedor_id = Column(BigInteger, ForeignKey('proveedores.id'))
    proveedor_text = Column(Text)
    numero_factura = Column(Text)
    moneda = Column(Text, default='EUR')
    fecha_emision = Column(Date)
    fecha_recepcion = Column(DateTime)
    
    base_imponible = Column(DECIMAL(18, 2))
    impuestos_total = Column(DECIMAL(18, 2))
    iva_porcentaje = Column(DECIMAL(5, 2))
    importe_total = Column(DECIMAL(18, 2), nullable=False)
    
    conceptos_json = Column(JSONB)
    metadatos_json = Column(JSONB)
    
    pagina_analizada = Column(Integer, default=1)
    extractor = Column(Text, nullable=False)
    confianza = Column(Text)
    hash_contenido = Column(Text)
    
    estado = Column(Text, default='procesado')
    error_msg = Column(Text)
    
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con proveedor
    proveedor = relationship("Proveedor", back_populates="facturas")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('char_length(moneda) = 3', name='check_moneda_length'),
        CheckConstraint('base_imponible >= 0', name='check_base_imponible_positive'),
        CheckConstraint('impuestos_total >= 0', name='check_impuestos_positive'),
        CheckConstraint('importe_total >= 0', name='check_importe_total_positive'),
        CheckConstraint("confianza IN ('alta', 'media', 'baja')", name='check_confianza_values'),
        CheckConstraint("estado IN ('procesado', 'pendiente', 'error', 'revisar')", name='check_estado_values'),
    )

class IngestEvent(Base):
    """Tabla de eventos de auditoría"""
    __tablename__ = 'ingest_events'
    
    id = Column(BigInteger, primary_key=True)
    drive_file_id = Column(Text, nullable=False)
    etapa = Column(Text, nullable=False)
    nivel = Column(Text, nullable=False)
    detalle = Column(Text)
    ts = Column(DateTime, default=datetime.utcnow)
```

## 5. src/db/database.py
```python
"""
Configuración de conexión a base de datos con SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from typing import Generator

from .models import Base
from src.logging_conf import get_logger

logger = get_logger(__name__)

class Database:
    """Gestión de conexión a PostgreSQL"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        
        if not self.database_url:
            raise ValueError("DATABASE_URL no configurada")
        
        # Crear engine con pool
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=2,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True,  # Verificar conexión antes de usar
            echo=False
        )
        
        # Session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info("Conexión a base de datos configurada")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager para sesiones de base de datos
        
        Usage:
            with db.get_session() as session:
                session.query(Factura).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en sesión de base de datos: {e}")
            raise
        finally:
            session.close()
    
    def init_db(self):
        """Crear tablas (si no existen)"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Tablas de base de datos verificadas")
    
    def close(self):
        """Cerrar conexión"""
        self.engine.dispose()
        logger.info("Conexión a base de datos cerrada")

# Instancia global
_db_instance = None

def get_database() -> Database:
    """Obtener instancia singleton de Database"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
```

## 6. src/db/repositories.py

**IMPLEMENTA**:
- `file_exists(drive_file_id: str) -> bool`
- `upsert_factura(factura_data: dict) -> int` (retorna ID)
- `insert_event(drive_file_id: str, etapa: str, nivel: str, detalle: str)`
- `get_facturas_by_month(month: str) -> List[dict]`
- `get_statistics() -> dict`
- `get_pending_files() -> List[str]` (leer drive_file_ids ya procesados)

## 7. src/pdf_utils.py

**IMPLEMENTA**:
- `validate_pdf(pdf_path: str) -> bool` (verificar magic bytes %PDF-)
- `get_pdf_info(pdf_path: str) -> dict` (número de páginas, tamaño)
- `pdf_to_image(pdf_path: str, page: int = 1, dpi: int = 200) -> PIL.Image`
- `pdf_to_base64(pdf_path: str, page: int = 1) -> str`

## 8. src/ocr_extractor.py

**CLASE**: `InvoiceExtractor`

**MÉTODOS**:
- `extract_invoice_data(pdf_path: str) -> dict`
- `_extract_with_ollama(image_base64: str) -> dict` (con @retry de tenacity)
- `_extract_with_tesseract(pdf_path: str) -> dict`
- `batch_extract(pdf_paths: List[str]) -> dict`

**USAR**: El prompt exacto que te di arriba para Ollama

## 9. src/parser_normalizer.py

**IMPLEMENTA**:
- `normalize_date(date_str: str) -> str` (retorna ISO YYYY-MM-DD)
- `normalize_amount(amount_str: str) -> float`
- `validate_fiscal_rules(data: dict) -> bool`
- `create_factura_dto(raw_data: dict, metadata: dict) -> dict`

## 10. src/drive_client.py

**CLASE**: `DriveClient`

**MÉTODOS**:
- `__init__(service_account_file: str)`
- `get_folder_id_by_name(folder_name: str, parent_id: str = None) -> str`
- `list_pdf_files(folder_id: str) -> List[dict]`
- `download_file(file_id: str, dest_path: str) -> bool`
- `get_files_from_months(months: List[str], base_folder_id: str) -> dict`

## 11. src/pipeline/ingest.py

**IMPLEMENTA**:
- `process_batch(files_list: List[dict], extractor, db) -> dict` (retorna stats)
- `handle_failure(file_info: dict, error: Exception)` (mover a quarantine)
- `save_to_pending_queue(factura_dto: dict)` (guardar en data/pending/)

## 12. src/pipeline/validate.py

**IMPLEMENTA**:
- `validate_business_rules(factura: dict) -> bool`
- `check_duplicates(factura: dict, db) -> bool`

## 13. src/pipeline/reconcile.py

**STUB** con comentarios de qué irá en el futuro (conciliación bancaria)

## 14. src/main.py

**SCRIPT PRINCIPAL** ejecutable con:
- `argparse` para `--months`, `--dry-run`, `--force`
- Cargar env con `secrets.load_env()`
- Flujo completo:
  1. Conectar Drive y DB
  2. Para cada mes:
     - Listar PDFs
     - Filtrar nuevos (comparar con DB)
     - Descargar a temp/
     - Validar PDF
     - Extraer con OCR
     - Normalizar
     - UPSERT en DB
     - Log evento
     - Limpiar temp/
  3. Generar métricas finales
  4. Backup si > 0 procesadas

**EXIT CODES**:
- 0: Éxito
- 1: Error parcial
- 2: Error crítico

## 15. src/dashboard/app.py

**STREAMLIT APP** con:
- Login (streamlit-authenticator)
- KPIs: total facturas, suma importes, promedio
- Filtros: mes, proveedor, rango fechas, estado
- Tabla de facturas ordenable
- Gráficos: barras (facturas/mes), pie (distribución proveedores)
- Vista de errores (estado='error' o confianza='baja')
- Botón export CSV
- Logout

**NO USAR**: localStorage/sessionStorage

## 16. src/dashboard/config.yaml (template)
```yaml
credentials:
  usernames:
    admin:
      email: admin@example.com
      name: Administrador
      password: $2b$12$placeholder_hash_aqui
cookie:
  name: invoice_dashboard
  key: random_signature_key_change_in_production
  expiry_days: 30
preauthorized:
  emails: []
```

## 17. scripts/test_connection.py

**VERIFICAR**:
1. PostgreSQL (conexión, tablas existen)
2. Ollama (API responde, modelo disponible)
3. Google Drive (credenciales válidas, puede listar)
4. Sistema (Tesseract, Poppler, permisos archivos)

Exit 0 si todo OK, 1 si algo falla

## 18. scripts/generate_config.py

**SCRIPT INTERACTIVO** para generar config.yaml con contraseña hasheada usando bcrypt

---

# REQUISITOS IMPORTANTES

1. **Type hints** en todas las funciones públicas
2. **Docstrings** en español
3. **Manejo robusto de errores** con try-except y logging
4. **Encoding UTF-8** explícito en operaciones de archivos
5. **Retries** con tenacity en APIs (Ollama, Drive)
6. **Logging** en puntos críticos con contexto
7. **Validaciones** antes de DB operations
8. **Idempotencia** donde sea posible
9. **No hardcodear paths** - usar variables de entorno
10. **Exit codes** apropiados en main.py

---

# OUTPUT ESPERADO

Genera TODOS los archivos Python mencionados, completos y funcionales:

**Core**:
- src/main.py
- src/drive_client.py
- src/pdf_utils.py
- src/ocr_extractor.py
- src/parser_normalizer.py

**Database**:
- src/db/database.py (COMPLETO)
- src/db/models.py (COMPLETO)
- src/db/repositories.py (IMPLEMENTAR)

**Pipeline**:
- src/pipeline/ingest.py (IMPLEMENTAR)
- src/pipeline/validate.py (IMPLEMENTAR)
- src/pipeline/reconcile.py (STUB)

**Dashboard**:
- src/dashboard/app.py (COMPLETO)
- src/dashboard/config.yaml (TEMPLATE)

**Security & Logging**:
- src/security/secrets.py (COMPLETO)
- src/logging_conf.py (COMPLETO)

**Scripts**:
- scripts/test_connection.py
- scripts/generate_config.py

**Config**:
- requirements.txt (COMPLETO)
- src/__init__.py y todos los __init__.py necesarios

