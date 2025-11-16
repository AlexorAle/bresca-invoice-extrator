"""
Configuración de logging estructurado con rotación
Alineado con estándar de Command Center
"""
import logging
import logging.handlers
import json
from datetime import datetime, timezone
from pathlib import Path
import os

class JSONFormatter(logging.Formatter):
    """Formatter para logs en formato JSON - Estándar Command Center"""
    
    def __init__(self, app_id: str = "invoice-extractor", component: str = "backend"):
        super().__init__()
        self.app_id = app_id
        self.component = component
    
    def format(self, record):
        # Timestamp en RFC3339 UTC
        ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Nivel normalizado (asegurar mayúsculas y mapear WARNING -> WARN, CRITICAL -> ERROR)
        level = record.levelname.upper()
        if level == 'WARNING':
            level = 'WARN'
        elif level == 'CRITICAL':
            level = 'ERROR'
        if level not in ['INFO', 'WARN', 'ERROR', 'DEBUG']:
            level = 'INFO'  # Default
        
        # Estructura base requerida
        log_data = {
            'ts': ts,
            'level': level,
            'component': self.component,
            'app': self.app_id,
            'msg': record.getMessage(),
        }
        
        # Campos opcionales estándar
        if hasattr(record, 'module'):
            log_data['module'] = record.module
        if hasattr(record, 'funcName'):
            log_data['function'] = record.funcName
        if hasattr(record, 'lineno'):
            log_data['line'] = record.lineno
        
        # Service (identificar si es FastAPI, Uvicorn, etc.)
        if hasattr(record, 'name'):
            if 'uvicorn' in record.name.lower():
                log_data['service'] = 'uvicorn'
            elif 'fastapi' in record.name.lower():
                log_data['service'] = 'fastapi'
            else:
                log_data['service'] = 'python'
        
        # Request ID y Trace ID (si existen)
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'trace_id'):
            log_data['trace_id'] = record.trace_id
        
        # Campos específicos de dominio (mantener compatibilidad)
        if hasattr(record, 'drive_file_id'):
            log_data['drive_file_id'] = record.drive_file_id
        if hasattr(record, 'etapa'):
            log_data['etapa'] = record.etapa
        if hasattr(record, 'elapsed_ms'):
            log_data['elapsed_ms'] = record.elapsed_ms
        
        # Excepciones
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(
    name: str, 
    log_file: str = None, 
    level: str = 'INFO',
    app_id: str = "invoice-extractor",
    component: str = "backend"
):
    """
    Configurar logger con rotación y formato JSON estándar
    
    Args:
        name: Nombre del logger
        log_file: Ruta del archivo de log (opcional)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        app_id: Identificador de la aplicación (default: invoice-extractor)
        component: Componente (backend, frontend, db) (default: backend)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicados
    if logger.handlers:
        return logger
    
    # Formatter estándar
    formatter = JSONFormatter(app_id=app_id, component=component)
    
    # Handler para consola (stdout) - CRÍTICO para Docker logs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo con rotación (opcional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, component: str = "backend"):
    """
    Obtener logger ya configurado con estándar Command Center
    
    Args:
        name: Nombre del logger (usualmente __name__)
        component: Componente (backend, frontend, db)
    
    Returns:
        Logger configurado
    """
    log_file = os.getenv('LOG_PATH', 'logs/extractor.log')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    app_id = os.getenv('APP_ID', 'invoice-extractor')
    
    return setup_logger(name, log_file, log_level, app_id, component)
