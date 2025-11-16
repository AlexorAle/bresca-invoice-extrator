#!/usr/bin/env python3
"""
Script que replica la lógica del endpoint /api/facturas/failed
para investigar discrepancias
"""
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, date
from calendar import monthrange
from collections import defaultdict

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.db.database import Database
from src.db.models import Factura
from sqlalchemy import func

load_env()

def _parse_date_from_filename(filename: str, default_year: int = None):
    """Replicar función del endpoint"""
    try:
        import dateparser
        
        meses_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
            'julio': 7, 'agosto': 8, 'agost': 8,
            'septiembre': 9, 'sep': 9, 'sept': 9,
            'octubre': 10, 'oct': 10,
            'noviembre': 11, 'nov': 11,
            'diciembre': 12, 'dec': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        filename_clean = filename.rsplit('.', 1)[0].lower()
        
        patterns = [
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|agost|septiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dec)\s+(\d{4})',
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|agost|septiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dec)\s+(\d{2})',
            r'(\d{4})[-/](\d{1,2})',
            r'(?:factura|fact)\s+\w+\s+\d*\s*(enero|febrero|marzo|abril|mayo|junio|julio|agosto|agost|septiembre|sep|sept|octubre|oct|noviembre|nov|diciembre|dec)\s+(\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename_clean, re.IGNORECASE)
            if match:
                grupos = match.groups()
                if len(grupos) == 2:
                    grupo1 = grupos[0].lower()
                    grupo2 = grupos[1]
                    
                    if grupo1 in meses_es and len(grupo2) == 4:
                        year = int(grupo2)
                        month = meses_es[grupo1]
                        return date(year, month, 1)
                    
                    if grupo1 in meses_es and len(grupo2) == 2:
                        year = 2000 + int(grupo2) if default_year is None else default_year
                        month = meses_es[grupo1]
                        return date(year, month, 1)
    except:
        pass
    return None

