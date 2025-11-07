#!/usr/bin/env python3
"""
Script para probar procesamiento de 5 facturas con nuevo prompt
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
print("PRUEBA: Procesar 5 facturas con nuevo prompt (nombre_proveedor)")
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
    
    # Limitar a 5
    files_to_process = files[:5]
    print(f"📋 Procesando solo las primeras {len(files_to_process)} facturas\n")
    
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
        
        print(f"   Descargando {idx}/5: {file_name}")
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
        facturas = session.query(Factura).order_by(Factura.creado_en.desc()).limit(5).all()
        
        print(f"\n   Facturas guardadas: {len(facturas)}")
        print()
        
        con_proveedor = 0
        sin_proveedor = 0
        con_cliente = 0
        
        for f in facturas:
            print(f"   📄 {f.drive_file_name}")
            print(f"      proveedor_text: {f.proveedor_text or '❌ NULL'}")
            
            # Verificar nombre_cliente en metadatos
            nombre_cliente = None
            if f.metadatos_json and isinstance(f.metadatos_json, dict):
                nombre_cliente = f.metadatos_json.get('nombre_cliente')
            
            if nombre_cliente:
                print(f"      nombre_cliente (en metadatos): {nombre_cliente}")
                con_cliente += 1
            else:
                print(f"      nombre_cliente: No guardado")
            
            print(f"      fecha_emision: {f.fecha_emision}")
            print(f"      importe_total: {f.importe_total} €")
            print(f"      estado: {f.estado}")
            print()
            
            if f.proveedor_text:
                con_proveedor += 1
            else:
                sin_proveedor += 1
        
        print(f"   📈 Resumen:")
        print(f"      Con proveedor_text: {con_proveedor}")
        print(f"      Sin proveedor_text: {sin_proveedor}")
        print(f"      Con nombre_cliente guardado: {con_cliente}")
        
        if sin_proveedor > 0:
            print(f"\n   ⚠️  {sin_provider} facturas sin proveedor (deberían estar en cuarentena)")
        
        if con_proveedor == len(facturas):
            print(f"\n   ✅ ¡ÉXITO! Todas las facturas tienen proveedor_text correcto")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("Prueba completada")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

