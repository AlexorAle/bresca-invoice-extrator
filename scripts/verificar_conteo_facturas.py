#!/usr/bin/env python3
"""
Script para verificar conteo de facturas:
- Cuenta PDFs en Google Drive
- Cuenta facturas en BD (procesadas + revisar)
- Compara ambos números
"""
import sys
import os
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.drive_client import DriveClient
from src.drive.drive_incremental import DriveIncrementalClient
from src.db.database import Database
from src.db.models import Factura

load_env()

def count_pdfs_in_drive():
    """Contar todos los PDFs en Google Drive (recursivo)"""
    print("📁 Contando archivos PDF en Google Drive...")
    
    drive_client = DriveClient()
    drive_incremental = DriveIncrementalClient()
    
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    if not folder_id:
        print("❌ GOOGLE_DRIVE_FOLDER_ID no configurado")
        return None
    
    try:
        # Obtener todas las subcarpetas (recursivo)
        all_folders = drive_incremental._get_all_subfolders(folder_id)
        print(f"   📂 Encontradas {len(all_folders)} carpetas/subcarpetas")
        
        # Contar PDFs en todas las carpetas
        total_pdfs = 0
        for folder_id_item in all_folders:
            pdfs = drive_client.list_pdf_files(folder_id_item)
            total_pdfs += len(pdfs)
        
        print(f"   ✅ Total de PDFs en Drive: {total_pdfs}")
        return total_pdfs
        
    except Exception as e:
        print(f"   ❌ Error contando PDFs: {e}")
        return None

def count_facturas_in_db():
    """Contar facturas en BD (procesadas + revisar)"""
    print("\n💾 Contando facturas en base de datos...")
    
    try:
        db = Database()
        
        # Contar procesadas
        with db.get_session() as session:
            procesadas = session.query(Factura).filter(
                Factura.estado == 'procesado'
            ).count()
            
            # Contar en revisión
            revisar = session.query(Factura).filter(
                Factura.estado == 'revisar'
            ).count()
            
            # Total
            total = procesadas + revisar
            
            print(f"   ✅ Procesadas: {procesadas}")
            print(f"   ⚠️  En revisión: {revisar}")
            print(f"   📊 Total (procesadas + revisar): {total}")
            
            return {
                'procesadas': procesadas,
                'revisar': revisar,
                'total': total
            }
            
    except Exception as e:
        print(f"   ❌ Error contando facturas en BD: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*70)
    print("🔍 VERIFICACIÓN DE CONTEO DE FACTURAS")
    print("="*70)
    print()
    
    # Contar PDFs en Drive
    count_drive = count_pdfs_in_drive()
    
    # Contar facturas en BD
    count_db = count_facturas_in_db()
    
    # Comparar
    print("\n" + "="*70)
    print("📊 COMPARACIÓN")
    print("="*70)
    
    if count_drive is not None and count_db is not None:
        print(f"   📁 PDFs en Google Drive: {count_drive}")
        print(f"   💾 Facturas en BD (procesadas + revisar): {count_db['total']}")
        print()
        
        if count_drive == count_db['total']:
            print("   ✅ ¡Los números coinciden!")
        else:
            diferencia = count_drive - count_db['total']
            print(f"   ⚠️  Diferencia: {abs(diferencia)} facturas")
            if diferencia > 0:
                print(f"   📥 Hay {diferencia} PDFs en Drive que no están en BD")
            else:
                print(f"   💾 Hay {abs(diferencia)} facturas en BD que no están en Drive")
    else:
        print("   ❌ No se pudo completar la comparación")
    
    print()

if __name__ == "__main__":
    main()

