# Plan de Implementación: Sistema de Extracción Automática de Facturas  
**Versión Refinada para Hostinger VPS + PostgreSQL + Streamlit Dashboard + Ollama 3.2 Vision**  
*Volumen: ≤100 facturas/mes | Enfoque: Robustez | Costo: $0 (todo local/gratis)*

---

## Resumen Ejecutivo
Sistema automatizado que:
1. **Escanea diariamente** carpetas mensuales en Google Drive (`Facturas/agosto/`, etc.)
2. **Detecta PDFs nuevos**
3. **Extrae nombre del cliente e importe total** usando:
   - **Primario**: Ollama 3.2 Vision (Llama 3.2 3B) – gratis, local en VPS
   - **Fallback**: Tesseract OCR (gratis)
4. **Almacena en PostgreSQL** (integrable con bot de trading y futuras apps)
5. **Muestra dashboard web seguro** con Streamlit (login para dueño del negocio)
6. **Ejecuta en Hostinger VPS** con cron job diario

Ollama 3.2 Vision: Corre localmente en 8GB RAM sin GPU. Instalación simple (curl + pull). API local para extracción de imágenes (PDF → PNG → base64).

---

## Arquitectura del Sistema

### Stack Tecnológico
| Componente | Tecnología |
|----------|------------  |
| Lenguaje | Python 3.9+ |
| Base de Datos | **PostgreSQL** (Hostinger VPS) |
| APIs | Google Drive API v3 (Service Account) |
| OCR Primario | **Ollama 3.2 Vision (Llama 3.2 3B)** – local, gratis |
| OCR Fallback | Tesseract OCR (`pytesseract`) |
| Dashboard | Streamlit + `streamlit-authenticator` |
| Logging | `logging` con rotación |
| Dependencias | `requirements.txt` |

### Estructura de Carpetas
/home/user/invoice-extractor/
├── .env
├── .gitignore
├── service_account.json         # Google Service Account (protegido)
├── requirements.txt
├── src/
│   ├── drive_client.py
│   ├── ocr_extractor.py         # Actualizado para Ollama
│   ├── database.py
│   ├── main.py
│   └── dashboard.py             # Streamlit dashboard
├── data/
│   └── backups/                 # Backups automáticos
├── logs/
│   └── extractor.log
└── temp/                        # Descargas temporales
text---

## Configuración en Hostinger VPS (SSH)

