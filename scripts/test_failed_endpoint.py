#!/usr/bin/env python3
"""
Script para probar el endpoint de facturas fallidas
"""
import sys
import asyncio
from pathlib import Path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
load_env()

from src.api.routes.facturas import get_failed_invoices
from src.db.database import Database
from src.db.repositories import FacturaRepository

async def test_endpoint():
    db = Database()
    repo = FacturaRepository(db)
    
    print('🔍 PROBANDO ENDPOINT /api/facturas/failed')
    print('='*70)
    
    meses = [(2024, 1, 'Enero 2024'), (2025, 7, 'Julio 2025'), (2025, 8, 'Agosto 2025')]
    
    for year, month, nombre in meses:
        print(f'\n📅 {nombre} ({year}-{month:02d}):')
        try:
            result = await get_failed_invoices(month=month, year=year, repo=repo)
            total = len(result.data) if hasattr(result, 'data') else 0
            print(f'  ✅ Total facturas devueltas: {total}')
            if total > 0:
                print(f'  Primeras 10:')
                for item in result.data[:10]:
                    nombre_item = item.nombre if hasattr(item, 'nombre') else str(item)
                    print(f'    - {nombre_item}')
            else:
                print(f'  ⚠️  No hay facturas devueltas')
        except Exception as e:
            print(f'  ❌ Error: {e}')
            import traceback
            traceback.print_exc()
    
    db.close()

if __name__ == '__main__':
    asyncio.run(test_endpoint())

