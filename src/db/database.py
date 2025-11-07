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
        """Crear tablas (si no existen) y aplicar migraciones necesarias"""
        Base.metadata.create_all(bind=self.engine)
        
        # Aplicar migraciones necesarias (columnas faltantes)
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(self.engine)
            
            # Verificar y agregar columna drive_modified_time si falta
            if 'facturas' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('facturas')]
                if 'drive_modified_time' not in columns:
                    try:
                        with self.get_session() as session:
                            session.execute(text("ALTER TABLE facturas ADD COLUMN drive_modified_time TIMESTAMP"))
                            session.commit()
                        logger.info("Columna drive_modified_time agregada a facturas")
                        
                        # Crear índice si no existe
                        indexes = [idx['name'] for idx in inspector.get_indexes('facturas')]
                        if 'idx_facturas_drive_modified' not in indexes:
                            with self.get_session() as session:
                                session.execute(text("CREATE INDEX idx_facturas_drive_modified ON facturas (drive_modified_time)"))
                                session.commit()
                            logger.info("Índice idx_facturas_drive_modified creado")
                    except Exception as e:
                        logger.warning(f"No se pudo agregar columna drive_modified_time: {e}")
                        logger.warning("Ejecutar manualmente: ALTER TABLE facturas ADD COLUMN drive_modified_time TIMESTAMP")
        except Exception as e:
            logger.warning(f"Error verificando migraciones: {e}")
        
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
