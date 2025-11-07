"""
Endpoints para sistema
"""
from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_sync_state_repository
from src.api.schemas.facturas import SyncStatusResponse
from src.db.repositories import SyncStateRepository

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/sync-status", response_model=SyncStatusResponse)
async def get_sync_status(
    repo: SyncStateRepository = Depends(get_sync_state_repository)
):
    """
    Obtener estado de sincronización con Drive
    """
    try:
        STATE_KEY = 'drive_last_sync_time'
        last_sync_value = repo.get_value(STATE_KEY)
        
        # Obtener updated_at desde la BD
        from src.db.database import get_database
        from src.db.models import SyncState
        from datetime import datetime
        
        db = get_database()
        with db.get_session() as session:
            state = session.query(SyncState).filter(
                SyncState.key == STATE_KEY
            ).first()
            
            updated_at = None
            if state:
                updated_at = state.updated_at.isoformat() if state.updated_at else None
        
        return SyncStatusResponse(
            last_sync=last_sync_value,
            updated_at=updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado de sincronización: {str(e)}")

