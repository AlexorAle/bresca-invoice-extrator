"""
Función para buscar o crear proveedores maestros automáticamente
Sistema multicapa: NIF → Fuzzy → Nuevo
"""
from typing import Dict, Optional
from sqlalchemy.orm import Session

from src.db.models import ProveedorMaestro
from src.utils.proveedor_normalizer_v2 import (
    normalizar_nombre_proveedor,
    calcular_similitud
)

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


def normalizar_y_buscar_proveedor(
    nombre_raw: str,
    nif: Optional[str] = None,
    session: Session = None
) -> Dict:
    """
    Buscar o crear proveedor maestro usando sistema multicapa
    
    Sistema de matching (en orden de prioridad):
    1. NIF/CIF (si está disponible) - 100% confianza
    2. Fuzzy matching con nombres normalizados - score >= 92
    3. Crear nuevo proveedor maestro
    
    Args:
        nombre_raw: Nombre original del proveedor (como viene en la factura)
        nif: NIF/CIF del proveedor (opcional, futuro)
        session: Sesión de SQLAlchemy
    
    Returns:
        {
            'proveedor_maestro_id': int,
            'nombre_canonico': str,
            'metodo': 'nif' | 'fuzzy' | 'nuevo',
            'confianza': float (0-100)
        }
    """
    if not session:
        raise ValueError("Session es requerida")
    
    # CAPA 1: Búsqueda por NIF (prioridad máxima)
    if nif and nif.strip():
        nif_clean = nif.strip().upper()
        
        proveedor = session.query(ProveedorMaestro).filter(
            ProveedorMaestro.nif_cif == nif_clean
        ).first()
        
        if proveedor:
            # Actualizar nombres alternativos si es nuevo
            if nombre_raw not in proveedor.nombres_alternativos:
                proveedor.nombres_alternativos.append(nombre_raw)
                session.flush()
            
            return {
                'proveedor_maestro_id': proveedor.id,
                'nombre_canonico': proveedor.nombre_canonico,
                'metodo': 'nif',
                'confianza': 100.0
            }
    
    # CAPA 2: Normalizar nombre
    nombre_normalizado = normalizar_nombre_proveedor(nombre_raw)
    
    if not nombre_normalizado:
        # Si después de normalizar no queda nada, usar nombre original
        nombre_normalizado = nombre_raw.upper().strip()
    
    # CAPA 3: Buscar en proveedores maestros existentes (fuzzy matching)
    todos_proveedores = session.query(ProveedorMaestro).filter(
        ProveedorMaestro.activo == True
    ).all()
    
    mejor_match = None
    mejor_score = 0.0
    
    for prov in todos_proveedores:
        # Comparar con nombre canónico
        nombre_canonico_norm = normalizar_nombre_proveedor(prov.nombre_canonico)
        score1 = calcular_similitud(nombre_normalizado, nombre_canonico_norm)
        
        # Comparar con nombres alternativos
        scores_alt = []
        for alt in prov.nombres_alternativos:
            alt_norm = normalizar_nombre_proveedor(alt)
            score_alt = calcular_similitud(nombre_normalizado, alt_norm)
            scores_alt.append(score_alt)
        
        score2 = max(scores_alt) if scores_alt else 0.0
        
        # Usar el mejor score
        score_final = max(score1, score2)
        
        if score_final > mejor_score:
            mejor_score = score_final
            mejor_match = prov
    
    # CAPA 4: Decisión
    UMBRAL_FUZZY = 92.0
    
    if mejor_match and mejor_score >= UMBRAL_FUZZY:
        # Match encontrado - actualizar nombres alternativos
        if nombre_raw not in mejor_match.nombres_alternativos:
            mejor_match.nombres_alternativos.append(nombre_raw)
            session.flush()
        
        return {
            'proveedor_maestro_id': mejor_match.id,
            'nombre_canonico': mejor_match.nombre_canonico,
            'metodo': 'fuzzy',
            'confianza': mejor_score
        }
    else:
        # Crear nuevo proveedor maestro
        nuevo_proveedor = ProveedorMaestro(
            nombre_canonico=nombre_raw,  # Usar nombre original como canónico inicial
            nif_cif=nif.strip().upper() if nif and nif.strip() else None,
            nombres_alternativos=[nombre_raw],
            total_facturas=0,
            total_importe=0.00,
            activo=True
        )
        session.add(nuevo_proveedor)
        session.flush()
        
        return {
            'proveedor_maestro_id': nuevo_proveedor.id,
            'nombre_canonico': nuevo_proveedor.nombre_canonico,
            'metodo': 'nuevo',
            'confianza': 0.0
        }

