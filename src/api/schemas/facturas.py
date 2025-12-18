"""
Schemas para endpoints de facturas
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal


class FacturaSummaryResponse(BaseModel):
    """Response del endpoint summary"""
    total_facturas: int = Field(..., description="Total de facturas del mes")
    facturas_exitosas: int = Field(..., description="Facturas procesadas exitosamente")
    facturas_fallidas: int = Field(..., description="Facturas con error o para revisar")
    importe_total: float = Field(..., description="Importe total del mes")
    promedio_factura: float = Field(..., description="Promedio por factura")
    proveedores_activos: int = Field(..., description="Número de proveedores únicos")
    confianza_extraccion: float = Field(..., description="Confianza promedio de extracción (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_facturas": 45,
                "facturas_exitosas": 42,
                "facturas_fallidas": 3,
                "importe_total": 12500.50,
                "promedio_factura": 297.63,
                "proveedores_activos": 8,
                "confianza_extraccion": 87.5
            }
        }


class FacturaByDayItem(BaseModel):
    """Item del array by_day"""
    dia: int = Field(..., ge=1, le=31, description="Día del mes")
    cantidad: int = Field(..., description="Cantidad de facturas del día")
    importe_total: float = Field(..., description="Importe total del día")
    importe_iva: float = Field(..., description="Importe de IVA del día")


class FacturaByDayResponse(BaseModel):
    """Response del endpoint by_day"""
    data: List[FacturaByDayItem]


class ManualFacturaCreate(BaseModel):
    """Schema para creación manual de factura"""
    drive_file_name: str = Field(..., description="Nombre del archivo (para detección de duplicados)")
    proveedor_text: str = Field(..., description="Nombre del proveedor (obligatorio)")
    fecha_emision: date = Field(..., description="Fecha de emisión de la factura (obligatorio)")
    importe_total: Decimal = Field(..., description="Importe total de la factura (obligatorio)")
    impuestos_total: Decimal = Field(..., description="Total de impuestos (obligatorio)")
    numero_factura: Optional[str] = Field(None, description="Número de factura (opcional)")
    # base_imponible se calcula automáticamente: importe_total - impuestos_total
    # iva_porcentaje se calcula automáticamente si es necesario
    # moneda siempre será EUR, no se envía desde frontend

    @validator('importe_total', 'impuestos_total')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('Debe ser mayor que 0')
        return v

    @validator('impuestos_total')
    def validate_impuestos_less_than_total(cls, v, values):
        """Validar que impuestos no sea mayor que el total"""
        if 'importe_total' in values:
            total = values.get('importe_total', 0)
            if v > total:
                raise ValueError(f'Los impuestos ({v}) no pueden ser mayores que el importe total ({total})')
        return v

    @validator('importe_total')
    def validate_total_greater_than_impuestos(cls, v, values):
        """Validar que el total sea mayor o igual a los impuestos"""
        impuestos = values.get('impuestos_total', 0)
        if v < impuestos:
            raise ValueError(f'El importe total ({v}) debe ser mayor o igual a los impuestos ({impuestos})')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "drive_file_name": "Fact NEGRINI sep 25.pdf",
                "proveedor_text": "NEGRINI S.L.",
                "fecha_emision": "2025-09-15",
                "importe_total": 1234.56,
                "base_imponible": 1020.30,
                "impuestos_total": 214.26,
                "iva_porcentaje": 21.0,
                "numero_factura": "FAC-2025-001",
                "moneda": "EUR"
            }
        }


class FacturaRecentItem(BaseModel):
    """Item del array recent"""
    id: int = Field(..., description="ID de la factura")
    numero_factura: Optional[str] = Field(None, description="Número de factura")
    proveedor_nombre: Optional[str] = Field(None, description="Nombre del proveedor")
    fecha_emision: Optional[date] = Field(None, description="Fecha de emisión")
    importe_base: Optional[float] = Field(None, description="Base imponible")
    importe_iva: Optional[float] = Field(None, description="Importe de IVA")
    importe_total: Optional[float] = Field(None, description="Importe total")


class FacturaRecentResponse(BaseModel):
    """Response del endpoint recent"""
    data: List[FacturaRecentItem]


class CategoryBreakdownItem(BaseModel):
    """Item del array categories"""
    categoria: str = Field(..., description="Nombre de la categoría (proveedor)")
    cantidad: int = Field(..., description="Cantidad de facturas")
    importe_total: float = Field(..., description="Importe total")


class CategoryBreakdownResponse(BaseModel):
    """Response del endpoint categories"""
    data: List[CategoryBreakdownItem]


class SyncStatusResponse(BaseModel):
    """Response del endpoint sync-status"""
    last_sync: Optional[str] = Field(None, description="Timestamp ISO de última sincronización")
    updated_at: Optional[str] = Field(None, description="Fecha de última actualización")


class FailedInvoiceItem(BaseModel):
    """Item del array failed"""
    nombre: str = Field(..., description="Nombre del archivo fallido")
    razon: Optional[str] = Field(None, description="Razón por la que fue enviada a cuarentena o marcada como fallida")


class FailedInvoicesResponse(BaseModel):
    """Response del endpoint failed"""
    data: List[FailedInvoiceItem]


class FacturaListItem(BaseModel):
    """Item de la lista completa de facturas"""
    id: int = Field(..., description="ID de la factura")
    proveedor_nombre: Optional[str] = Field(None, description="Nombre del proveedor")
    categoria: Optional[str] = Field(None, description="Categoría (nombre de carpeta)")
    fecha_emision: Optional[str] = Field(None, description="Fecha de emisión (ISO format)")
    impuestos_total: float = Field(0.0, description="Total de impuestos")
    importe_total: float = Field(0.0, description="Total pagado")


class FacturaListResponse(BaseModel):
    """Response del endpoint list (todas las facturas del mes)"""
    data: List[FacturaListItem]

