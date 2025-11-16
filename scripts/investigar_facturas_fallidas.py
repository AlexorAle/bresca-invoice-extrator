#!/usr/bin/env python3
"""
Script para investigar facturas fallidas y comparar BD vs Frontend
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.db.database import Database
from src.db.models import Factura
from src.db.repositories import FacturaRepository
from sqlalchemy import func, extract
from datetime import date
import json

load_env()
db = Database()
repo = FacturaRepository(db)

print('='*70)
print('🔍 INVESTIGACIÓN COMPLETA: FACTURAS FALLIDAS')
print('='*70)

# Meses a verificar
meses = [
    (2024, 1, 'Enero 2024'),
    (2025, 7, 'Julio 2025'),
    (2025, 8, 'Agosto 2025')
]

for year, month, nombre_mes in meses:
    print(f'\n{"="*70}')
    print(f'📅 {nombre_mes} ({year}-{month:02d})')
    print('='*70)
    
    # 1. Verificar en BD
    with db.get_session() as session:
        facturas_mes = session.query(Factura).filter(
            extract('year', Factura.fecha_emision) == year,
            extract('month', Factura.fecha_emision) == month
        ).all()
        
        procesadas = [f for f in facturas_mes if f.estado == 'procesado']
        revisar = [f for f in facturas_mes if f.estado == 'revisar']
        error = [f for f in facturas_mes if f.estado == 'error']
        
        print(f'\n💾 BASE DE DATOS:')
        print(f'  Total facturas: {len(facturas_mes)}')
        print(f'  ✅ Procesadas: {len(procesadas)}')
        print(f'  ⚠️  En revisar: {len(revisar)}')
        print(f'  ❌ Error: {len(error)}')
        
        if revisar or error:
            print(f'\n  Facturas con problemas:')
            for f in revisar + error:
                print(f'    - {f.drive_file_name} ({f.estado})')
    
    # 2. Llamar al endpoint directamente
    print(f'\n🌐 ENDPOINT /api/facturas/failed:')
    try:
        from src.api.routes.facturas import get_failed_invoices
        result = get_failed_invoices(month=month, year=year, repo=repo)
        if hasattr(result, 'data'):
            items = result.data
            print(f'  Total facturas fallidas devueltas: {len(items)}')
            if items:
                print(f'  Primeras 5:')
                for item in items[:5]:
                    nombre = item.nombre if hasattr(item, 'nombre') else str(item)
                    print(f'    - {nombre}')
            else:
                print(f'  ⚠️  NO HAY FACTURAS FALLIDAS DEVUELTAS')
        else:
            print(f'  ⚠️  Respuesta sin formato esperado: {result}')
        result_obj = result  # Guardar para el resumen
    except Exception as e:
        print(f'  ❌ Error llamando endpoint: {e}')
        import traceback
        traceback.print_exc()
        result_obj = None
    
    # 3. Verificar archivos en cuarentena
    print(f'\n📁 ARCHIVOS EN CUARENTENA:')
    quarantine_path = Path('data/quarantine')
    cuarentena_mes = []
    
    if quarantine_path.exists():
        for meta_file in quarantine_path.rglob('*.meta.json'):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        continue
                    meta = json.loads(content)
                
                nombre = meta.get('drive_file_name') or meta.get('file_info', {}).get('name') or 'unknown'
                
                # Intentar obtener fecha
                fecha_emision = meta.get('fecha_emision') or meta.get('factura_data', {}).get('fecha_emision')
                fecha_valida = False
                
                if fecha_emision:
                    try:
                        from datetime import datetime
                        if isinstance(fecha_emision, str):
                            fecha = datetime.fromisoformat(fecha_emision.replace('Z', '+00:00'))
                            if fecha.year == year and fecha.month == month:
                                fecha_valida = True
                    except:
                        pass
                
                # Si no hay fecha válida, intentar del nombre
                if not fecha_valida and nombre and nombre != 'unknown':
                    import re
                    match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{2,4})', nombre.lower())
                    if match:
                        mes_nombre = match.group(1)
                        año_str = match.group(2)
                        
                        if len(año_str) == 2:
                            año_inferido = 2000 + int(año_str)
                        else:
                            año_inferido = int(año_str)
                        
                        meses_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
                            'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                        }
                        
                        if mes_nombre in meses_map and año_inferido == year and meses_map[mes_nombre] == month:
                            fecha_valida = True
                
                if fecha_valida:
                    cuarentena_mes.append({
                        'nombre': nombre,
                        'archivo': str(meta_file),
                        'decision': meta.get('decision', 'unknown'),
                        'fecha_emision': fecha_emision
                    })
            
            except:
                pass
        
        print(f'  Total archivos en cuarentena para este mes: {len(cuarentena_mes)}')
        if cuarentena_mes:
            print(f'  Primeros 5:')
            for arch in cuarentena_mes[:5]:
                print(f'    - {arch["nombre"]} ({arch["decision"]})')
        else:
            print(f'  ⚠️  NO HAY ARCHIVOS EN CUARENTENA PARA ESTE MES')
    else:
        print(f'  ⚠️  Directorio de cuarentena no existe')
    
    # 4. Resumen
    print(f'\n📊 RESUMEN:')
    total_fallidas_esperadas = len(revisar) + len(error) + len(cuarentena_mes)
    print(f'  Facturas fallidas esperadas: {total_fallidas_esperadas}')
    print(f'    - En BD (revisar/error): {len(revisar) + len(error)}')
    print(f'    - En cuarentena: {len(cuarentena_mes)}')
    
    if result_obj and hasattr(result_obj, 'data'):
        facturas_devueltas = len(result_obj.data)
        print(f'  Facturas devueltas por endpoint: {facturas_devueltas}')
        
        if facturas_devueltas == 0 and total_fallidas_esperadas > 0:
            print(f'  ⚠️  PROBLEMA: Hay {total_fallidas_esperadas} facturas fallidas pero el endpoint devuelve 0')
            print(f'      Esto explica por qué no aparecen en el frontend')
    else:
        print(f'  ⚠️  No se pudo obtener resultado del endpoint')

db.close()

