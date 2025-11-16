"""
Normalización y validación de datos extraídos de facturas
"""
import re
from datetime import datetime, timedelta, date
from typing import Optional, Dict
from decimal import Decimal

try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False

from src.logging_conf import get_logger
from src.utils.hash_generator import generate_content_hash

logger = get_logger(__name__, component="backend")

def normalize_date(date_str: str) -> Optional[str]:
    """
    Normalizar fecha a formato ISO YYYY-MM-DD
    
    Args:
        date_str: Cadena de fecha en varios formatos posibles
    
    Returns:
        Fecha en formato ISO o None si no se puede parsear
    """
    if not date_str:
        return None
    
    # Limpiar espacios
    date_str = date_str.strip()
    
    # Patrones comunes de fecha
    patterns = [
        # YYYY-MM-DD o YYYY/MM/DD
        (r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', '%Y-%m-%d'),
        # DD-MM-YYYY o DD/MM/YYYY
        (r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', '%d-%m-%Y'),
        # DD.MM.YYYY
        (r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '%d.%m.%Y'),
    ]
    
    for pattern, format_str in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                # Para formato YYYY-MM-DD
                if format_str == '%Y-%m-%d':
                    year, month, day = match.groups()
                    date_obj = datetime(int(year), int(month), int(day))
                # Para formatos DD-MM-YYYY
                elif format_str in ['%d-%m-%Y', '%d.%m.%Y']:
                    day, month, year = match.groups()
                    date_obj = datetime(int(year), int(month), int(day))
                else:
                    # Usar strptime para otros casos
                    date_obj = datetime.strptime(date_str, format_str)
                
                return date_obj.strftime('%Y-%m-%d')
            except (ValueError, IndexError) as e:
                logger.debug(f"No se pudo parsear fecha {date_str} con formato {format_str}: {e}")
                continue
    
    # Si dateparser está disponible, intentar parsear fechas en texto natural
    if DATEPARSER_AVAILABLE:
        try:
            # Configurar dateparser para español
            parsed_date = dateparser.parse(
                date_str,
                languages=['es', 'en'],
                settings={
                    'DATE_ORDER': 'DMY',  # Día-Mes-Año (formato español)
                    'PREFER_DAY_OF_MONTH': 'first',
                    'PREFER_DATES_FROM': 'past'
                }
            )
            
            if parsed_date:
                return parsed_date.strftime('%Y-%m-%d')
        except Exception as e:
            logger.debug(f"dateparser falló para '{date_str}': {e}")
    
    logger.warning(f"No se pudo normalizar fecha: {date_str}")
    return None

def normalize_amount(amount_str: str) -> Optional[float]:
    """
    Normalizar string de importe a float
    
    Args:
        amount_str: Cadena con importe (ej: "1.234,56" o "1,234.56")
    
    Returns:
        Float o None si no se puede parsear
    """
    if not amount_str:
        return None
    
    # Si ya es número
    if isinstance(amount_str, (int, float)):
        return float(amount_str)
    
    # Limpiar string
    amount_str = str(amount_str).strip()
    
    # Remover símbolos de moneda y espacios
    amount_str = re.sub(r'[€$£\s]', '', amount_str)
    
    # Detectar formato: europeo (1.234,56) vs americano (1,234.56)
    # Si tiene punto antes de la coma, es formato europeo
    if ',' in amount_str and '.' in amount_str:
        if amount_str.rindex('.') < amount_str.rindex(','):
            # Formato europeo: 1.234,56
            amount_str = amount_str.replace('.', '').replace(',', '.')
        else:
            # Formato americano: 1,234.56
            amount_str = amount_str.replace(',', '')
    elif ',' in amount_str:
        # Solo coma: asumir formato europeo si tiene 2 dígitos después
        parts = amount_str.split(',')
        if len(parts) == 2 and len(parts[1]) == 2:
            amount_str = amount_str.replace(',', '.')
        else:
            amount_str = amount_str.replace(',', '')
    
    try:
        return float(amount_str)
    except ValueError as e:
        logger.warning(f"No se pudo normalizar importe: {amount_str} - {e}")
        return None

def validate_fiscal_rules(data: dict) -> bool:
    """
    Validar reglas fiscales de la factura
    
    Args:
        data: Diccionario con datos de la factura
    
    Returns:
        True si pasa todas las validaciones, False en caso contrario
    """
    errors = []
    
    # 1. Importe total debe existir y ser > 0
    importe_total = data.get('importe_total')
    if importe_total is None or importe_total <= 0:
        errors.append("importe_total debe ser > 0")
    
    # 2. Drive file ID debe existir
    drive_file_id = data.get('drive_file_id')
    if not drive_file_id or not drive_file_id.strip():
        errors.append("drive_file_id es obligatorio")
    
    # 2.1. Proveedor/Emisor debe existir (OBLIGATORIO)
    proveedor_text = data.get('proveedor_text')
    if not proveedor_text or not proveedor_text.strip():
        errors.append("proveedor_text es obligatorio (nombre del emisor de la factura)")
    
    # 3. Extractor debe ser válido
    extractor = data.get('extractor')
    if extractor not in ['ollama', 'tesseract', 'openai', 'hybrid']:
        errors.append("extractor debe ser 'ollama', 'tesseract', 'openai' o 'hybrid'")
    
    # 4. Confianza debe ser válida
    confianza = data.get('confianza')
    if confianza not in ['alta', 'media', 'baja', None]:
        errors.append("confianza debe ser 'alta', 'media' o 'baja'")
    
    # 5. Si existen base_imponible e impuestos_total, validar suma
    base_imponible = data.get('base_imponible')
    impuestos_total = data.get('impuestos_total')
    
    if base_imponible is not None and impuestos_total is not None and importe_total is not None:
        suma = float(base_imponible) + float(impuestos_total)
        diferencia = abs(suma - float(importe_total))
        
        if diferencia > 0.02:  # Tolerancia de 2 céntimos
            errors.append(
                f"base_imponible ({base_imponible}) + impuestos_total ({impuestos_total}) "
                f"!= importe_total ({importe_total}), diferencia: {diferencia:.2f}"
            )
    
    # 6. Fecha emisión no puede ser futura (+ 1 día de tolerancia)
    fecha_emision = data.get('fecha_emision')
    if fecha_emision:
        try:
            # Aceptar tanto string ISO como objeto date/datetime
            if isinstance(fecha_emision, str):
                fecha_obj = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
            elif isinstance(fecha_emision, date):
                fecha_obj = datetime.combine(fecha_emision, datetime.min.time())
            elif isinstance(fecha_emision, datetime):
                fecha_obj = fecha_emision
            else:
                errors.append(f"fecha_emision tiene tipo inválido: {type(fecha_emision)}")
                fecha_obj = None
            
            if fecha_obj:
                hoy = datetime.now()
                if fecha_obj > hoy + timedelta(days=1):
                    errors.append(f"fecha_emision ({fecha_emision}) es futura")
        except (ValueError, TypeError, AttributeError) as e:
            errors.append(f"fecha_emision ({fecha_emision}) tiene formato inválido: {e}")
    
    # 7. Moneda debe tener 3 caracteres
    moneda = data.get('moneda')
    if moneda and len(moneda) != 3:
        errors.append(f"moneda debe tener 3 caracteres, tiene {len(moneda)}")
    
    # Logear errores
    if errors:
        logger.warning(f"Validación fiscal falló: {', '.join(errors)}")
        return False
    
    return True

def create_factura_dto(raw_data: dict, metadata: dict) -> dict:
    """
    Crear DTO (Data Transfer Object) de factura listo para insertar en DB
    
    Args:
        raw_data: Datos crudos extraídos del OCR
        metadata: Metadatos del archivo (drive info, etc.)
    
    Returns:
        Diccionario con datos normalizados y validados
    """
    # Usar nombre_proveedor para proveedor_text (CORRECTO: proveedor es quien emite)
    # Si no existe nombre_proveedor, la factura será marcada como problemática
    if raw_data.get('nombre_proveedor'):
        raw_data['proveedor_text'] = raw_data['nombre_proveedor']
    elif raw_data.get('proveedor_text'):
        # Ya existe proveedor_text, mantenerlo
        pass
    else:
        # No hay proveedor_text ni nombre_proveedor - será validado después
        raw_data['proveedor_text'] = None
    
    # Normalizar fecha (convertir string ISO a date object)
    fecha_emision = None
    if raw_data.get('fecha_emision'):
        fecha_str = normalize_date(raw_data['fecha_emision'])
        if fecha_str:
            try:
                # Convertir string ISO (YYYY-MM-DD) a date object
                from datetime import date as date_type
                fecha_emision = date_type.fromisoformat(fecha_str)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error convirtiendo fecha_emision a date: {fecha_str} - {e}")
                fecha_emision = None
    
    # Normalizar importes
    importe_total = raw_data.get('importe_total')
    if isinstance(importe_total, str):
        importe_total = normalize_amount(importe_total)
    
    base_imponible = raw_data.get('base_imponible')
    if isinstance(base_imponible, str):
        base_imponible = normalize_amount(base_imponible)
    
    impuestos_total = raw_data.get('impuestos_total')
    if isinstance(impuestos_total, str):
        impuestos_total = normalize_amount(impuestos_total)
    
    iva_porcentaje = raw_data.get('iva_porcentaje')
    if isinstance(iva_porcentaje, str):
        iva_porcentaje = normalize_amount(iva_porcentaje)
    
    # Calcular hash de contenido para detección de duplicados
    hash_contenido = generate_content_hash(
        proveedor_text=raw_data.get('proveedor_text'),
        numero_factura=raw_data.get('numero_factura'),
        fecha_emision=fecha_emision,
        importe_total=importe_total
    )
    
    # Construir DTO
    dto = {
        # Campos de Drive
        'drive_file_id': metadata.get('drive_file_id'),
        'drive_file_name': metadata.get('drive_file_name'),
        'drive_folder_name': metadata.get('drive_folder_name', 'unknown'),
        'drive_modified_time': metadata.get('drive_modified_time'),
        
        # Campos extraídos
        'proveedor_text': raw_data.get('proveedor_text'),
        'numero_factura': raw_data.get('numero_factura'),
        'moneda': raw_data.get('moneda', 'EUR'),
        'fecha_emision': fecha_emision,
        'fecha_recepcion': datetime.utcnow(),
        
        # Importes
        'base_imponible': base_imponible,
        'impuestos_total': impuestos_total,
        'iva_porcentaje': iva_porcentaje,
        'importe_total': importe_total,
        
        # Metadatos
        'conceptos_json': raw_data.get('conceptos_json'),
        # Agregar nombre_cliente a metadatos (no se muestra en dashboard)
        'metadatos_json': {
            **metadata,
            'nombre_cliente': raw_data.get('nombre_cliente')  # Cliente que recibe la factura
        },
        
        # Control
        'pagina_analizada': metadata.get('page', 1),
        'extractor': metadata.get('extractor', 'unknown'),
        'confianza': raw_data.get('confianza', 'baja'),
        'hash_contenido': hash_contenido,
        'revision': 1,
        'estado': 'procesado'
    }
    
    # Validar antes de retornar
    if not validate_fiscal_rules(dto):
        logger.warning(f"DTO no pasó validación fiscal: {dto.get('drive_file_name')}")
        dto['estado'] = 'revisar'
    
    return dto

def sanitize_text(text: str, max_length: int = 500) -> Optional[str]:
    """
    Sanitizar texto para almacenamiento seguro
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima
    
    Returns:
        Texto sanitizado o None
    """
    if not text:
        return None
    
    # Convertir a string si no lo es
    text = str(text).strip()
    
    # Remover caracteres de control
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Truncar si es muy largo
    if len(text) > max_length:
        text = text[:max_length] + '...'
    
    return text if text else None
