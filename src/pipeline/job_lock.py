"""
Sistema de lock para prevenir ejecuciones concurrentes del job
"""
import os
from pathlib import Path
from contextlib import contextmanager
from filelock import FileLock, Timeout
from typing import Generator

from src.logging_conf import get_logger

logger = get_logger(__name__)


class JobLock:
    """Gestor de lock para prevenir ejecuciones concurrentes"""
    
    def __init__(self, lock_file_path: str = None, timeout: int = 300):
        """
        Inicializar gestor de lock
        
        Args:
            lock_file_path: Ruta al archivo de lock (default: data/.job_running.lock)
            timeout: Timeout en segundos para adquirir lock (default: 300 = 5 min)
        """
        if lock_file_path is None:
            data_dir = Path(os.getenv('DATA_PATH', 'data'))
            data_dir.mkdir(parents=True, exist_ok=True)
            lock_file_path = str(data_dir / '.job_running.lock')
        
        self.lock_file_path = lock_file_path
        self.lock = FileLock(lock_file_path, timeout=timeout)
        self.timeout = timeout
        
        logger.debug(f"JobLock inicializado: lock_file={lock_file_path}, timeout={timeout}s")
    
    @contextmanager
    def acquire(self) -> Generator[None, None, None]:
        """
        Context manager para adquirir lock
        
        Usage:
            with job_lock.acquire():
                # Código que necesita exclusión mutua
                pass
        
        Raises:
            Timeout: Si no se puede adquirir el lock en el timeout especificado
        """
        try:
            logger.info(f"Intentando adquirir lock: {self.lock_file_path}")
            self.lock.acquire()
            logger.info("Lock adquirido exitosamente")
            
            try:
                yield
            finally:
                self.lock.release()
                logger.info("Lock liberado exitosamente")
        
        except Timeout:
            logger.warning(
                f"No se pudo adquirir lock después de {self.timeout}s segundos. "
                f"Otra instancia del job está ejecutándose."
            )
            raise
    
    def is_locked(self) -> bool:
        """
        Verificar si el lock está activo (otra instancia está ejecutándose)
        
        Returns:
            True si el lock está activo, False en caso contrario
        """
        try:
            # Intentar adquirir lock con timeout 0 (inmediato)
            test_lock = FileLock(self.lock_file_path, timeout=0)
            test_lock.acquire()
            test_lock.release()
            return False
        except Timeout:
            return True
        except Exception as e:
            logger.warning(f"Error verificando lock: {e}")
            # En caso de error, asumir que no está bloqueado para no bloquear el sistema
            return False
    
    def force_release(self):
        """
        Forzar liberación del lock (usar con precaución)
        
        Solo usar si estás seguro de que no hay otra instancia ejecutándose
        """
        try:
            if Path(self.lock_file_path).exists():
                Path(self.lock_file_path).unlink()
                logger.warning(f"Lock forzado a liberarse: {self.lock_file_path}")
        except Exception as e:
            logger.error(f"Error forzando liberación de lock: {e}")

