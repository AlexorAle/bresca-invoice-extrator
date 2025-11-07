#!/usr/bin/env python3
"""
Script para verificar conexiones y componentes del sistema
"""
import sys
import os
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from security.secrets import load_env, get_secret
from logging_conf import get_logger

# Cargar .env
load_env()

logger = get_logger(__name__)

def test_postgresql():
    """Verificar conexión a PostgreSQL"""
    print("\n🗄️  Verificando PostgreSQL...")
    
    try:
        from db.database import get_database
        
        db = get_database()
        
        # Intentar consulta simple
        with db.get_session() as session:
            result = session.execute("SELECT 1").scalar()
            
            if result == 1:
                print("✅ PostgreSQL: Conexión exitosa")
                
                # Verificar tablas
                tables = session.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                ).fetchall()
                
                table_names = [t[0] for t in tables]
                expected_tables = ['facturas', 'proveedores', 'ingest_events']
                
                missing_tables = [t for t in expected_tables if t not in table_names]
                
                if missing_tables:
                    print(f"⚠️  Tablas faltantes: {', '.join(missing_tables)}")
                    print("   Ejecuta el script de setup de base de datos")
                    return False
                else:
                    print(f"✅ Tablas encontradas: {', '.join(expected_tables)}")
                
                db.close()
                return True
            else:
                print("❌ PostgreSQL: Consulta de prueba falló")
                return False
    
    except Exception as e:
        print(f"❌ PostgreSQL: Error - {e}")
        return False

def test_ollama():
    """Verificar Ollama API y modelo"""
    print("\n🤖 Verificando Ollama...")
    
    try:
        import requests
        
        ollama_url = get_secret('OLLAMA_BASE_URL', 'http://localhost:11434')
        ollama_model = get_secret('OLLAMA_MODEL', 'llava:7b')
        
        # Verificar que Ollama está corriendo
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Ollama API: Activo en {ollama_url}")
            
            # Verificar modelo
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            # Buscar modelo (puede tener diferentes variantes del nombre)
            model_base = ollama_model.split(':')[0]
            model_found = any(model_base in m for m in models)
            
            if model_found:
                print(f"✅ Modelo encontrado: {ollama_model}")
                return True
            else:
                print(f"⚠️  Modelo {ollama_model} no encontrado")
                print(f"   Modelos disponibles: {', '.join(models)}")
                print(f"   Ejecuta: ollama pull {ollama_model}")
                return False
        else:
            print(f"❌ Ollama API: No responde (status {response.status_code})")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Ollama: No se puede conectar. ¿Está corriendo?")
        print(f"   Ejecuta: ollama serve")
        return False
    
    except Exception as e:
        print(f"❌ Ollama: Error - {e}")
        return False

def test_google_drive():
    """Verificar credenciales de Google Drive"""
    print("\n☁️  Verificando Google Drive...")
    
    try:
        service_account_file = get_secret('GOOGLE_SERVICE_ACCOUNT_FILE')
        
        if not service_account_file:
            print("❌ Google Drive: GOOGLE_SERVICE_ACCOUNT_FILE no configurado")
            return False
        
        service_account_path = Path(service_account_file)
        
        if not service_account_path.exists():
            print(f"❌ Google Drive: Archivo no encontrado - {service_account_file}")
            return False
        
        # Verificar permisos del archivo
        import stat
        st = service_account_path.stat()
        
        if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            print(f"⚠️  Google Drive: Permisos inseguros en {service_account_file}")
            print(f"   Ejecuta: chmod 600 {service_account_file}")
        
        print(f"✅ Service account encontrado: {service_account_file}")
        
        # Intentar inicializar cliente
        from drive_client import DriveClient
        
        client = DriveClient(service_account_file)
        print("✅ Google Drive: Cliente inicializado correctamente")
        
        return True
    
    except Exception as e:
        print(f"❌ Google Drive: Error - {e}")
        return False