def get_failed_invoices_by_month(month, year):
    """Replicar lógica del endpoint"""
    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)
    
    failed_invoices = []
    processed_names = set()
    
    # 1. FACTURAS EN BD
    db = Database()
    with db.get_session() as session:
        fecha_filtro = func.coalesce(Factura.fecha_emision, Factura.fecha_recepcion)
        
        facturas_bd = session.query(Factura).filter(
            Factura.estado.in_(['error', 'revisar']),
            fecha_filtro >= start_date,
            fecha_filtro <= end_date
        ).all()
        
        for factura_obj in facturas_bd:
            nombre = factura_obj.drive_file_name
            if nombre not in processed_names:
                failed_invoices.append({
                    'nombre': nombre,
                    'fecha_emision': factura_obj.fecha_emision.isoformat() if factura_obj.fecha_emision else None,
                    'estado': factura_obj.estado,
                    'source': 'bd'
                })
                processed_names.add(nombre)
    
    # 2. ARCHIVOS EN CUARENTENA
    quarantine_path = Path(os.getenv('QUARANTINE_PATH', 'data/quarantine'))
    
    if quarantine_path.exists():
        for meta_file in quarantine_path.rglob("*.meta.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                
                file_info = meta_data.get('file_info', {})
                nombre = (
                    meta_data.get('drive_file_name') or 
                    file_info.get('name') or 
                    meta_file.stem.replace('.meta', '').split('_', 2)[-1] if '_' in meta_file.stem else meta_file.stem.replace('.meta', '')
                )
                
                if nombre in processed_names or nombre == 'unknown':
                    continue
                
                file_date = None
                fecha_emision_str = meta_data.get('fecha_emision') or meta_data.get('factura_data', {}).get('fecha_emision')
                
                if fecha_emision_str:
                    try:
                        if isinstance(fecha_emision_str, str):
                            file_date = datetime.fromisoformat(fecha_emision_str.replace('Z', '+00:00')).date()
                        else:
                            if hasattr(fecha_emision_str, 'date'):
                                file_date = fecha_emision_str.date()
                            elif hasattr(fecha_emision_str, 'isoformat'):
                                file_date = datetime.fromisoformat(fecha_emision_str.isoformat()).date()
                    except:
                        pass
                
                if file_date is None:
                    file_date = _parse_date_from_filename(nombre, year)
                
                if file_date is None:
                    modified_time = file_info.get('modifiedTime') or meta_data.get('file_info', {}).get('modifiedTime')
                    if modified_time:
                        try:
                            if isinstance(modified_time, str):
                                file_date = datetime.fromisoformat(modified_time.replace('Z', '+00:00')).date()
                        except:
                            pass
                
                if file_date is None:
                    quarantined_at_str = meta_data.get('quarantined_at')
                    if quarantined_at_str:
                        try:
                            quarantined_date = datetime.fromisoformat(quarantined_at_str.replace('Z', '+00:00')).date()
                            if start_date <= quarantined_date <= end_date:
                                file_date = quarantined_date
                        except:
                            pass
                
                if file_date is not None:
                    if start_date <= file_date <= end_date:
                        failed_invoices.append({
                            'nombre': nombre,
                            'fecha_emision': file_date.isoformat() if file_date else None,
                            'estado': 'quarantine',
                            'source': 'quarantine'
                        })
                        processed_names.add(nombre)
                elif nombre and nombre != 'unknown':
                    nombre_lower = nombre.lower()
                    meses_nombres = {
                        1: ['enero', 'jan'], 2: ['febrero', 'feb'], 3: ['marzo', 'mar'],
                        4: ['abril', 'apr'], 5: ['mayo', 'may'], 6: ['junio', 'jun'],
                        7: ['julio', 'jul'], 8: ['agosto', 'agost', 'aug'], 9: ['septiembre', 'sep', 'sept'],
                        10: ['octubre', 'oct'], 11: ['noviembre', 'nov'], 12: ['diciembre', 'dec']
                    }
                    
                    mes_encontrado = False
                    for mes_nombre in meses_nombres.get(month, []):
                        if mes_nombre in nombre_lower:
                            if str(year) in nombre or str(year)[-2:] in nombre:
                                mes_encontrado = True
                                break
                    
                    if mes_encontrado:
                        failed_invoices.append({
                            'nombre': nombre,
                            'fecha_emision': None,
                            'estado': 'quarantine',
                            'source': 'quarantine'
                        })
                        processed_names.add(nombre)
            
            except:
                continue
    
    return failed_invoices

def main():
    print("="*70)
    print("🔍 INVESTIGACIÓN: FACTURAS EN CUARENTENA (LÓGICA DEL ENDPOINT)")
    print("="*70)
    print()
    
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    
    resultados = {}
    
    for month in range(5, 12):  # Mayo a Noviembre 2025
        year = 2025
        facturas = get_failed_invoices_by_month(month, year)
        resultados[month] = {
            'count': len(facturas),
            'items': facturas
        }
        print(f"{meses[month-1].capitalize()} {year} - {len(facturas)} facturas")
    
    print()
    print("="*70)
    print("📊 DESGLOSE DETALLADO")
    print("="*70)
    print()
    
    for month in range(5, 12):
        year = 2025
        data = resultados[month]
        print(f"\n{meses[month-1].capitalize()} {year} ({data['count']} facturas):")
        
        # Contar por fuente
        bd_count = sum(1 for item in data['items'] if item['source'] == 'bd')
        quarantine_count = sum(1 for item in data['items'] if item['source'] == 'quarantine')
        
        print(f"  - Desde BD: {bd_count}")
        print(f"  - Desde cuarentena: {quarantine_count}")
        
        # Mostrar primeras 3 facturas como ejemplo
        if data['items']:
            print(f"  Ejemplos:")
            for item in data['items'][:3]:
                print(f"    - {item['nombre']} ({item['source']})")

if __name__ == "__main__":
    main()

