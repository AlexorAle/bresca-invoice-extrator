"""
Dependencias para la API FastAPI
"""
from functools import lru_cache
from typing import Generator

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from src.db.database import Database, get_database
from src.db.repositories import FacturaRepository, SyncStateRepository


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos
    
    Yields:
        Session de SQLAlchemy
    """
    db = get_database()
    with db.get_session() as session:
        yield session


def get_factura_repository(
    db: Database = Depends(get_database)
) -> FacturaRepository:
    """
    Dependency para obtener FacturaRepository
    
    Args:
        db: Instancia de Database
    
    Returns:
        FacturaRepository
    """
    return FacturaRepository(db)


def get_sync_state_repository(
    db: Database = Depends(get_database)
) -> SyncStateRepository:
    """
    Dependency para obtener SyncStateRepository
    
    Args:
        db: Instancia de Database
    
    Returns:
        SyncStateRepository
    """
    return SyncStateRepository(db)

