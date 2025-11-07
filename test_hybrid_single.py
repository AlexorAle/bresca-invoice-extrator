#!/usr/bin/env python3
"""
Prueba rápida de arquitectura híbrida
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from security.secrets import load_env
from ocr_extractor import InvoiceExtractor
from logging_conf import get_logger

# Cargar entorno
load_env()

logger = get_logger(__name__)

def test_hybrid():
    """Probar extracción híbrida con una sola factura"""
    
    pdf_path = Path(__file__).parent / 'temp' / 'Iberdrola Junio 2025.pdf'
    
    if not pdf_path.exists():
        print(f"❌ Error: Archivo no encontrado: {pdf_path}")
        return
    
    print("\n" + "="*70)
    print("🧪 PRUEBA DE ARQUITECTURA HÍBRIDA")
    print("="*70)
    print(f"Archivo: {pdf_path.name}\n")
    
    # Inicializar extractor
    extractor = InvoiceExtractor()
    
    print("🔄 Procesando con arquitectura híbrida...")
    print("   → Tesseract: extraerá números")
    print("   → Ollama: extraerá texto\n")
    
    # Extraer datos
    result = extractor.extract_invoice_data(str(pdf_path))
    
    # Mostrar resultados
    print("="*70)
    print("📊 RESULTADOS DE EXTRACCIÓN HÍBRIDA")
    print("="*70)
    
    print("\n🔢 CAMPOS NUMÉRICOS (Tesseract):")
    print(f"   Importe Total:    €{result.get('importe_total')}")
    print(f"   Base Imponible:   €{result.get('base_imponible')}")
    print(f"   Impuestos Total:  €{result.get('impuestos_total')}")
    print(f"   IVA %:            {result.get('iva_porcentaje')}%")
    
    print("\n📝 CAMPOS DE TEXTO (Ollama):")
    print(f"   Proveedor:        {result.get('proveedor_text')}")
    print(f"   Nº Factura:       {result.get('numero_factura')}")
    print(f"   Fecha Emisión:    {result.get('fecha_emision')}")
    print(f"   Moneda:           {result.get('moneda')}")
    
    print("\n⚙️  METADATOS:")
    print(f"   Confianza:        {result.get('confianza')}")
    print(f"   Extractor usado:  {result.get('extractor_used')}")
    print(f"   Extractor núm:    {result.get('extractor_numeros')}")
    print(f"   Extractor txt:    {result.get('extractor_texto')}")
    
    print("\n" + "="*70)
    
    # Validar resultado crítico
    if result.get('importe_total') is not None:
        print(f"\n✅ ¡ÉXITO! Tesseract extrajo importe total: €{result.get('importe_total')}")
    else:
        print("\n❌ FALLO: Tesseract NO extrajo el importe total")
    
    print("\n📄 JSON completo:")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    print()

if __name__ == '__main__':
    test_hybrid()


