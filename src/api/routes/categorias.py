"""
API endpoints para gestión de categorías
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from src.db.database import Database
from src.db.models import Categoria
from sqlalchemy import func

router = APIRouter()

# Schemas
class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    color: Optional[str] = '#3b82f6'

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    color: Optional[str] = None
    activo: Optional[bool] = None

class CategoriaResponse(CategoriaBase):
    id: int
    color: str
    activo: bool
    creado_en: str
    actualizado_en: str
    
    class Config:
        from_attributes = True

# Dependency
def get_db():
    db = Database()
    try:
        with db.get_session() as session:
            yield session
    finally:
        db.close()

@router.get("/categorias", response_model=List[CategoriaResponse])
async def listar_categorias(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    search: Optional[str] = Query(None, description="Buscar por nombre"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session = Depends(get_db)
):
    """
    Listar todas las categorías
    """
    query = session.query(Categoria)
    
    # Filtros
    if activo is not None:
        query = query.filter(Categoria.activo == activo)
    else:
        # Por defecto, solo mostrar activas
        query = query.filter(Categoria.activo == True)
    
    if search:
        query = query.filter(Categoria.nombre.ilike(f'%{search}%'))
    
    # Ordenar por nombre
    query = query.order_by(Categoria.nombre)
    
    # Paginación
    categorias = query.offset(skip).limit(limit).all()
    
    return [
        CategoriaResponse(
            id=cat.id,
            nombre=cat.nombre,
            descripcion=cat.descripcion,
            color=cat.color or '#3b82f6',
            activo=cat.activo,
            creado_en=cat.creado_en.isoformat() if cat.creado_en else "",
            actualizado_en=cat.actualizado_en.isoformat() if cat.actualizado_en else ""
        )
        for cat in categorias
    ]

@router.get("/categorias/{categoria_id}", response_model=CategoriaResponse)
async def obtener_categoria(
    categoria_id: int,
    session = Depends(get_db)
):
    """
    Obtener una categoría específica
    """
    categoria = session.query(Categoria).filter(Categoria.id == categoria_id).first()
    
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    return CategoriaResponse(
        id=categoria.id,
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        color=categoria.color or '#3b82f6',
        activo=categoria.activo,
        creado_en=categoria.creado_en.isoformat() if categoria.creado_en else "",
        actualizado_en=categoria.actualizado_en.isoformat() if categoria.actualizado_en else ""
    )

@router.post("/categorias", response_model=CategoriaResponse, status_code=201)
async def crear_categoria(
    categoria_create: CategoriaCreate,
    session = Depends(get_db)
):
    """
    Crear una nueva categoría
    """
    # Verificar si ya existe
    existente = session.query(Categoria).filter(
        func.lower(Categoria.nombre) == func.lower(categoria_create.nombre)
    ).first()
    
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
    
    categoria = Categoria(
        nombre=categoria_create.nombre,
        descripcion=categoria_create.descripcion,
        color=categoria_create.color or '#3b82f6',
        activo=True
    )
    
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    
    return CategoriaResponse(
        id=categoria.id,
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        color=categoria.color or '#3b82f6',
        activo=categoria.activo,
        creado_en=categoria.creado_en.isoformat() if categoria.creado_en else "",
        actualizado_en=categoria.actualizado_en.isoformat() if categoria.actualizado_en else ""
    )

@router.put("/categorias/{categoria_id}", response_model=CategoriaResponse)
async def actualizar_categoria(
    categoria_id: int,
    categoria_update: CategoriaUpdate,
    session = Depends(get_db)
):
    """
    Actualizar una categoría
    """
    categoria = session.query(Categoria).filter(Categoria.id == categoria_id).first()
    
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar nombre único si se está cambiando
    if categoria_update.nombre and categoria_update.nombre != categoria.nombre:
        existente = session.query(Categoria).filter(
            func.lower(Categoria.nombre) == func.lower(categoria_update.nombre),
            Categoria.id != categoria_id
        ).first()
        
        if existente:
            raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
    
    # Actualizar campos
    if categoria_update.nombre is not None:
        categoria.nombre = categoria_update.nombre
    if categoria_update.descripcion is not None:
        categoria.descripcion = categoria_update.descripcion
    if categoria_update.color is not None:
        categoria.color = categoria_update.color
    if categoria_update.activo is not None:
        categoria.activo = categoria_update.activo
    
    session.commit()
    session.refresh(categoria)
    
    return CategoriaResponse(
        id=categoria.id,
        nombre=categoria.nombre,
        descripcion=categoria.descripcion,
        color=categoria.color or '#3b82f6',
        activo=categoria.activo,
        creado_en=categoria.creado_en.isoformat() if categoria.creado_en else "",
        actualizado_en=categoria.actualizado_en.isoformat() if categoria.actualizado_en else ""
    )

@router.delete("/categorias/{categoria_id}", status_code=204)
async def eliminar_categoria(
    categoria_id: int,
    session = Depends(get_db)
):
    """
    Eliminar (desactivar) una categoría
    """
    categoria = session.query(Categoria).filter(Categoria.id == categoria_id).first()
    
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # En lugar de eliminar, desactivamos
    categoria.activo = False
    session.commit()
    
    return None
