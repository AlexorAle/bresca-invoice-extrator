#!/usr/bin/env python3
"""Script rápido para probar extracción con Ollama"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from security.secrets import load_env, validate_secrets
from ocr_extractor import InvoiceExtractor

load_env()
validate_secrets()

pdf_path = Path(__file__).parent / 'temp' / 'Iberdrola Junio 2025.pdf'

print("="*60)
print("🧪 PRUEBA RÁPIDA CON OLLAMA")
print("="*60)
print(f"Archivo: {pdf_path}")
print(f"Modelo: llama3.2-vision:latest")
print("\nExtrayendo datos (esto puede tardar 60-120 segundos)...\n")

extractor = InvoiceExtractor()
raw_data = extractor.extract_invoice_data(str(pdf_path))

print("\n" + "="*60)
print("📊 RESULTADOS DE EXTRACCIÓN")
print("="*60)
print(f"Confianza:      {raw_data.get('confianza', 'N/A')}")
print(f"Extractor:      {'Ollama' if raw_data.get('confianza') != 'baja' else 'Tesseract'}")
print(f"Proveedor:      {raw_data.get('proveedor_text', 'N/A')}")
print(f"Número:         {raw_data.get('numero_factura', 'N/A')}")
print(f"Fecha:          {raw_data.get('fecha_emision', 'N/A')}")
print(f"Importe Total:  €{raw_data.get('importe_total', 'N/A')}")
print(f"Base Imponible: €{raw_data.get('base_imponible', 'N/A')}")
print(f"IVA %:          {raw_data.get('iva_porcentaje', 'N/A')}%")
print(f"Impuestos:      €{raw_data.get('impuestos_total', 'N/A')}")
print("="*60)

if raw_data.get('importe_total'):
    print("\n✅ ¡ÉXITO! Ollama extrajo el importe correctamente")
else:
    print("\n⚠️  Importe no extraído (puede ser problema con el PDF o el modelo)")




