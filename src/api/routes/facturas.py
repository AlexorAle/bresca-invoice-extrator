"""
Endpoints para facturas
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from src.api.dependencies import get_factura_repository
from src.api.schemas.facturas import (
    FacturaSummaryResponse,
    FacturaByDayResponse,
    FacturaByDayItem,
    FacturaRecentResponse,
    FacturaRecentItem,
    CategoryBreakdownResponse,
    CategoryBreakdownItem,
    FailedInvoicesResponse,
    FailedInvoiceItem,
    FacturaListResponse,
    FacturaListItem,
)
from src.db.repositories import FacturaRepository

router = APIRouter(prefix="/facturas", tags=["facturas"])


@router.get("/summary", response_model=FacturaSummaryResponse)
async def get_summary(
    month: int = Query(..., ge=1, le=12, description="Mes (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Año"),
    repo: FacturaRepository = Depends(get_factura_repository)
):
    """
    Obtener resumen de facturas del mes seleccionado
    """
    try:
        summary = repo.get_summary_by_month(month, year)
        return FacturaSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")


@router.get("/by_day", response_model=FacturaByDayResponse)
async def get_by_day(
    month: int = Query(..., ge=1, le=12, description="Mes (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Año"),
    repo: FacturaRepository = Depends(get_factura_repository)
):
    """
    Obtener facturas agrupadas por día del mes
    """
    try:
        by_day = repo.get_facturas_by_day(month, year)
        items = [FacturaByDayItem(**item) for item in by_day]
        return FacturaByDayResponse(data=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos por día: {str(e)}")


@router.get("/recent", response_model=FacturaRecentResponse)
async def get_recent(
    month: int = Query(..., ge=1, le=12, description="Mes (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Año"),
    limit: int = Query(5, ge=1, le=100, description="Límite de facturas"),
    repo: FacturaRepository = Depends(get_factura_repository)
):
    """
    Obtener facturas recientes del mes
    """
    try:
        recent = repo.get_recent_facturas(month, year, limit)
        items = []
        for item in recent:
            # Convertir fecha_emision a date si es datetime
            fecha_emision = item.get('fecha_emision')
            if fecha_emision and hasattr(fecha_emision, 'date'):
                fecha_emision = fecha_emision.date()
            elif fecha_emision and isinstance(fecha_emision, str):
                from datetime import datetime
                fecha_emision = datetime.fromisoformat(fecha_emision).date()
            
            items.append(FacturaRecentItem(
                id=item['id'],
                numero_factura=item.get('numero_factura'),
                proveedor_nombre=item.get('proveedor_nombre'),
                fecha_emision=fecha_emision,
                importe_base=item.get('importe_base'),
                importe_iva=item.get('importe_iva'),
                importe_total=item.get('importe_total')
            ))
        return FacturaRecentResponse(data=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener facturas recientes: {str(e)}")


@router.get("/list", response_model=FacturaListResponse)
async def get_all_facturas(
    month: int = Query(..., ge=1, le=12, description="Mes (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Año"),
    repo: FacturaRepository = Depends(get_factura_repository)
):
    """
    Obtener todas las facturas del mes
    """
    try:
        facturas = repo.get_all_facturas_by_month(month, year)
        items = []
        for item in facturas:
            items.append(FacturaListItem(**item))
        
        return FacturaListResponse(data=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener facturas: {str(e)}")


@router.get("/categories", response_model=CategoryBreakdownResponse)
async def get_categories(
    month: int = Query(..., ge=1, le=12, description="Mes (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Año"),
    repo: FacturaRepository = Depends(get_factura_repository)
):
    """
    Obtener desglose por categorías (proveedores)
    """
    try:
        categories = repo.get_categories_breakdown(month, year)
        items = [CategoryBreakdownItem(**item) for item in categories]
        return CategoryBreakdownResponse(data=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener desglose por categorías: {str(e)}")


@router.get("/failed", response_model=FailedInvoicesResponse)
async def get_failed_invoices(
    month: int = Query(..., ge=1, le=12, description="Mes (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Año")
):
    """
    Obtener lista de facturas fallidas del mes seleccionado desde la carpeta de cuarentena
    """
    try:
        import json
        import os
        from pathlib import Path
        from datetime import datetime, date
        from calendar import monthrange
        
        # Ruta de cuarentena
        quarantine_path = Path(os.getenv('QUARANTINE_PATH', 'data/quarantine'))
        
        if not quarantine_path.exists():
            return FailedInvoicesResponse(data=[])
        
        # Calcular rango de fechas del mes
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        
        failed_invoices = []
        
        # Buscar todos los archivos .meta.json en cuarentena
        for meta_file in quarantine_path.glob("*.meta.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                
                # Extraer información del archivo
                file_info = meta_data.get('file_info', {})
                nombre = file_info.get('name', meta_file.stem.replace('.meta', ''))
                
                # Intentar obtener fecha de modificación del archivo en Drive (preferida)
                # Si no está disponible, usar fecha de cuarentena como fallback
                file_date = None
                modified_time = file_info.get('modifiedTime')
                if modified_time:
                    try:
                        # Parsear fecha de modificación de Drive (formato ISO)
                        file_date = datetime.fromisoformat(modified_time.replace('Z', '+00:00')).date()
                    except (ValueError, AttributeError):
                        pass
                
                # Si no hay fecha de modificación, usar fecha de cuarentena como fallback
                if file_date is None:
                    quarantined_at_str = meta_data.get('quarantined_at')
                    if quarantined_at_str:
                        try:
                            file_date = datetime.fromisoformat(quarantined_at_str.replace('Z', '+00:00')).date()
                        except (ValueError, AttributeError):
                            continue
                    else:
                        continue
                
                # Filtrar por mes usando fecha del archivo (modificación o cuarentena)
                if start_date <= file_date <= end_date:
                    failed_invoices.append({
                        'nombre': nombre,
                        'timestamp': modified_time or meta_data.get('quarantined_at', '')
                    })
            
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Si hay error leyendo un archivo, continuar con el siguiente
                continue
        
        # Ordenar por fecha (más recientes primero) y limitar a 10
        failed_invoices.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        failed_invoices = failed_invoices[:10]
        
        # Remover timestamp del resultado final
        items = [FailedInvoiceItem(nombre=item['nombre']) for item in failed_invoices]
        return FailedInvoicesResponse(data=items)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener facturas fallidas: {str(e)}")

