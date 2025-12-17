#!/usr/bin/env python3
"""
Prueba de extracción y mapeo con una única factura
Verifica qué devuelve OpenAI y cómo se mapea a la BD
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.drive_client import DriveClient
from src.ocr_extractor import InvoiceExtractor
from src.parser_normalizer import create_factura_dto

print('=== PRUEBA DE EXTRACCIÓN Y MAPEO ===')
print('')

# 1. Obtener una factura de prueba
client = DriveClient()
folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
pdfs = client.list_all_pdfs_recursive(folder_id)

if not pdfs:
    print('❌ No se encontraron PDFs')
    sys.exit(1)

# Probar con una factura diferente (no la primera)
# Buscar una que probablemente tenga problemas
test_file = None
for pdf in pdfs:
    # Probar con una factura que no sea la primera
    if 'MAKRO' not in pdf.get('name', '').upper():
        test_file = pdf
        break

if not test_file:
    test_file = pdfs[0]  # Fallback a la primera

file_name = test_file.get('name')
file_id = test_file.get('id')

print(f'📄 Factura de prueba: {file_name}')
print(f'   ID: {file_id}')
print('')

# 2. Descargar la factura
print('📥 Descargando factura...')
try:
    # download_file devuelve True/False, pero guarda el archivo en temp/
    # Necesitamos construir la ruta manualmente
    temp_dir = os.getenv('TEMP_PATH', '/app/temp')
    os.makedirs(temp_dir, exist_ok=True)
    local_path = os.path.join(temp_dir, file_name)
    
    # Descargar el archivo
    success = client.download_file(file_id, local_path)
    if not success:
        print(f'   ❌ Error: La descarga falló')
        sys.exit(1)
    
    print(f'   Descargada en: {local_path}')
    if not os.path.exists(local_path):
        print(f'   ❌ Error: El archivo no existe en: {local_path}')
        sys.exit(1)
except Exception as e:
    print(f'   ❌ Error descargando: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
print('')

# 3. Extraer datos con OpenAI
print('🔍 Extrayendo datos con OpenAI...')
extractor = InvoiceExtractor()
raw_data = extractor.extract_invoice_data(local_path)

print('')
print('📋 DATOS RAW DEVUELTOS POR OPENAI:')
print('=' * 60)
print(json.dumps(raw_data, indent=2, ensure_ascii=False, default=str))
print('=' * 60)
print('')

# 4. Verificar campos relacionados con proveedor
print('🔍 CAMPOS RELACIONADOS CON PROVEEDOR EN RAW DATA:')
proveedor_fields = ['nombre_proveedor', 'proveedor_text', 'emisor', 'vendedor', 'empresa', 'supplier', 'vendor', 'proveedor', 'nombre_emisor']
found_fields = {}
for field in proveedor_fields:
    if field in raw_data and raw_data[field]:
        found_fields[field] = raw_data[field]
        print(f'   ✅ {field}: {raw_data[field]}')

if not found_fields:
    print('   ❌ No se encontró ningún campo relacionado con proveedor')
    print('')
    print('   📋 Todos los campos disponibles en raw_data:')
    for key in raw_data.keys():
        print(f'      - {key}')
print('')

# 5. Crear DTO (mapeo)
print('🔄 Creando DTO (mapeo a BD)...')
metadata = {
    'drive_file_id': file_id,
    'drive_file_name': file_name,
    'extractor': 'openai'
}
dto = create_factura_dto(raw_data, metadata)

print('')
print('📋 DTO RESULTANTE (mapeado para BD):')
print('=' * 60)
# Mostrar solo campos relevantes
relevant_fields = ['proveedor_text', 'nombre_cliente', 'fecha_emision', 'importe_total', 'base_imponible', 'impuestos_total', 'iva_porcentaje', 'estado']
for field in relevant_fields:
    if field in dto:
        print(f'   {field}: {dto[field]}')
print('=' * 60)
print('')

# 6. Verificar si el proveedor se mapeó correctamente
proveedor_text = dto.get('proveedor_text')
if proveedor_text and proveedor_text.strip():
    print(f'✅ proveedor_text mapeado correctamente: {proveedor_text}')
    print('')
    print('✅ La factura SERÁ ACEPTADA')
else:
    print('❌ proveedor_text NO se mapeó (será rechazada)')
    print('')
    print('🔍 Análisis:')
    if found_fields:
        print(f'   OpenAI devolvió: {list(found_fields.keys())[0]} = {list(found_fields.values())[0]}')
        print(f'   Pero el parser NO lo mapeó a proveedor_text')
        print('')
        print('   ⚠️  PROBLEMA: El mapeo no está funcionando correctamente')
    else:
        print('   OpenAI NO devolvió ningún campo relacionado con proveedor')
        print('')
        print('   ⚠️  PROBLEMA: El prompt de OpenAI no está extrayendo el proveedor')

# Limpiar archivo temporal
if os.path.exists(local_path):
    os.remove(local_path)
    print('')
    print('🧹 Archivo temporal eliminado')
