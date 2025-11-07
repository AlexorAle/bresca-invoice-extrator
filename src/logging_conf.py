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
    """
    Obtener logger ya configurado
    
    Args:
        name: Nombre del logger (usualmente __name__)
    
    Returns:
        Logger configurado
    """
    log_file = os.getenv('LOG_PATH', 'logs/extractor.log')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    return setup_logger(name, log_file, log_level)
