"""
API endpoints para gestión de proveedores
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from src.db.database import Database
from src.db.models import Proveedor, ProveedorMaestro, Factura
from sqlalchemy import func, or_

router = APIRouter(prefix="/proveedores", tags=["proveedores"])

# Schemas
class ProveedorBase(BaseModel):
    nombre: str
    categoria: Optional[str] = None
    nif_cif: Optional[str] = None
    email_contacto: Optional[str] = None

class ProveedorResponse(ProveedorBase):
    id: int
    total_facturas: int
    total_importe: float
    
    class Config:
        from_attributes = True

class ProveedorUpdate(BaseModel):
    categoria: Optional[str] = None
    nif_cif: Optional[str] = None
    email_contacto: Optional[str] = None

# Dependency
def get_db():
    db = Database()
    try:
        with db.get_session() as session:
            yield session
    finally:
        db.close()

@router.get("", response_model=List[ProveedorResponse])
async def listar_proveedores(
    letra: Optional[str] = Query(None, description="Filtrar por letra inicial"),
    search: Optional[str] = Query(None, description="Buscar por nombre"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session = Depends(get_db)
):
    """
    Listar todos los proveedores maestros con sus estadísticas
    """
    from sqlalchemy import select
    
    # Query base usando ProveedorMaestro
    query = select(
        ProveedorMaestro.id,
        ProveedorMaestro.nombre_canonico.label('nombre'),
        ProveedorMaestro.categoria,
        ProveedorMaestro.nif_cif,
        ProveedorMaestro.total_facturas,
        ProveedorMaestro.total_importe
    ).where(
        ProveedorMaestro.activo == True
    )
    
    # Filtros
    if letra:
        query = query.where(func.upper(ProveedorMaestro.nombre_canonico).like(f'{letra.upper()}%'))
    
    if search:
        query = query.where(ProveedorMaestro.nombre_canonico.ilike(f'%{search}%'))
    
    if categoria:
        query = query.where(ProveedorMaestro.categoria == categoria)
    
    # Ordenar por nombre
    query = query.order_by(ProveedorMaestro.nombre_canonico)
    
    # Paginación
    query = query.offset(skip).limit(limit)
    
    result = session.execute(query)
    proveedores = []
    
    for row in result:
        proveedores.append(ProveedorResponse(
            id=row.id,
            nombre=row.nombre,
            categoria=row.categoria,
            nif_cif=row.nif_cif,
            email_contacto=None,  # ProveedorMaestro no tiene email_contacto
            total_facturas=row.total_facturas or 0,
            total_importe=float(row.total_importe) if row.total_importe else 0.0
        ))
    
    return proveedores

@router.get("/autocomplete", response_model=List[dict])
async def autocomplete_proveedores(
    q: str = Query(..., min_length=1, description="Texto de búsqueda"),
    limit: int = Query(10, ge=1, le=50, description="Límite de resultados"),
    session = Depends(get_db)
):
    """
    Autocompletado de proveedores maestros
    Busca en nombre_canonico y nombres_alternativos (JSONB)
    IMPORTANTE: Esta ruta debe estar ANTES de /{proveedor_id} para evitar conflictos
    """
    if not q or len(q.strip()) < 1:
        return []
    
    search_term = q.strip().upper()
    
    # Obtener todos los proveedores activos
    all_proveedores = session.query(ProveedorMaestro).filter(
        ProveedorMaestro.activo == True
    ).all()
    
    results = []
    for prov in all_proveedores:
        # Buscar en nombre_canonico (case insensitive, contiene)
        nombre_match = False
        if prov.nombre_canonico:
            nombre_match = search_term in prov.nombre_canonico.upper()
        
        # Buscar en nombres_alternativos (JSONB array)
        match_in_alternativos = False
        if prov.nombres_alternativos:
            for alt in prov.nombres_alternativos:
                if isinstance(alt, str) and search_term in alt.upper():
                    match_in_alternativos = True
                    break
        
        # Si hay match en nombre o alternativos, agregar a resultados
        if nombre_match or match_in_alternativos:
            results.append({
                "id": prov.id,
                "nombre": prov.nombre_canonico,
                "categoria": prov.categoria,
                "nif_cif": prov.nif_cif,
                "match_en_alternativos": match_in_alternativos
            })
    
    # Ordenar por nombre y limitar
    results.sort(key=lambda x: x['nombre'])
    return results[:limit]

@router.get("/{proveedor_id}", response_model=ProveedorResponse)
async def obtener_proveedor(
    proveedor_id: int,
    session = Depends(get_db)
):
    """
    Obtener un proveedor maestro específico con sus estadísticas
    """
    proveedor = session.query(ProveedorMaestro).filter(
        ProveedorMaestro.id == proveedor_id,
        ProveedorMaestro.activo == True
    ).first()
    
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    return ProveedorResponse(
        id=proveedor.id,
        nombre=proveedor.nombre_canonico,
        categoria=proveedor.categoria,
        nif_cif=proveedor.nif_cif,
        email_contacto=None,  # ProveedorMaestro no tiene email_contacto
        total_facturas=proveedor.total_facturas or 0,
        total_importe=float(proveedor.total_importe) if proveedor.total_importe else 0.0
    )

@router.put("/proveedores/{proveedor_id}")
async def actualizar_proveedor(
    proveedor_id: int,
    proveedor_update: ProveedorUpdate,
    session = Depends(get_db)
):
    """
    Actualizar información de un proveedor maestro (principalmente categoría)
    """
    proveedor = session.query(ProveedorMaestro).filter(
        ProveedorMaestro.id == proveedor_id,
        ProveedorMaestro.activo == True
    ).first()
    
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Actualizar campos
    if proveedor_update.categoria is not None:
        proveedor.categoria = proveedor_update.categoria
    if proveedor_update.nif_cif is not None:
        proveedor.nif_cif = proveedor_update.nif_cif
    
    session.commit()
    session.refresh(proveedor)
    
    return {"message": "Proveedor actualizado", "id": proveedor.id}

@router.get("/proveedores/stats/categorias")
async def estadisticas_categorias(
    session = Depends(get_db)
):
    """
    Obtener estadísticas por categoría (usando proveedores maestros)
    """
    from sqlalchemy import select, func
    
    query = select(
        ProveedorMaestro.categoria,
        func.count(ProveedorMaestro.id).label('total_proveedores')
    ).where(
        ProveedorMaestro.activo == True
    ).group_by(
        ProveedorMaestro.categoria
    ).order_by(
        func.count(ProveedorMaestro.id).desc()
    )
    
    result = session.execute(query)
    
    stats = []
    for row in result:
        stats.append({
            'categoria': row.categoria or 'Sin categoría',
            'total_proveedores': row.total_proveedores
        })
    
    return stats
