"""
Utilidades para validar espacio en disco
"""
import os
import shutil
from pathlib import Path
from typing import Tuple
from src.logging_conf import get_logger

logger = get_logger(__name__, component="backend")


def check_disk_space(
    min_percent: int = 10,
    critical_percent: int = 5,
    path: str = None
) -> Tuple[bool, bool, float, float]:
    """
    Verificar espacio disponible en disco
    
    Args:
        min_percent: Porcentaje mínimo para advertencia (default: 10)
        critical_percent: Porcentaje crítico para error (default: 5)
        path: Ruta a verificar (default: directorio actual)
    
    Returns:
        Tuple: (has_space, is_critical, available_gb, total_gb)
            - has_space: True si hay espacio suficiente (>= critical_percent)
            - is_critical: True si está en nivel crítico (< critical_percent)
            - available_gb: Espacio disponible en GB
            - total_gb: Espacio total en GB
    """
    if path is None:
        path = os.getcwd()
    
    # Obtener uso de disco
    total, used, free = shutil.disk_usage(path)
    
    # Convertir a GB
    total_gb = total / (1024 ** 3)
    available_gb = free / (1024 ** 3)
    used_gb = used / (1024 ** 3)
    
    # Calcular porcentaje disponible
    percent_available = (free / total) * 100 if total > 0 else 0
    
    # Determinar estado
    is_critical = percent_available < critical_percent
    is_warning = percent_available < min_percent
    has_space = not is_critical
    
    # Log según nivel
    if is_critical:
        logger.error(
            f"Espacio en disco CRÍTICO: {percent_available:.1f}% disponible "
            f"({available_gb:.2f} GB de {total_gb:.2f} GB)"
        )
    elif is_warning:
        logger.warning(
            f"Espacio en disco bajo: {percent_available:.1f}% disponible "
            f"({available_gb:.2f} GB de {total_gb:.2f} GB)"
        )
    else:
        logger.debug(
            f"Espacio en disco: {percent_available:.1f}% disponible "
            f"({available_gb:.2f} GB de {total_gb:.2f} GB)"
        )
    
    return has_space, is_critical, available_gb, total_gb

