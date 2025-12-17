"""
Utilidades para normalizar nombres de proveedores
"""
import re
import unicodedata


def normalize_proveedor_name(nombre: str) -> str:
    """
    Normaliza un nombre de proveedor para facilitar la agrupación
    
    Reglas de normalización (MUY AGRESIVAS):
    1. Convertir a mayúsculas
    2. Eliminar acentos/diacríticos
    3. Eliminar TODOS los puntos
    4. Eliminar TODAS las comas
    5. Normalizar espacios (múltiples → uno solo)
    6. Eliminar guiones
    7. Normalizar abreviaturas comunes (SL, SA, etc.)
    8. Eliminar información extra (NIF, CIF)
    
    Args:
        nombre: Nombre original del proveedor
    
    Returns:
        Nombre normalizado
    
    Ejemplos:
        "AE PROYECTOS S.L." → "AE PROYECTOS SL"
        "AE. PROYECTOS S.L." → "AE PROYECTOS SL"
        "ANDALUZA DE SUPERMERCADOS H. MARTIN, S.L." → "ANDALUZA DE SUPERMERCADOS H MARTIN SL"
        "ANDALUZA DE SUPERMERCADOS H.MARTIN, S.L." → "ANDALUZA DE SUPERMERCADOS H MARTIN SL"
    """
    if not nombre:
        return ""
    
    # 1. Convertir a mayúsculas
    normalized = nombre.upper().strip()
    
    # 2. Eliminar acentos/diacríticos (CRÍTICO para MARTÍN vs MARTIN)
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', normalized)
        if unicodedata.category(c) != 'Mn'
    )
    
    # 3. Eliminar información de NIF/CIF (antes de normalizar para no interferir)
    normalized = re.sub(r'\s*-?\s*NIF\s*[A-Z0-9]+', '', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\s*-?\s*CIF\s*[A-Z0-9]+', '', normalized, flags=re.IGNORECASE)
    
    # 4. Reemplazar comas, guiones y underscores por espacios
    normalized = normalized.replace(',', ' ')
    normalized = normalized.replace('-', ' ')
    normalized = normalized.replace('_', ' ')
    
    # 5. Eliminar TODOS los puntos (incluyendo S.L., S.A., iniciales, etc.)
    normalized = normalized.replace('.', '')
    
    # 6. Eliminar espacios después de letras solas (iniciales sin punto)
    # Esto convierte "H MARTIN" y "HMARTIN" a lo mismo
    # IMPORTANTE: esto puede ser muy agresivo, pero es necesario para detectar duplicados
    normalized = re.sub(r'\b([A-Z])\s+', r'\1', normalized)
    
    # 7. Normalizar abreviaturas comunes (ahora sin puntos)
    # Estas patrones capturan variaciones como "S L" o "SL"
    normalized = re.sub(r'\bS\s*L\s*U\b', 'SLU', normalized)
    normalized = re.sub(r'\bS\s*A\s*U\b', 'SAU', normalized)
    normalized = re.sub(r'\bS\s*L\b', 'SL', normalized)
    normalized = re.sub(r'\bS\s*A\b', 'SA', normalized)
    normalized = re.sub(r'\bC\s*B\b', 'CB', normalized)
    
    # 8. Normalizar espacios múltiples a uno solo
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # 8. Limpiar espacios al inicio y final
    normalized = normalized.strip()
    
    return normalized


def find_similar_proveedores(nombre: str, lista_proveedores: list) -> list:
    """
    Encuentra proveedores similares en una lista usando normalización
    
    Args:
        nombre: Nombre del proveedor a buscar
        lista_proveedores: Lista de tuplas (id, nombre_original)
    
    Returns:
        Lista de tuplas (id, nombre_original, nombre_normalizado) de proveedores similares
    """
    nombre_norm = normalize_proveedor_name(nombre)
    similares = []
    
    for prov_id, prov_nombre in lista_proveedores:
        if normalize_proveedor_name(prov_nombre) == nombre_norm:
            similares.append((prov_id, prov_nombre, nombre_norm))
    
    return similares


def get_canonical_name(nombres: list) -> str:
    """
    Dado un conjunto de nombres similares, devuelve el nombre "canónico"
    (el más completo y con mejor formato)
    
    Args:
        nombres: Lista de nombres de proveedor
    
    Returns:
        Nombre canónico seleccionado
    
    Heurísticas:
    - Preferir el nombre más largo (más información)
    - Preferir nombres CON puntos si son abreviaturas estándar (S.L. mejor que SL)
    - Preferir nombres sin NIF/CIF embebido
    """
    if not nombres:
        return ""
    
    if len(nombres) == 1:
        return nombres[0]
    
    # Filtrar nombres que tienen NIF embebido (menos deseables)
    nombres_sin_nif = [n for n in nombres if not re.search(r'NIF\s*[A-Z0-9]{8,}', n, re.IGNORECASE)]
    
    if nombres_sin_nif:
        candidatos = nombres_sin_nif
    else:
        candidatos = nombres
    
    # Preferir nombres con formato estándar de sociedad (S.L., S.A., etc.)
    nombres_con_formato = [n for n in candidatos if re.search(r'S\.L\.|S\.A\.|S\.L\.U\.', n)]
    
    if nombres_con_formato:
        # De los que tienen formato, elegir el más largo
        return max(nombres_con_formato, key=len)
    
    # Si no hay formato estándar, elegir el más largo
    return max(candidatos, key=len)

