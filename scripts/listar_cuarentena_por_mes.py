#!/usr/bin/env python3
"""
Script para listar facturas en cuarentena agrupadas por mes y año
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import dateparser

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Meses en español
MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio',
    7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

def parse_fecha(fecha_str):
    """Parsear fecha desde string (múltiples formatos)"""
    if not fecha_str:
        return None
    
    # Intentar parsear con dateparser (soporta múltiples formatos)
    try:
        fecha = dateparser.parse(fecha_str, languages=['es', 'en'])
        if fecha:
            return fecha
    except:
        pass
    
    # Intentar formatos comunes
    formatos = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%SZ',
        '%d/%m/%Y',
        '%d-%m-%Y'
    ]
    
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str.split('T')[0], fmt)
        except:
            continue
    
    return None

def main():
    quarantine_path = Path(project_root / 'data' / 'quarantine')
    
    if not quarantine_path.exists():
        print("❌ Carpeta de cuarentena no existe")
        return
    
    # Buscar todos los archivos .meta.json
    meta_files = list(quarantine_path.glob('**/*.meta.json'))
    
    if not meta_files:
        print("📭 No hay archivos en cuarentena")
        return
    
    # Agrupar por mes/año
    por_mes = defaultdict(int)
    sin_fecha = 0
    
    for meta_file in meta_files:
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Intentar obtener fecha_emision desde múltiples ubicaciones
            fecha_emision = None
            
            # 1. Nivel raíz
            if 'fecha_emision' in metadata:
                fecha_emision = parse_fecha(metadata['fecha_emision'])
            
            # 2. Dentro de factura_data
            if not fecha_emision and 'factura_data' in metadata:
                if 'fecha_emision' in metadata['factura_data']:
                    fecha_emision = parse_fecha(metadata['factura_data']['fecha_emision'])
            
            # 3. Dentro de file_info (modifiedTime como fallback)
            if not fecha_emision and 'file_info' in metadata:
                if 'modifiedTime' in metadata['file_info']:
                    fecha_emision = parse_fecha(metadata['file_info']['modifiedTime'])
            
            if fecha_emision:
                mes_ano = (fecha_emision.year, fecha_emision.month)
                por_mes[mes_ano] += 1
            else:
                sin_fecha += 1
                
        except Exception as e:
            print(f"⚠️  Error leyendo {meta_file.name}: {e}", file=sys.stderr)
            sin_fecha += 1
    
    # Ordenar por año y mes
    meses_ordenados = sorted(por_mes.items())
    
    # Mostrar resultados
    print("="*70)
    print("📋 FACTURAS EN CUARENTENA POR MES Y AÑO")
    print("="*70)
    print()
    
    if meses_ordenados:
        for (año, mes), cantidad in meses_ordenados:
            mes_nombre = MESES_ES[mes]
            print(f"{mes_nombre.capitalize()} {año} - {cantidad} facturas")
    
    if sin_fecha > 0:
        print(f"Sin fecha - {sin_fecha} facturas")
    
    print()
    print(f"Total: {sum(por_mes.values()) + sin_fecha} facturas en cuarentena")

if __name__ == "__main__":
    main()

