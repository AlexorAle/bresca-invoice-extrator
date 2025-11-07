#!/usr/bin/env python3
"""
Script para probar una sola factura sin Google Drive
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from security.secrets import load_env, validate_secrets
from logging_conf import get_logger
from db.database import get_database
from db.repositories import FacturaRepository, EventRepository
from ocr_extractor import InvoiceExtractor
from parser_normalizer import create_factura_dto
from pipeline.validate import validate_business_rules, validate_file_integrity

# Cargar entorno
load_env()
validate_secrets()

logger = get_logger(__name__)

def test_invoice(pdf_path: str):
    """Probar procesamiento de una factura"""
    
    logger.info(f"Probando factura: {pdf_path}")
    
    print("\n" + "="*60)
    print("🧪 TEST DE FACTURA INDIVIDUAL")
    print("="*60)
    print(f"Archivo: {pdf_path}\n")
    
    # Validar archivo
    print("1️⃣  Validando archivo...")
    if not validate_file_integrity(pdf_path):
        print("❌ Archivo no válido")
        return
    
    print("✅ Archivo válido")
    
    # Extraer datos
    print("\n2️⃣  Extrayendo datos con OCR...")
    print("   (Esto puede tomar 30-60 segundos...)")
    
    extractor = InvoiceExtractor()
    raw_data = extractor.extract_invoice_data(pdf_path)
    
    print("\n📄 Datos extraídos:")
    print("-" * 60)
    import json
    print(json.dumps(raw_data, indent=2, ensure_ascii=False))
    print("-" * 60)
    
    # Crear DTO
    print("\n3️⃣  Normalizando datos...")
    metadata = {
        'drive_file_id': 'test_manual_' + Path(pdf_path).stem.replace(' ', '_'),
        'drive_file_name': Path(pdf_path).name,
        'drive_folder_name': 'test',
        'extractor': 'ollama' if raw_data.get('confianza') != 'baja' else 'tesseract'
    }
    
    dto = create_factura_dto(raw_data, metadata)
    
    print("✅ DTO creado:")
    print("-" * 60)
    print(json.dumps(dto, indent=2, ensure_ascii=False, default=str))
    print("-" * 60)
    
    # Validar
    print("\n4️⃣  Validando reglas de negocio...")
    if validate_business_rules(dto):
        print("✅ Validación exitosa")
    else:
        print("⚠️  Validación falló - estado: revisar")
        print(f"   Estado: {dto.get('estado')}")
        if dto.get('error_msg'):
            print(f"   Error: {dto.get('error_msg')}")
    
    # Guardar en BD
    print("\n5️⃣  Guardando en base de datos...")
    db = get_database()
    repo = FacturaRepository(db)
    
    try:
        factura_id = repo.upsert_factura(dto)
        print(f"✅ Factura guardada con ID: {factura_id}")
        
        # Registrar evento
        event_repo = EventRepository(db)
        event_repo.insert_event(
            dto['drive_file_id'],
            'test_manual',
            'INFO',
            f'Prueba manual exitosa - ID: {factura_id}'
        )
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("🎉 ¡PRUEBA COMPLETADA EXITOSAMENTE!")
        print("="*60)
        print(f"ID Factura:      {factura_id}")
        print(f"Proveedor:       {dto.get('proveedor_text', 'N/A')}")
        print(f"Número:          {dto.get('numero_factura', 'N/A')}")
        print(f"Fecha:           {dto.get('fecha_emision', 'N/A')}")
        print(f"Importe:         €{dto.get('importe_total', 0)}")
        print(f"Confianza:       {dto.get('confianza', 'N/A')}")
        print(f"Extractor:       {dto.get('extractor', 'N/A')}")
        print(f"Estado:          {dto.get('estado', 'N/A')}")
        print("="*60)
        
        print("\n💡 Puedes ver la factura en el dashboard:")
        print("   streamlit run src/dashboard/app.py")
        print("\n📊 O consultar estadísticas:")
        print("   python src/main.py --stats")
        
    except Exception as e:
        print(f"\n❌ Error guardando en BD: {e}")
        logger.error(f"Error en test: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ Uso incorrecto")
        print("\nUso:")
        print(f"   python {Path(__file__).name} <ruta_a_factura.pdf>")
        print("\nEjemplo:")
        print(f'   python {Path(__file__).name} temp/mi_factura.pdf')
        print(f'   python {Path(__file__).name} "temp/Factura template.pdf"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"\n❌ Archivo no encontrado: {pdf_path}")
        print("\n💡 Verifica que:")
        print("   1. El archivo existe en la ruta especificada")
        print("   2. Si el nombre tiene espacios, usa comillas")
        print(f'\n   Ejemplo: python {Path(__file__).name} "temp/Factura template.pdf"')
        sys.exit(1)
    
    test_invoice(pdf_path)
