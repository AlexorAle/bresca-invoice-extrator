"""
Normalización avanzada de nombres de proveedores v2
Usa limpieza agresiva + fuzzy matching para detectar duplicados
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple


# Palabras vacías a eliminar
PALABRAS_VACIAS = {
    'COMERCIAL', 'DISTRIBUCIONES', 'DISTRIBUCION', 'DISTRIBUCIONES',
    'HORECA', 'SERVICIOS', 'MALAGA', 'MÁLAGA', 'IBERICA', 'IBÉRICA',
    'MAYORISTA', 'PLATFORM', 'SPAIN', 'EUROPEAN', 'PARTNERS',
    'SERVICIOS', 'HOSTELEROS', 'HOSTELERIA', 'HOSTELERÍA'
}

# Formas jurídicas a eliminar
FORMAS_JURIDICAS = [
    r'\bS\.?\s*L\.?\s*U?\.?\b',
    r'\bS\.?\s*A\.?\s*U?\.?\b',
    r'\bC\.?\s*B\.?\b',
    r'\bS\.?\s*L\.?\b',
    r'\bS\.?\s*A\.?\b',
    r'\bSLU\b',
    r'\bSAU\b',
    r'\bSL\b',
    r'\bSA\b',
    r'\bCB\b',
]

# Reglas heurísticas específicas para casos conocidos
REGLAS_ESPECIFICAS: Dict[str, List[str]] = {
    'NEGRINI': ['negrini', 'negriñi', 'negri'],
    'MAKRO': ['makro distribucion', 'makro distribucion mayorista', 'makro'],
    'GLOVO': ['glovoapp', 'glovo app', 'glovo'],
    'H MARTIN': ['h martin', 'h.martin', 'hmartin', 'h martín'],
    'GARMATIZ': ['garmatz', 'garmazit', 'garnatiz', 'garmatiz'],
    'COCA COLA': ['coca cola', 'coca-cola', 'cocacola'],
    'SERVI FRUTAS JUANI': ['servi frutas juaní', 'servi-frutas juani', 'servi frutas juani'],
    'ANDALUZA SUPERMERCADOS': ['andaluza supermercados', 'andaluza de supermercados'],
    'ECOTIENDAS BIOGLORIA': ['ecotiendas biogloria', 'ecotiendas biogloría'],
}


def normalizar_nombre_proveedor(nombre: str) -> str:
    """
    Normalización agresiva de nombres de proveedores
    
    Reglas aplicadas (en orden):
    1. Eliminar NIF/CIF embebido
    2. Convertir a mayúsculas y eliminar acentos
    3. Eliminar formas jurídicas
    4. Eliminar palabras vacías
    5. Normalizar espacios y puntuación
    6. Aplicar reglas heurísticas específicas
    
    Args:
        nombre: Nombre original del proveedor
    
    Returns:
        Nombre normalizado para matching
    """
    if not nombre:
        return ""
    
    # 1. Convertir a mayúsculas
    normalized = nombre.upper().strip()
    
    # 2. Eliminar información de NIF/CIF embebida
    normalized = re.sub(r'\s*-?\s*NIF\s*[A-Z0-9]+', '', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\s*-?\s*CIF\s*[A-Z0-9]+', '', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\s*-?\s*VAT\s*[A-Z0-9]+', '', normalized, flags=re.IGNORECASE)
    
    # 3. Eliminar acentos/diacríticos
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', normalized)
        if unicodedata.category(c) != 'Mn'
    )
    
    # 4. Reemplazar comas, guiones, underscores por espacios
    normalized = normalized.replace(',', ' ')
    normalized = normalized.replace('-', ' ')
    normalized = normalized.replace('_', ' ')
    normalized = normalized.replace('.', ' ')  # Puntos también a espacios
    
    # 5. Eliminar formas jurídicas
    for forma in FORMAS_JURIDICAS:
        normalized = re.sub(forma, ' ', normalized, flags=re.IGNORECASE)
    
    # 6. Eliminar palabras vacías
    palabras = normalized.split()
    palabras_filtradas = [
        p for p in palabras 
        if p not in PALABRAS_VACIAS and len(p) > 1
    ]
    normalized = ' '.join(palabras_filtradas)
    
    # 7. Normalizar espacios múltiples
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    
    # 8. Aplicar reglas heurísticas específicas
    for clave_canonica, variantes in REGLAS_ESPECIFICAS.items():
        for variante in variantes:
            variante_norm = variante.upper()
            # Eliminar acentos de variante también
            variante_norm = ''.join(
                c for c in unicodedata.normalize('NFD', variante_norm)
                if unicodedata.category(c) != 'Mn'
            )
            if variante_norm in normalized or normalized in variante_norm:
                # Si encontramos una variante conocida, normalizar a la clave canónica
                normalized = clave_canonica
                break
    
    return normalized


def seleccionar_nombre_canonico(grupo: List[Dict]) -> Tuple[str, Optional[str]]:
    """
    Selecciona el nombre canónico de un grupo de proveedores similares
    
    Prioridad:
    1. Nombre con más facturas
    2. Nombre con formato estándar (S.L., S.A.)
    3. Nombre más largo (más completo)
    4. Nombre sin NIF embebido
    
    Args:
        grupo: Lista de diccionarios con proveedores similares
               Cada dict debe tener: 'nombre', 'total_facturas', 'nif_cif'
    
    Returns:
        Tupla (nombre_canonico, nif_cif)
    """
    if not grupo:
        return ("", None)
    
    if len(grupo) == 1:
        return (grupo[0]['nombre'], grupo[0].get('nif_cif'))
    
    # Prioridad 1: Nombre con más facturas
    grupo_ordenado = sorted(grupo, key=lambda x: x.get('total_facturas', 0), reverse=True)
    candidato_principal = grupo_ordenado[0]
    
    # Prioridad 2: Si hay empate, preferir nombre con formato estándar
    nombres_con_formato = [
        p for p in grupo_ordenado 
        if re.search(r'S\.L\.|S\.A\.|S\.L\.U\.', p['nombre'])
    ]
    
    if nombres_con_formato:
        candidato_principal = nombres_con_formato[0]
    
    # Prioridad 3: Preferir nombre sin NIF embebido
    nombres_sin_nif = [
        p for p in grupo_ordenado
        if not re.search(r'NIF\s*[A-Z0-9]+', p['nombre'], re.IGNORECASE)
    ]
    
    if nombres_sin_nif:
        # De los sin NIF, elegir el más largo (más completo)
        candidato_principal = max(nombres_sin_nif, key=lambda x: len(x['nombre']))
    
    # Obtener NIF del grupo (si alguno lo tiene)
    nif_cif = None
    for p in grupo:
        if p.get('nif_cif') and p['nif_cif'].strip():
            nif_cif = p['nif_cif'].strip().upper()
            break
    
    return (candidato_principal['nombre'], nif_cif)


def calcular_similitud(nombre1: str, nombre2: str) -> float:
    """
    Calcula similitud entre dos nombres normalizados
    
    Args:
        nombre1: Primer nombre (ya normalizado)
        nombre2: Segundo nombre (ya normalizado)
    
    Returns:
        Score de similitud (0-100)
    """
    try:
        from rapidfuzz import fuzz
        
        # Token Set Ratio es mejor para variaciones de orden
        score = fuzz.token_set_ratio(nombre1, nombre2)
        return float(score)
    except ImportError:
        # Fallback si rapidfuzz no está disponible
        # Usar similitud simple basada en palabras comunes
        palabras1 = set(nombre1.split())
        palabras2 = set(nombre2.split())
        
        if not palabras1 or not palabras2:
            return 0.0
        
        interseccion = palabras1.intersection(palabras2)
        union = palabras1.union(palabras2)
        
        if not union:
            return 0.0
        
        return (len(interseccion) / len(union)) * 100

