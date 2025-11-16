"""
Almacenamiento persistente del estado de sincronización incremental
Soporta backend DB y File
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from abc import ABC, abstractmethod

from src.logging_conf import get_logger

logger = get_logger(__name__, component="backend")


class StateStore(ABC):
    """Interface abstracta para almacenamiento de estado"""
    
    @abstractmethod
    def get_last_sync_time(self) -> Optional[datetime]:
        """Obtener última fecha de sincronización"""
        pass
    
    @abstractmethod
    def set_last_sync_time(self, timestamp: datetime):
        """Establecer última fecha de sincronización"""
        pass


class DBStateStore(StateStore):
    """Almacenamiento de estado en base de datos"""
    
    STATE_KEY = 'drive_last_sync_time'
    
    def __init__(self, db):
        """
        Inicializar store con base de datos
        
        Args:
            db: Instancia de Database
        """
        from src.db.repositories import SyncStateRepository
        self.repo = SyncStateRepository(db)
        logger.info("DBStateStore inicializado")
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """
        Obtener última fecha de sincronización desde DB
        
        Returns:
            Timestamp de última sincronización, o None si no existe
        """
        value = self.repo.get_value(self.STATE_KEY)
        
        if not value:
            logger.info("No hay última sincronización registrada (primera ejecución)")
            return None
        
        try:
            ts = datetime.fromisoformat(value)
            logger.info(f"Última sincronización: {ts.isoformat()}")
            return ts
        except ValueError as e:
            logger.error(f"Error parseando timestamp de estado: {value} - {e}")
            return None
    
    def set_last_sync_time(self, timestamp: datetime):
        """
        Establecer última fecha de sincronización en DB
        
        Args:
            timestamp: Timestamp a guardar
        """
        value = timestamp.isoformat()
        self.repo.set_value(self.STATE_KEY, value)
        logger.info(f"Estado de sincronización actualizado: {value}")


class FileStateStore(StateStore):
    """Almacenamiento de estado en archivo JSON"""
    
    def __init__(self, file_path: str = None):
        """
        Inicializar store con archivo
        
        Args:
            file_path: Ruta al archivo de estado (por defecto desde env STATE_FILE)
        """
        self.file_path = Path(file_path or os.getenv('STATE_FILE', 'state/last_sync.json'))
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileStateStore inicializado: {self.file_path}")
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """
        Obtener última fecha de sincronización desde archivo
        
        Returns:
            Timestamp de última sincronización, o None si no existe
        """
        if not self.file_path.exists():
            logger.info("Archivo de estado no existe (primera ejecución)")
            return None
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            value = data.get('last_sync_time')
            if not value:
                logger.warning("Archivo de estado no contiene 'last_sync_time'")
                return None
            
            ts = datetime.fromisoformat(value)
            logger.info(f"Última sincronización: {ts.isoformat()}")
            return ts
        
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error leyendo archivo de estado: {e}")
            return None
    
    def set_last_sync_time(self, timestamp: datetime):
        """
        Establecer última fecha de sincronización en archivo
        
        Args:
            timestamp: Timestamp a guardar
        """
        data = {
            'last_sync_time': timestamp.isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Estado de sincronización actualizado: {timestamp.isoformat()}")
        
        except Exception as e:
            logger.error(f"Error escribiendo archivo de estado: {e}")
            raise


def get_state_store(db=None) -> StateStore:
    """
    Factory para obtener store según configuración
    
    Args:
        db: Instancia de Database (requerida si backend es 'db')
    
    Returns:
        Instancia de StateStore
    """
    backend = os.getenv('STATE_BACKEND', 'db').lower()
    
    if backend == 'db':
        if not db:
            from src.db.database import Database
            db = Database()
        return DBStateStore(db)
    
    elif backend == 'file':
        return FileStateStore()
    
    else:
        raise ValueError(f"STATE_BACKEND inválido: {backend}. Usar 'db' o 'file'")