### 1. Acceso y Preparación
```bash
ssh user@tu-ip-hostinger
mkdir invoice-extractor && cd invoice-extractor
python3 -m venv venv
source venv/bin/activate
2. Instalar Dependencias del Sistema
bashsudo apt update
sudo apt install -y poppler-utils tesseract-ocr postgresql postgresql-contrib curl
3. Instalar y Configurar Ollama 3.2 Vision
bash# Instalar Ollama (1 comando)
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo Llama 3.2 Vision 3B (gratis, ~2GB, ~5-10 min)
ollama pull llama3.2-vision:3b

# Iniciar servicio Ollama en background (persiste con systemd)
nohup ollama serve > /home/user/ollama.log 2>&1 &
# O para auto-start: sudo systemctl enable ollama (si disponible)

# Verificar (debe correr en http://localhost:11434)
curl http://localhost:11434/api/tags  # Lista modelos
4. Configurar PostgreSQL
bashsudo -u postgres psql
sqlCREATE DATABASE negocio_db;
CREATE USER extractor_user WITH ENCRYPTED PASSWORD 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE negocio_db TO extractor_user;
\q

Credenciales y .env
service_account.json

Crea en Google Cloud Console > IAM > Service Accounts
Comparte carpeta Facturas/ con el email del service account
Descarga y sube via SCP/SSH:
bashscp service_account.json user@tu-ip:/home/user/invoice-extractor/
chmod 600 service_account.json


.env (protegido)
env# Google Drive
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434

# PostgreSQL
DATABASE_URL=postgresql://extractor_user:tu_contraseña_segura@localhost/negocio_db

# Configuración
MONTHS_TO_SCAN=agosto,septiembre,octubre
TEMP_PATH=/home/user/invoice-extractor/temp
LOG_PATH=/home/user/invoice-extractor/logs/extractor.log
BACKUP_PATH=/home/user/invoice-extractor/data/backups
bashchmod 600 .env

requirements.txt
txtgoogle-api-python-client==2.108.0
google-auth==2.23.0
pdf2image==1.17.0
Pillow==10.2.0
python-dotenv==1.0.1
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23
pytesseract==0.3.10
tenacity==8.2.3
streamlit==1.28.0
streamlit-authenticator==0.2.2
requests==2.31.0  # Para llamadas API a Ollama

Código Principal (Resumen para Agente de Implementación)
Instrucciones para Cursor/Agente

Usa este código base. El agente debe:

Reemplazar llamadas OpenAI por requests a Ollama API (/api/generate para visión).
Convertir imagen PDF a base64.
Prompt similar, parsear JSON response.
Agregar retries con tenacity para Ollama calls.
Fallback a Tesseract si Ollama falla (e.g., modelo no responde).



src/drive_client.py (Service Account – Sin cambios)
pythonfrom google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE'), scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

# Resto del código igual: get_folder_id_by_name, list_pdf_files, download_file, get_files_from_months
src/ocr_extractor.py (Ollama 3.2 Vision + Tesseract Fallback)
pythonimport base64
import json
import requests
import os
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import io
import pytesseract  # Para fallback
from tenacity import retry, wait_exponential

class InvoiceExtractor:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.2-vision:3b"

    def _pdf_to_base64_image(self, pdf_path: str) -> str:
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
        img = images[0]
        max_size = 2000
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    @retry(wait=wait_exponential(multiplier=1, max=10))
    def _extract_with_ollama(self, img_base64: str) -> dict:
        prompt = """Analiza esta factura y extrae en formato JSON:
{
  "nombre_cliente": "Nombre completo del cliente o empresa",
  "importe_total": 1234.56,
  "confianza": "alta/media/baja"
}
INSTRUCCIONES: nombre_cliente exacto, importe_total solo número, confianza tu certeza. Responde SOLO JSON."""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [img_base64],
            "format": "json",
            "stream": False
        }
        response = requests.post(f"{self.ollama_url}/api/generate", json=payload)
        response.raise_for_status()
        content = response.json()["response"].strip()
        if content.startswith('```json
            content = content.split('```json')[1].split('```')[0]
        data = json.loads(content)
        if data.get('importe_total'):
            data['importe_total'] = float(data['importe_total'])
        return data

    def _extract_with_tesseract(self, pdf_path: str) -> dict:
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
        text = pytesseract.image_to_string(images[0], lang='spa+eng')
        # Regex simple para extraer (agente: mejora con patrones específicos)
        import re
        cliente_match = re.search(r'(Cliente|Bill to):?\s*([A-Z][a-z\s]+)', text, re.IGNORECASE)
        importe_match = re.search(r'Total[:\s]*(\d+[.,]?\d*)', text, re.IGNORECASE)
        return {
            'nombre_cliente': cliente_match.group(2).strip() if cliente_match else None,
            'importe_total': float(importe_match.group(1).replace(',', '.')) if importe_match else None,
            'confianza': 'baja'  # Tesseract es aproximado
        }

    def extract_invoice_data(self, pdf_path: str) -> dict:
        try:
            img_base64 = self._pdf_to_base64_image(pdf_path)
            data = self._extract_with_ollama(img_base64)
            if not data or data.get('confianza') == 'baja':
                print("Usando Tesseract como fallback...")
                data = self._extract_with_tesseract(pdf_path)
            return data
        except Exception as e:
            print(f"Error en extracción: {e}")
            return self._extract_with_tesseract(pdf_path)  # Fallback en error

    def batch_extract(self, pdf_paths: list) -> dict:
        results = {}
        for pdf_path in pdf_paths:
            results[pdf_path] = self.extract_invoice_data(pdf_path)
        return results
src/database.py (SQLAlchemy + PostgreSQL – Sin cambios mayores)
pythonfrom sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()
engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)

class Factura(Base):
    __tablename__ = 'facturas'
    id = Column(Integer, primary_key=True)
    drive_file_id = Column(String, unique=True, nullable=False)
    nombre_archivo = Column(String, nullable=False)
    mes = Column(String, nullable=False)
    nombre_cliente = Column(String)
    importe_total = Column(Float)
    confianza = Column(String)
    fecha_creacion_drive = Column(String)
    fecha_procesado = Column(DateTime, default=datetime.utcnow)
    estado = Column(String, default='procesado')
    notas = Column(Text)

# Crear tablas
Base.metadata.create_all(engine)

