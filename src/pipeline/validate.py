"""
Validaciones de reglas de negocio y duplicados
"""
from typing import Dict, List
from datetime import datetime, date

from src.db.database import Database
from src.db.repositories import FacturaRepository
from src.logging_conf import get_logger

logger = get_logger(__name__, component="backend")

def validate_business_rules(factura: dict) -> bool:
    """
    Validar reglas de negocio de la factura
    
    Args:
        factura: Diccionario con datos de la factura
    
    Returns:
        True si pasa todas las validaciones, False en caso contrario
    """
    errors = []
    
    # 1. Campos obligatorios
    required_fields = ['drive_file_id', 'drive_file_name', 'importe_total', 'extractor']
    for field in required_fields:
        if not factura.get(field):
            errors.append(f"Campo obligatorio faltante: {field}")
    
    # 2. Importe total debe ser positivo
    importe_total = factura.get('importe_total')
    if importe_total is not None:
        try:
            importe_float = float(importe_total)
            if importe_float <= 0:
                errors.append(f"importe_total debe ser > 0, recibido: {importe_float}")
        except (ValueError, TypeError):
            errors.append(f"importe_total debe ser numérico, recibido: {importe_total}")
    
    # 3. Validar moneda (debe ser código ISO de 3 letras)
    moneda = factura.get('moneda')
    if moneda and len(moneda) != 3:
        errors.append(f"moneda debe ser código ISO de 3 letras, recibido: {moneda}")
    
    # 4. Validar confianza
    confianza = factura.get('confianza')
    if confianza and confianza not in ['alta', 'media', 'baja']:
        errors.append(f"confianza debe ser 'alta', 'media' o 'baja', recibido: {confianza}")
    
    # 5. Validar estado
    estado = factura.get('estado')
    if estado and estado not in ['procesado', 'pendiente', 'error', 'revisar', 'duplicado', 'error_permanente']:
        errors.append(f"estado inválido: {estado}")
    
    # 6. Validar coherencia de importes (si existen todos los campos)
    base_imponible = factura.get('base_imponible')
    impuestos_total = factura.get('impuestos_total')
    
    if base_imponible is not None and impuestos_total is not None and importe_total is not None:
        try:
            base = float(base_imponible)
            impuestos = float(impuestos_total)
            total = float(importe_total)
            
            suma = base + impuestos
            diferencia = abs(suma - total)
            
            # Tolerancia de 2 céntimos para errores de redondeo
            if diferencia > 0.02:
                errors.append(
                    f"Incoherencia en importes: base_imponible ({base}) + "
                    f"impuestos_total ({impuestos}) != importe_total ({total}), "
                    f"diferencia: {diferencia:.2f}"
                )
        except (ValueError, TypeError) as e:
            errors.append(f"Error validando coherencia de importes: {e}")
    
    # 7. Validar fecha de emisión (no puede ser futura)
    fecha_emision = factura.get('fecha_emision')
    if fecha_emision:
        try:
            # Manejar diferentes tipos: date, datetime, string ISO
            if isinstance(fecha_emision, date):
                # Ya es un objeto date, convertir a datetime para comparación
                fecha_obj = datetime.combine(fecha_emision, datetime.min.time())
            elif isinstance(fecha_emision, datetime):
                # Ya es datetime
                fecha_obj = fecha_emision
            elif isinstance(fecha_emision, str):
                # String ISO, parsear
                fecha_obj = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
            else:
                errors.append(f"fecha_emision tiene tipo inválido: {type(fecha_emision)}")
                fecha_obj = None
            
            if fecha_obj:
                hoy = datetime.now()
                # Tolerancia de 1 día para diferencias de zona horaria
                if fecha_obj > hoy.replace(hour=23, minute=59, second=59):
                    errors.append(f"fecha_emision es futura: {fecha_emision}")
        except (ValueError, TypeError, AttributeError) as e:
            errors.append(f"fecha_emision tiene formato inválido: {fecha_emision} - {e}")
    
    # Logear errores
    if errors:
        logger.warning(
            f"Validación de negocio falló para {factura.get('drive_file_name')}: {'; '.join(errors)}",
            extra={'drive_file_id': factura.get('drive_file_id')}
        )
        return False
    
    logger.info(
        f"Validación de negocio exitosa: {factura.get('drive_file_name')}",
        extra={'drive_file_id': factura.get('drive_file_id')}
    )
    
    return True

def check_duplicates(factura: dict, db: Database) -> bool:
    """
    Verificar si la factura ya existe en la base de datos
    
    Args:
        factura: Diccionario con datos de la factura
        db: Instancia de Database
    
    Returns:
        True si la factura ya existe (es duplicada), False si es nueva
    """
    drive_file_id = factura.get('drive_file_id')
    
    if not drive_file_id:
        logger.warning("No se puede verificar duplicados sin drive_file_id")
        return False
    
    repo = FacturaRepository(db)
    
    exists = repo.file_exists(drive_file_id)
    
    if exists:
        logger.info(
            f"Factura duplicada detectada: {factura.get('drive_file_name')}",
            extra={'drive_file_id': drive_file_id}
        )
    
    return exists

def validate_file_integrity(file_path: str, expected_size: int = None) -> bool:
    """
    Validar integridad del archivo descargado
    
    Args:
        file_path: Ruta al archivo
        expected_size: Tamaño esperado en bytes (opcional)
    
    Returns:
        True si el archivo es válido, False en caso contrario
    """
    from pathlib import Path
    
    path = Path(file_path)
    
    # Verificar que existe
    if not path.exists():
        logger.error(f"Archivo no existe: {file_path}")
        return False
    
    # Verificar que no está vacío
    size = path.stat().st_size
    if size == 0:
        logger.error(f"Archivo vacío: {file_path}")
        return False
    
    # Verificar tamaño esperado (si se proporciona)
    if expected_size is not None:
        if size != expected_size:
            logger.warning(
                f"Tamaño de archivo no coincide. Esperado: {expected_size}, "
                f"Actual: {size}, Archivo: {file_path}"
            )
            # No retornar False, solo advertir
    
    # Verificar magic bytes de PDF
    with open(file_path, 'rb') as f:
        header = f.read(5)
        if header != b'%PDF-':
            logger.error(f"Archivo no es un PDF válido: {file_path}")
            return False
    
    logger.debug(f"Archivo válido: {file_path} ({size} bytes)")
    return True

def sanitize_filename(filename: str) -> str:
    """
    Sanitizar nombre de archivo para evitar problemas de seguridad
    
    Args:
        filename: Nombre original del archivo
    
    Returns:
        Nombre de archivo sanitizado
    """
    import re
    
    # Remover caracteres peligrosos
    safe_name = re.sub(r'[^\w\s\-\.]', '_', filename)
    
    # Limitar longitud
    if len(safe_name) > 255:
        name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
        safe_name = name[:250] + ('.' + ext if ext else '')
    
    return safe_name