def test_tesseract():
    """Verificar instalación de Tesseract"""
    print("\n📝 Verificando Tesseract OCR...")
    
    try:
        import pytesseract
        import subprocess
        
        tesseract_cmd = get_secret('TESSERACT_CMD', '/usr/bin/tesseract')
        
        # Verificar versión
        result = subprocess.run(
            [tesseract_cmd, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Tesseract: {version_line}")
            
            # Verificar idiomas
            result_langs = subprocess.run(
                [tesseract_cmd, '--list-langs'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            langs = result_langs.stdout
            
            tesseract_lang = get_secret('TESSERACT_LANG', 'spa+eng')
            required_langs = tesseract_lang.split('+')
            
            missing_langs = [lang for lang in required_langs if lang not in langs]
            
            if missing_langs:
                print(f"⚠️  Idiomas faltantes: {', '.join(missing_langs)}")
                print(f"   Instala con: sudo apt install tesseract-ocr-{missing_langs[0]}")
                return False
            else:
                print(f"✅ Idiomas disponibles: {tesseract_lang}")
            
            return True
        else:
            print(f"❌ Tesseract: No se pudo ejecutar")
            return False
    
    except FileNotFoundError:
        print(f"❌ Tesseract: No instalado")
        print(f"   Instala con: sudo apt install tesseract-ocr tesseract-ocr-spa")
        return False
    
    except Exception as e:
        print(f"❌ Tesseract: Error - {e}")
        return False

def test_poppler():
    """Verificar instalación de Poppler (pdf2image)"""
    print("\n📄 Verificando Poppler (PDF tools)...")
    
    try:
        import subprocess
        
        # Verificar pdftoppm
        result = subprocess.run(
            ['pdftoppm', '-v'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 or 'pdftoppm' in result.stderr:
            version_info = result.stderr.split('\n')[0] if result.stderr else 'instalado'
            print(f"✅ Poppler: {version_info}")
            return True
        else:
            print("❌ Poppler: No instalado")
            print("   Instala con: sudo apt install poppler-utils")
            return False
    
    except FileNotFoundError:
        print("❌ Poppler: No instalado")
        print("   Instala con: sudo apt install poppler-utils")
        return False
    
    except Exception as e:
        print(f"❌ Poppler: Error - {e}")
        return False

def test_directories():
    """Verificar estructura de directorios"""
    print("\n📁 Verificando estructura de directorios...")
    
    required_dirs = [
        get_secret('TEMP_PATH', 'temp'),
        get_secret('BACKUP_PATH', 'data/backups'),
        get_secret('QUARANTINE_PATH', 'data/quarantine'),
        Path(get_secret('LOG_PATH', 'logs/extractor.log')).parent,
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        
        if path.exists():
            print(f"✅ {path}")
        else:
            print(f"⚠️  {path} (no existe, se creará automáticamente)")
            # Crear directorio
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ Creado: {path}")
            except Exception as e:
                print(f"   ❌ Error creando directorio: {e}")
                all_ok = False
    
    return all_ok

def main():
    """Ejecutar todos los tests"""
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE COMPONENTES DEL SISTEMA")
    print("=" * 60)
    
    results = {
        'PostgreSQL': test_postgresql(),
        'Ollama': test_ollama(),
        'Google Drive': test_google_drive(),
        'Tesseract': test_tesseract(),
        'Poppler': test_poppler(),
        'Directorios': test_directories()
    }
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component:20} {'OK' if status else 'FALLO'}")
    
    print("=" * 60)
    
    all_ok = all(results.values())
    
    if all_ok:
        print("\n🎉 Todos los componentes están correctamente configurados")
        print("   Puedes ejecutar: python src/main.py")
        return 0
    else:
        print("\n⚠️  Algunos componentes requieren atención")
        print("   Revisa los mensajes de error arriba")
        return 1

if __name__ == "__main__":
    sys.exit(main())
