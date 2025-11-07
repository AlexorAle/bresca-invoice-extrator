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
        'OPENAI_API_KEY',
        'GOOGLE_SERVICE_ACCOUNT_FILE'
    ]
    
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"ERROR: Variables de entorno faltantes: {', '.join(missing)}")
        sys.exit(1)

def check_file_permissions(file_path: str) -> bool:
    """
    Verificar permisos de archivos sensibles (debe ser 600)
    
    Args:
        file_path: Ruta del archivo a verificar
    
    Returns:
        True si los permisos son seguros, False en caso contrario
    """
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
    """
    Obtener secret de forma segura
    
    Args:
        key: Nombre de la variable de entorno
        default: Valor por defecto si no existe
    
    Returns:
        Valor de la variable de entorno o default
    """
    return os.getenv(key, default)
