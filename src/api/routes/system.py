"""
Endpoints para sistema
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.api.dependencies import get_sync_state_repository, get_factura_repository
from src.api.schemas.facturas import SyncStatusResponse
from src.db.repositories import SyncStateRepository, FacturaRepository

router = APIRouter(prefix="/system", tags=["system"])


class DataLoadStatsResponse(BaseModel):
    """Response con estadísticas de carga de datos"""
    archivos_drive: int = Field(..., description="Total de archivos en Drive")
    facturas_bd: int = Field(..., description="Total de facturas en BD")
    facturas_procesadas: int = Field(..., description="Facturas procesadas exitosamente")
    facturas_cuarentena: int = Field(..., description="Facturas en cuarentena")
    facturas_error: int = Field(..., description="Facturas con error")
    diferencia: int = Field(..., description="Diferencia entre Drive y BD")
    nivel_calidad: float = Field(..., description="Porcentaje de importación exitosa (0-100): procesadas / archivos en Drive")
    last_sync: Optional[str] = Field(None, description="Última sincronización")


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


@router.get("/data-load-stats", response_model=DataLoadStatsResponse)
async def get_data_load_stats(
    factura_repo: FacturaRepository = Depends(get_factura_repository),
    sync_repo: SyncStateRepository = Depends(get_sync_state_repository)
):
    """
    Obtener estadísticas de carga de datos
    """
    try:
        import os
        import json
        from pathlib import Path
        
        # 1. Contar archivos en Drive (desde cuarentena + BD)
        archivos_drive = 0
        facturas_cuarentena = 0
        
        # Obtener archivos en cuarentena (usar la misma lógica que get_failed_invoices)
        quarantine_path_env = os.getenv('QUARANTINE_PATH', 'data/quarantine')
        
        # Resolver desde /app (directorio de trabajo del contenedor)
        if os.path.isabs(quarantine_path_env):
            # Si viene como ruta absoluta, extraer solo el nombre relativo
            parts = Path(quarantine_path_env).parts
            if 'data' in parts and 'quarantine' in parts:
                data_idx = parts.index('data')
                quarantine_path_env = str(Path(*parts[data_idx:]))
        
        quarantine_path = Path('/app') / quarantine_path_env
        
        # Obtener lista de facturas ya procesadas en BD para filtrar cuarentena
        # (solo contar archivos que NO están procesados en BD)
        processed_in_bd = set()
        with factura_repo.db.get_session() as session:
            from src.db.models import Factura
            # Obtener todas las facturas procesadas (estado diferente de 'error' y 'revisar')
            facturas_procesadas_bd = session.query(Factura.drive_file_name).filter(
                Factura.drive_file_name.isnot(None),
                ~Factura.estado.in_(['error', 'revisar'])
            ).all()
            processed_in_bd = {f[0] for f in facturas_procesadas_bd if f[0]}
        
        # Contar archivos en cuarentena usando la misma lógica que get_failed_invoices
        # Buscar archivos .meta.json (que es lo que realmente identifica facturas en cuarentena)
        if quarantine_path.exists():
            meta_files = list(quarantine_path.rglob("*.meta.json"))
            archivos_quarantine_count = 0
            processed_names_quarantine = set()  # Para evitar duplicados
            
            for meta_file in meta_files:
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                    
                    # Extraer nombre del archivo (misma lógica que get_failed_invoices)
                    file_info = meta_data.get('file_info', {})
                    nombre = (
                        meta_data.get('drive_file_name') or 
                        file_info.get('name') or 
                        meta_file.stem.replace('.meta', '').split('_', 2)[-1] if '_' in meta_file.stem else meta_file.stem.replace('.meta', '')
                    )
                    
                    # Omitir si es 'unknown' o ya procesado
                    if nombre == 'unknown':
                        continue
                    
                    if nombre in processed_in_bd:
                        continue
                    
                    # Evitar duplicados entre archivos de cuarentena
                    if nombre in processed_names_quarantine:
                        continue
                    
                    processed_names_quarantine.add(nombre)
                    archivos_quarantine_count += 1
                    
                except (json.JSONDecodeError, KeyError, IOError):
                    # Si no se puede leer el meta, usar el nombre del archivo
                    nombre_archivo = meta_file.stem.replace('.meta', '')
                    if nombre_archivo and nombre_archivo != 'unknown' and nombre_archivo not in processed_in_bd and nombre_archivo not in processed_names_quarantine:
                        processed_names_quarantine.add(nombre_archivo)
                        archivos_quarantine_count += 1
            
            facturas_cuarentena = archivos_quarantine_count
            archivos_drive += facturas_cuarentena
        
        # Contar archivos únicos en BD (por drive_file_name)
        with factura_repo.db.get_session() as session:
            from src.db.models import Factura
            from sqlalchemy import func, distinct
            
            # Total de facturas en BD
            total_facturas = session.query(func.count(Factura.id)).scalar() or 0
            
            # Facturas procesadas (estado 'procesada' o sin estado de error)
            facturas_procesadas = session.query(func.count(Factura.id)).filter(
                ~Factura.estado.in_(['error', 'revisar'])
            ).scalar() or 0
            
            # Facturas con error
            facturas_error = session.query(func.count(Factura.id)).filter(
                Factura.estado.in_(['error', 'revisar'])
            ).scalar() or 0
            
            # Contar archivos únicos en Drive (por drive_file_name)
            archivos_unicos_bd = session.query(func.count(func.distinct(Factura.drive_file_name))).filter(
                Factura.drive_file_name.isnot(None)
            ).scalar() or 0
            
            archivos_drive = archivos_unicos_bd + facturas_cuarentena
        
        # Calcular diferencia
        diferencia = archivos_drive - total_facturas
        
        # Calcular estado de importación (procesadas / archivos en Drive * 100)
        # Esto muestra qué porcentaje de archivos en Drive se procesaron exitosamente
        nivel_calidad = (facturas_procesadas / archivos_drive * 100) if archivos_drive > 0 else 0
        
        # Obtener última sincronización
        STATE_KEY = 'drive_last_sync_time'
        last_sync_value = sync_repo.get_value(STATE_KEY)
        
        return DataLoadStatsResponse(
            archivos_drive=archivos_drive,
            facturas_bd=total_facturas,
            facturas_procesadas=facturas_procesadas,
            facturas_cuarentena=facturas_cuarentena,
            facturas_error=facturas_error,
            diferencia=diferencia,
            nivel_calidad=round(nivel_calidad, 2),
            last_sync=last_sync_value
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

