"""
Utilidades para procesamiento de archivos PDF
"""
import os
import base64
from pathlib import Path
from typing import Optional
from pdf2image import convert_from_path
from PIL import Image
import io

from src.logging_conf import get_logger

logger = get_logger(__name__, component="backend")

def validate_pdf(pdf_path: str) -> bool:
    """
    Validar que un archivo es un PDF válido (verificar magic bytes)
    
    Args:
        pdf_path: Ruta al archivo PDF
    
    Returns:
        True si es un PDF válido, False en caso contrario
    """
    try:
        path = Path(pdf_path)
        if not path.exists():
            logger.warning(f"Archivo no existe: {pdf_path}")
            return False
        
        # Leer primeros 4 bytes para verificar magic bytes %PDF-
        with open(pdf_path, 'rb') as f:
            header = f.read(5)
            if header != b'%PDF-':
                logger.warning(f"Archivo no es un PDF válido: {pdf_path}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error validando PDF {pdf_path}: {e}")
        return False

def get_num_pages(pdf_path: str) -> int:
    """
    Obtener número de páginas del PDF
    
    Args:
        pdf_path: Ruta al archivo PDF
    
    Returns:
        Número de páginas (0 si hay error)
    """
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except ImportError:
        # Fallback: usar pdf2image para contar
        try:
            images = convert_from_path(pdf_path)
            return len(images)
        except Exception:
            logger.warning(f"No se pudo contar páginas de {pdf_path}, asumiendo 1 página")
            return 1
    except Exception as e:
        logger.warning(f"Error contando páginas de {pdf_path}: {e}, asumiendo 1 página")
        return 1

def get_pdf_info(pdf_path: str) -> dict:
    """
    Obtener información básica del PDF
    
    Args:
        pdf_path: Ruta al archivo PDF
    
    Returns:
        Diccionario con información del PDF (páginas, tamaño)
    """
    try:
        path = Path(pdf_path)
        
        if not path.exists():
            return {'error': 'Archivo no existe'}
        
        # Obtener tamaño del archivo
        file_size = path.stat().st_size
        
        # Contar páginas
        num_pages = get_num_pages(pdf_path)
        
        return {
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'num_pages': num_pages,
            'path': str(path.absolute())
        }
    except Exception as e:
        logger.error(f"Error obteniendo info de PDF {pdf_path}: {e}")
        return {'error': str(e)}

def pdf_to_image(pdf_path: str, page: int = 1, dpi: int = 200) -> Optional[Image.Image]:
    """
    Convertir página de PDF a imagen PIL
    
    Args:
        pdf_path: Ruta al archivo PDF
        page: Número de página (1-indexed)
        dpi: Resolución de la imagen
    
    Returns:
        Objeto PIL.Image o None si falla
    """
    try:
        images = convert_from_path(
            pdf_path,
            first_page=page,
            last_page=page,
            dpi=dpi
        )
        
        if not images:
            logger.warning(f"No se pudo convertir página {page} de {pdf_path}")
            return None
        
        img = images[0]
        
        # Redimensionar si es muy grande (optimización)
        max_size = 2000
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Imagen redimensionada a {new_size}")
        
        return img
    except Exception as e:
        logger.error(f"Error convirtiendo PDF a imagen {pdf_path}: {e}")
        return None

def pdf_to_base64(pdf_path: str, page: int = 1, dpi: int = 200) -> Optional[str]:
    """
    Convertir página de PDF a imagen en base64 (para Ollama)
    
    Args:
        pdf_path: Ruta al archivo PDF
        page: Número de página (1-indexed)
        dpi: Resolución de la imagen
    
    Returns:
        String base64 de la imagen o None si falla
    """
    try:
        img = pdf_to_image(pdf_path, page, dpi)
        
        if img is None:
            return None
        
        # Convertir a base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        logger.debug(f"PDF convertido a base64: {len(img_base64)} caracteres")
        
        return img_base64
    except Exception as e:
        logger.error(f"Error convirtiendo PDF a base64 {pdf_path}: {e}")
        return None

def cleanup_temp_file(file_path: str):
    """
    Eliminar archivo temporal de forma segura
    
    Args:
        file_path: Ruta al archivo a eliminar
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.debug(f"Archivo temporal eliminado: {file_path}")
    except Exception as e:
        logger.warning(f"No se pudo eliminar archivo temporal {file_path}: {e}")
