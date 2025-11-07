#!/usr/bin/env python3
"""
Script para probar procesamiento de 20 facturas con validación ajustada
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from security.secrets import load_env, validate_secrets
from db.database import get_database
from db.repositories import FacturaRepository
from drive_client import DriveClient
from ocr_extractor import InvoiceExtractor
from pipeline.ingest import process_batch
import time

load_env()
validate_secrets()

print("=" * 70)
print("PRUEBA: Procesar 20 facturas con validación ajustada (permite negativos)")
print("=" * 70)

# Inicializar
db = get_database()
drive = DriveClient()
extractor = InvoiceExtractor()

try:
    # Obtener archivos de julio
    base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    folder_id = drive.get_folder_id_by_name("Julio 2025", base_folder_id)
    if not folder_id:
        print("❌ Carpeta 'Julio 2025' no encontrada")
        sys.exit(1)
    
    # Listar PDFs
    files = drive.list_pdf_files(folder_id)
    print(f"\n📁 Encontrados {len(files)} archivos en 'Julio 2025'")
    
    if len(files) == 0:
        print("❌ No se encontraron archivos")
        sys.exit(1)
    
    # Limitar a 20
    files_to_process = files[:20]
    print(f"📋 Procesando las primeras {len(files_to_process)} facturas\n")
    
    # Mostrar archivos
    for i, f in enumerate(files_to_process, 1):
        print(f"  {i}. {f.get('name', 'N/A')}")
    
    # Descargar
    print(f"\n⬇️  Descargando archivos...")
    temp_path = Path("temp")
    temp_path.mkdir(exist_ok=True)
    
    files_with_paths = []
    for idx, file_info in enumerate(files_to_process, 1):
        file_id = file_info['id']
        file_name = file_info['name']
        local_path = temp_path / file_name
        
        print(f"   Descargando {idx}/{len(files_to_process)}: {file_name}")
        if drive.download_file(file_id, str(local_path)):
            file_info['local_path'] = str(local_path)
            file_info['folder_name'] = "Julio 2025"
            files_with_paths.append(file_info)
        else:
            print(f"   ⚠️  Error descargando {file_name}")
    
    # Procesar
    print(f"\n🔄 Procesando {len(files_with_paths)} facturas...")
    print("   (Espera de 3 segundos entre cada factura)\n")
    
    stats = process_batch(files_with_paths, extractor, db)
    
    print(f"\n✅ Resultados del procesamiento:")
    print(f"   Exitosos: {stats.get('exitosos', 0)}")
    print(f"   Fallidos: {stats.get('fallidos', 0)}")
    print(f"   Duplicados: {stats.get('duplicados', 0)}")
    
    # Verificar datos en BD
    print(f"\n📊 Verificando datos guardados en BD...")
    repo = FacturaRepository(db)
    
    with db.get_session() as session:
        from src.db.models import Factura
        facturas = session.query(Factura).order_by(Factura.creado_en.desc()).limit(20).all()
        
        print(f"\n   Facturas guardadas: {len(facturas)}")
        print()
        
        positivos = 0
        negativos = 0
        nulos = 0
        
        for f in facturas:
            print(f"   📄 {f.drive_file_name}")
            print(f"      proveedor_text: {f.proveedor_text or '❌ NULL'}")
            print(f"      fecha_emision: {f.fecha_emision}")
            
            if f.importe_total is None:
                print(f"      importe_total: ❌ NULL")
                nulos += 1
            elif f.importe_total < 0:
                print(f"      importe_total: {f.importe_total} € (NEGATIVO)")
                negativos += 1
            else:
                print(f"      importe_total: {f.importe_total} € (POSITIVO)")
                positivos += 1
            
            print(f"      estado: {f.estado}")
            print()
        
        print(f"   📈 Resumen de importes:")
        print(f"      Positivos: {positivos}")
        print(f"      Negativos: {negativos}")
        print(f"      NULL: {nulos}")
        
        if negativos > 0:
            print(f"\n   ✅ ¡ÉXITO! Se guardaron {negativos} facturas con importe negativo")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("Prueba completada")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

