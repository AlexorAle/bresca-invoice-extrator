"""
API endpoints para gestión de costos de personal mensuales
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
from pydantic import BaseModel, Field
from src.db.database import Database
from src.db.repositories import CostoPersonalRepository

router = APIRouter(tags=["costos-personal"])

# Schemas
class CostoPersonalBase(BaseModel):
    mes: int = Field(..., ge=1, le=12, description="Mes (1-12)")
    año: int = Field(..., ge=2000, le=2100, description="Año (2000-2100)")
    sueldos_netos: float = Field(..., ge=0, description="Total sueldos netos pagados")
    coste_empresa: float = Field(..., ge=0, description="Total coste empresa (seguros sociales)")
    notas: Optional[str] = Field(None, max_length=500, description="Notas opcionales")

class CostoPersonalCreate(CostoPersonalBase):
    """Schema para crear/actualizar costo de personal"""
    pass

class CostoPersonalResponse(CostoPersonalBase):
    """Schema de respuesta con campos calculados"""
    id: int
    total_personal: float = Field(..., description="Suma de sueldos_netos + coste_empresa")
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    
    class Config:
        from_attributes = True

class CostoPersonalTotalesResponse(BaseModel):
    """Schema para totales anuales"""
    total_sueldos_netos: float
    total_coste_empresa: float
    total_personal: float

# Dependency
def get_costo_personal_repository():
    """Dependency para obtener repository de costos de personal"""
    db = Database()
    try:
        return CostoPersonalRepository(db)
    finally:
        db.close()

@router.get("/{year}", response_model=List[CostoPersonalResponse])
async def get_costos_by_year(
    year: int = Path(..., ge=2000, le=2100, description="Año a consultar"),
    repo: CostoPersonalRepository = Depends(get_costo_personal_repository)
):
    """
    Obtener todos los costos de personal de un año específico
    
    Returns:
        Lista de costos de personal ordenados por mes
    """
    try:
        costos = repo.get_all_by_año(year)
        return costos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener costos: {str(e)}")

@router.get("/{year}/{month}", response_model=CostoPersonalResponse)
async def get_costo_by_mes(
    year: int = Path(..., ge=2000, le=2100, description="Año"),
    month: int = Path(..., ge=1, le=12, description="Mes (1-12)"),
    repo: CostoPersonalRepository = Depends(get_costo_personal_repository)
):
    """
    Obtener costo de personal de un mes/año específico
    
    Returns:
        Costo de personal del mes indicado
    
    Raises:
        404: Si no existe costo para ese mes/año
    """
    try:
        costo = repo.get_by_mes_año(month, year)
        
        if not costo:
            raise HTTPException(
                status_code=404, 
                detail=f"No existe costo de personal para {month}/{year}"
            )
        
        return costo
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener costo: {str(e)}")

@router.post("", response_model=CostoPersonalResponse, status_code=201)
async def upsert_costo_personal(
    costo_data: CostoPersonalCreate,
    repo: CostoPersonalRepository = Depends(get_costo_personal_repository)
):
    """
    Crear o actualizar costo de personal (upsert)
    
    Si ya existe un costo para el mes/año indicado, se actualiza.
    Si no existe, se crea uno nuevo.
    
    Returns:
        Costo de personal creado/actualizado
    """
    try:
        costo = repo.upsert(
            mes=costo_data.mes,
            año=costo_data.año,
            sueldos_netos=costo_data.sueldos_netos,
            coste_empresa=costo_data.coste_empresa,
            notas=costo_data.notas
        )
        
        return costo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar costo: {str(e)}")

@router.delete("/{id}", status_code=204)
async def delete_costo_personal(
    id: int,
    repo: CostoPersonalRepository = Depends(get_costo_personal_repository)
):
    """
    Eliminar un costo de personal
    
    Args:
        id: ID del costo a eliminar
    
    Raises:
        404: Si no existe el costo con ese ID
    """
    try:
        deleted = repo.delete(id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Costo con ID {id} no encontrado")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar costo: {str(e)}")

@router.get("/{year}/totales", response_model=CostoPersonalTotalesResponse)
async def get_totales_by_year(
    year: int = Path(..., ge=2000, le=2100, description="Año a consultar"),
    repo: CostoPersonalRepository = Depends(get_costo_personal_repository)
):
    """
    Obtener totales de costos de personal de un año
    
    Returns:
        Totales de sueldos netos, coste empresa y total personal del año
    """
    try:
        totales = repo.get_total_by_año(year)
        return totales
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular totales: {str(e)}")

