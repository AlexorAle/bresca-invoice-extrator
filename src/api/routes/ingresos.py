"""
API endpoints para gestión de ingresos mensuales y análisis de rentabilidad
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
from src.db.database import Database
from src.db.models import IngresoMensual, Factura
from sqlalchemy import func, extract

router = APIRouter(tags=["ingresos"])

# Schemas
class IngresoMensualItem(BaseModel):
    mes: int
    año: int
    ingresos: float
    gastos: float
    rentabilidad: float
    margen: float
    ingreso_cargado: bool
    estado: str  # "positivo", "negativo", "sin_datos"
    
    class Config:
        populate_by_name = True

class RentabilidadResponse(BaseModel):
    meses: List[IngresoMensualItem]
    totales: dict  # {ingresos, gastos, rentabilidad, margen}

class IngresoUpsertRequest(BaseModel):
    mes: int
    año: int
    monto_ingresos: float
    
    class Config:
        # Permitir usar 'año' en el modelo aunque el campo en BD sea 'año'
        populate_by_name = True

# Dependency
def get_db():
    db = Database()
    try:
        with db.get_session() as session:
            yield session
    finally:
        db.close()

@router.get("/rentabilidad/{year}", response_model=RentabilidadResponse)
async def get_rentabilidad(
    year: int,
    session = Depends(get_db)
):
    """
    Obtener análisis de rentabilidad para un año completo
    """
    try:
        meses_data = []
        totales_ingresos = 0
        totales_gastos = 0
        meses_con_datos = 0
        
        # Obtener gastos por mes desde facturas
        gastos_por_mes = {}
        gastos_query = (
            session.query(
                extract('month', Factura.fecha_emision).label('mes'),
                func.sum(Factura.importe_total).label('total_gastos')
            )
            .filter(
                extract('year', Factura.fecha_emision) == year,
                Factura.importe_total.isnot(None),
                Factura.estado == 'procesado',  # Solo facturas procesadas (excluye pendientes)
                ~Factura.estado.in_(['error', 'revisar', 'pendiente'])  # Excluir explícitamente pendientes
            )
            .group_by(extract('month', Factura.fecha_emision))
        )
        
        for row in gastos_query:
            mes = int(row.mes)
            gastos_por_mes[mes] = float(row.total_gastos or 0)
        
        # Obtener ingresos cargados manualmente
        ingresos_cargados = {}
        ingresos_query = session.query(IngresoMensual).filter(
            IngresoMensual.año == year
        ).all()
        
        for ingreso in ingresos_query:
            ingresos_cargados[ingreso.mes] = float(ingreso.monto_ingresos)
        
        # Procesar los 12 meses
        for mes in range(1, 13):
            ingresos = ingresos_cargados.get(mes, 5000.0)  # Default 5000
            gastos = gastos_por_mes.get(mes, 0.0)
            ingreso_cargado = mes in ingresos_cargados
            
            rentabilidad = ingresos - gastos
            margen = (rentabilidad / ingresos * 100) if ingresos > 0 else 0
            
            # Determinar estado
            if not ingreso_cargado:
                estado = "sin_datos"
            elif margen > 0:
                estado = "positivo"
            else:
                estado = "negativo"
            
            meses_data.append(IngresoMensualItem(
                mes=mes,
                año=year,
                ingresos=ingresos,
                gastos=gastos,
                rentabilidad=rentabilidad,
                margen=round(margen, 1),
                ingreso_cargado=ingreso_cargado,
                estado=estado
            ))
            
            # Sumar solo meses con datos cargados para totales
            if ingreso_cargado:
                totales_ingresos += ingresos
                totales_gastos += gastos
                meses_con_datos += 1
        
        # Calcular totales
        totales_rentabilidad = totales_ingresos - totales_gastos
        totales_margen = (totales_rentabilidad / totales_ingresos * 100) if totales_ingresos > 0 else 0
        
        return RentabilidadResponse(
            meses=meses_data,
            totales={
                "ingresos": round(totales_ingresos, 2),
                "gastos": round(totales_gastos, 2),
                "rentabilidad": round(totales_rentabilidad, 2),
                "margen": round(totales_margen, 1)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener rentabilidad: {str(e)}")

@router.put("/upsert", response_model=dict)
async def upsert_ingreso(
    request: IngresoUpsertRequest,
    session = Depends(get_db)
):
    """
    Crear o actualizar un ingreso mensual
    """
    try:
        # Validar mes y año
        if request.mes < 1 or request.mes > 12:
            raise HTTPException(status_code=400, detail="Mes debe estar entre 1 y 12")
        if request.año < 2000 or request.año > 2100:
            raise HTTPException(status_code=400, detail="Año debe estar entre 2000 y 2100")
        if request.monto_ingresos < 0:
            raise HTTPException(status_code=400, detail="El monto de ingresos no puede ser negativo")
        
        # Buscar ingreso existente
        ingreso = session.query(IngresoMensual).filter(
            IngresoMensual.mes == request.mes,
            IngresoMensual.año == request.año
        ).first()
        
        if ingreso:
            # Actualizar
            ingreso.monto_ingresos = Decimal(str(request.monto_ingresos))
        else:
            # Crear nuevo
            ingreso = IngresoMensual(
                mes=request.mes,
                año=request.año,
                monto_ingresos=Decimal(str(request.monto_ingresos))
            )
            session.add(ingreso)
        
        session.commit()
        session.refresh(ingreso)
        
        return {
            "id": ingreso.id,
            "mes": ingreso.mes,
            "año": ingreso.año,
            "monto_ingresos": float(ingreso.monto_ingresos),
            "mensaje": "Ingreso guardado correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar ingreso: {str(e)}")