# Métodos: file_exists, insert_invoice, get_all_invoices, get_invoices_by_month, get_statistics, log_event, close
# (Agente: Implementa con session.commit() para robustez)
src/main.py (Con retries y backup – Actualizado para Ollama)
pythonimport os
import sys
from pathlib import Path
from datetime import datetime
import time
import shutil
from dotenv import load_dotenv
from tenacity import retry, wait_exponential

from drive_client import DriveClient
from ocr_extractor import InvoiceExtractor  # Ahora con Ollama
from database import InvoiceDatabase, backup_database  # Asume función backup

load_dotenv()

class InvoiceProcessor:
    def __init__(self):
        self.drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')  # Agrega a .env si falta
        self.months = os.getenv('MONTHS_TO_SCAN', 'agosto,septiembre,octubre').split(',')
        self.temp_path = Path(os.getenv('TEMP_PATH', './temp'))
        self.db_path = os.getenv('DATABASE_URL')  # Para PostgreSQL
        self.ollama_url = os.getenv('OLLAMA_BASE_URL')
        
        self.temp_path.mkdir(parents=True, exist_ok=True)
        self.drive_client = DriveClient()
        self.extractor = InvoiceExtractor(self.ollama_url)
        self.db = InvoiceDatabase(self.db_path)
    
    @retry(wait=wait_exponential(multiplier=1, max=10))
    def scan_and_process(self) -> dict:
        # Lógica igual: files_by_month, procesar por mes, download, extract, insert
        # Agrega: time.sleep(1) entre calls para no saturar Ollama
        # Al final: backup_database(os.getenv('BACKUP_PATH'))
        pass  # Agente: Completa con código del plan original adaptado

    def show_database_stats(self):
        # Igual

    def cleanup_temp(self):
        # Igual

    def close(self):
        self.db.close()

def main():
    try:
        processor = InvoiceProcessor()
        stats = processor.scan_and_process()
        processor.show_database_stats()
        processor.close()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
src/dashboard.py (Streamlit con Login – Sin cambios)
pythonimport streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
from sqlalchemy import create_engine
import os

# Cargar config.yaml (crea con: credentials: {usernames: {dueño: {email: email@ej, name: Dueño, password: hashed_pass}}}
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'main')
    st.rerun()
elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
    st.rerun()
elif authenticator.login('Login', 'main'):
    st.title("Dashboard de Facturas")
    engine = create_engine(os.getenv('DATABASE_URL'))
    df = pd.read_sql("SELECT * FROM facturas ORDER BY mes DESC", engine)
    mes = st.selectbox("Seleccionar Mes", df['mes'].unique())
    st.dataframe(df[df['mes'] == mes])
    if st.button("Logout"):
        authenticator.logout()

Ejecución Diaria (Cron en Hostinger)
En hPanel > Cron Jobs:
text0 9 * * * cd /home/user/invoice-extractor && /home/user/invoice-extractor/venv/bin/python src/main.py >> /home/user/invoice-extractor/logs/cron.log 2>&1
Backup Semanal (PostgreSQL)
text0 3 * * 0 pg_dump -U extractor_user -h localhost negocio_db > /home/user/invoice-extractor/data/backups/facturas_$(date +\%Y\%m\%d).sql
Dashboard en Background
bashcd /home/user/invoice-extractor && nohup streamlit run src/dashboard.py --server.port=8501 --server.headless=true > /home/user/streamlit.log 2>&1 &

Seguridad

chmod 600 en .env, service_account.json
Login obligatorio en Streamlit (hash passwords en config.yaml con bcrypt)
No datos sensibles → sin encriptación DB
Logs auditables con timestamps
Ollama local: Solo accesible en localhost





































MilestoneTareaCursor/Agente1Instalar Ollama + Service Account GoogleManual SSH; Agente: "Verifica API Ollama con curl"2OCR con Ollama (prompt visión + base64)Genera ocr_extractor.py completo3Base de datos PostgreSQL + Modelos SQLAlchemyMigra schema y métodos4Main con retries + Dashboard StreamlitAgente: "Integra fallback Tesseract y filtros en dashboard"5Deploy: Cron, backups, pruebas en VPSAgente: "Agrega logging estructurado y error handling"

Próximos Pasos

Instalar Ollama en VPS (ver arriba)
Crear Service Account en Google Cloud
Configurar PostgreSQL y crear config.yaml para login
Subir código y .env via SCP
Probar manual: python src/main.py (verifica Ollama responde)
Configurar cron y dashboard
Entregar URL + login al dueño


