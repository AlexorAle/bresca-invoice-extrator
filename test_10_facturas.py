#!/usr/bin/env python3
"""
Script para probar procesamiento de facturas y verificar fecha_emision
"""
import sys
import os
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from security.secrets import load_env, validate_secrets
from db.database import get_database
from db.repositories import FacturaRepository
from drive_client import DriveClient
from ocr_extractor import InvoiceExtractor
from pipeline.ingest import process_batch
from datetime import datetime

# Cargar variables de entorno
load_env()
validate_secrets()

NUM_FACTURAS = 30

print("=" * 60)
print(f"PRUEBA: Procesar {NUM_FACTURAS} facturas de julio 2025")
print("=" * 60)

# Inicializar
db = get_database()
drive = DriveClient()
extractor = InvoiceExtractor()

# Listar archivos de julio
print("\n1. Listando archivos de 'Julio 2025'...")
try:
    # Obtener archivos del mes julio
    base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    # Buscar carpeta "Julio 2025"
    folder_id = drive.get_folder_id_by_name("Julio 2025", base_folder_id)
    if not folder_id:
        print("   ❌ Carpeta 'Julio 2025' no encontrada")
        sys.exit(1)
    
    # Listar PDFs en la carpeta
    files = drive.list_pdf_files(folder_id)
    
    print(f"   Encontrados {len(files)} archivos")
    
    if len(files) == 0:
        print("   ❌ No se encontraron archivos")
        sys.exit(1)
    
    # Limitar a NUM_FACTURAS
    files_to_process = files[:NUM_FACTURAS]
    print(f"   Procesando solo los primeros {len(files_to_process)} archivos")
    
    # Mostrar qué archivos se procesarán
    print("\n   Archivos a procesar:")
    for i, f in enumerate(files_to_process, 1):
        print(f"   {i}. {f.get('name', 'N/A')}")
    
    # Descargar archivos primero (necesario para process_batch)
    print("\n2. Descargando archivos...")
    temp_path = Path("temp")
    temp_path.mkdir(exist_ok=True)
    
    files_with_paths = []
    for idx, file_info in enumerate(files_to_process, 1):
        file_id = file_info['id']
        file_name = file_info['name']
        local_path = temp_path / file_name
        
        print(f"   Descargando {idx}/{NUM_FACTURAS}: {file_name}")
        if drive.download_file(file_id, str(local_path)):
            file_info['local_path'] = str(local_path)
            file_info['folder_name'] = "Julio 2025"
            files_with_paths.append(file_info)
        else:
            print(f"   ⚠️  Error descargando {file_name}")
    
    # Procesar
    print(f"\n3. Procesando {len(files_with_paths)} facturas...")
    stats = process_batch(files_with_paths, extractor, db)
    
    print(f"\n✅ Resultados:")
    print(f"   Exitosos: {stats.get('exitosos', 0)}")
    print(f"   Fallidos: {stats.get('fallidos', 0)}")
    
    # Verificar fecha_emision
    print("\n3. Verificando fecha_emision en BD...")
    repo = FacturaRepository(db)
    
    with db.get_session() as session:
        from src.db.models import Factura
        facturas = session.query(Factura).order_by(Factura.creado_en.desc()).limit(NUM_FACTURAS).all()
        
        print(f"\n   Verificando {len(facturas)} facturas:")
        con_fecha = 0
        sin_fecha = 0
        
        for f in facturas:
            if f.fecha_emision:
                con_fecha += 1
                print(f"   ✅ {f.drive_file_name}: fecha_emision = {f.fecha_emision}")
            else:
                sin_fecha += 1
                print(f"   ❌ {f.drive_file_name}: fecha_emision = None")
        
        print(f"\n   📊 Resumen:")
        print(f"      Con fecha_emision: {con_fecha}")
        print(f"      Sin fecha_emision: {sin_fecha}")
        
        if con_fecha > 0:
            print(f"\n   ✅ ¡ÉXITO! {con_fecha} facturas tienen fecha_emision guardada correctamente")
        else:
            print(f"\n   ⚠️  Ninguna factura tiene fecha_emision. Revisar el prompt de OpenAI.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

print("\n" + "=" * 60)
print("Prueba completada")
print("=" * 60)

