"""
Generador de hash de contenido para detección de duplicados

El hash se genera basándose en:
- proveedor_text
- numero_factura  
- fecha_emision
- importe_total

Esto permite detectar facturas duplicadas incluso si el archivo 
tiene diferente nombre o fue subido múltiples veces.
"""
import hashlib
from typing import Optional
from decimal import Decimal

from src.logging_conf import get_logger

logger = get_logger(__name__)

def normalize_for_hash(value: any) -> str:
    """
    Normalizar un valor para cálculo de hash
    
    Args:
        value: Valor a normalizar (puede ser None, string, number, etc.)
    
    Returns:
        String normalizado para hash
    """
    if value is None:
        return ''
    
    # Convertir a string y limpiar espacios
    value_str = str(value).strip().lower()
    
    # Normalizar espacios múltiples
    import re
    value_str = re.sub(r'\s+', ' ', value_str)
    
    # Para números, normalizar formato (remover separadores)
    if isinstance(value, (int, float, Decimal)):
        # Convertir a float y formatear con 2 decimales
        try:
            value_str = f"{float(value):.2f}"
        except (ValueError, TypeError):
            pass
    
    return value_str

def generate_content_hash(
    proveedor_text: Optional[str],
    numero_factura: Optional[str],
    fecha_emision: Optional[str],
    importe_total: Optional[float]
) -> Optional[str]:
    """
    Generar hash SHA256 de contenido de factura
    
    El hash se calcula concatenando los campos clave normalizados:
    proveedor_text + numero_factura + fecha_emision + importe_total
    
    Args:
        proveedor_text: Nombre del proveedor
        numero_factura: Número de factura
        fecha_emision: Fecha de emisión (formato ISO YYYY-MM-DD)
        importe_total: Importe total de la factura
    
    Returns:
        Hash SHA256 en formato hexadecimal, o None si faltan campos críticos
    
    Examples:
        >>> generate_content_hash("ACME Corp", "INV-001", "2025-01-15", 1250.50)
        'a3f5e2b1c4d8f9e0...'
    """
    # Validar que al menos tengamos número de factura e importe
    # (proveedor y fecha pueden faltar en facturas mal extraídas)
    if not numero_factura and not importe_total:
        logger.debug("No se puede generar hash: faltan número_factura e importe_total")
        return None
    
    # Normalizar cada campo
    proveedor_norm = normalize_for_hash(proveedor_text)
    numero_norm = normalize_for_hash(numero_factura)
    fecha_norm = normalize_for_hash(fecha_emision)
    importe_norm = normalize_for_hash(importe_total)
    
    # Concatenar campos en orden fijo
    content = f"{proveedor_norm}|{numero_norm}|{fecha_norm}|{importe_norm}"
    
    # Generar hash SHA256
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    logger.debug(
        f"Hash generado: {hash_hex[:16]}... para content: {content[:50]}...",
        extra={
            'proveedor': proveedor_text,
            'numero': numero_factura,
            'hash': hash_hex
        }
    )
    
    return hash_hex

def generate_content_hash_from_dto(factura_dto: dict) -> Optional[str]:
    """
    Generar hash de contenido desde un DTO de factura
    
    Args:
        factura_dto: Diccionario con datos de factura
    
    Returns:
        Hash SHA256 o None si faltan campos críticos
    """
    return generate_content_hash(
        proveedor_text=factura_dto.get('proveedor_text'),
        numero_factura=factura_dto.get('numero_factura'),
        fecha_emision=factura_dto.get('fecha_emision'),
        importe_total=factura_dto.get('importe_total')
    )

def validate_hash_completeness(factura_dto: dict) -> tuple:
    """
    Validar si una factura tiene suficientes datos para generar un hash confiable
    
    Args:
        factura_dto: Diccionario con datos de factura
    
    Returns:
        Tupla (es_valido, mensaje)
    """
    issues = []
    
    if not factura_dto.get('numero_factura'):
        issues.append('numero_factura faltante')
    
    if not factura_dto.get('importe_total'):
        issues.append('importe_total faltante')
    
    if not factura_dto.get('proveedor_text'):
        issues.append('proveedor_text faltante (recomendado)')
    
    if not factura_dto.get('fecha_emision'):
        issues.append('fecha_emision faltante (recomendado)')
    
    # Considerar válido si tiene al menos número o importe
    is_valid = bool(factura_dto.get('numero_factura') or factura_dto.get('importe_total'))
    
    if issues:
        mensaje = f"Hash con calidad reducida: {', '.join(issues)}"
    else:
        mensaje = "Hash completo y confiable"
    
    return is_valid, mensaje
