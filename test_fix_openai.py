#!/usr/bin/env python3

"""
Script para probar el fix de OpenAI con el extractor real
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

from src.ocr_extractor import InvoiceExtractor

def test_extraction(pdf_path: str):
    """Probar extracción con el extractor real"""
    print(f"\n{'='*70}")
    print(f"🧪 PRUEBA DEL FIX DE OPENAI")
    print(f"{'='*70}")
    print(f"📄 PDF: {Path(pdf_path).name}\n")
    
    extractor = InvoiceExtractor()
    
    print("⏳ Extrayendo datos...")
    result = extractor.extract_invoice_data(pdf_path)
    
    print(f"\n📊 RESULTADO:")
    print(f"   Cliente: {result.get('nombre_cliente')}")
    print(f"   Importe: {result.get('importe_total')}")
    print(f"   Confianza: {result.get('confianza')}")
    print(f"   Extractor usado: {result.get('extractor_used', 'N/A')}")
    
    if result.get('confianza') == 'alta' and result.get('importe_total'):
        print(f"\n✅ ¡ÉXITO! OpenAI funcionó correctamente")
        return True
    else:
        print(f"\n❌ Falló o confianza baja")
        return False

if __name__ == "__main__":
    test_file = "data/quarantine/20251102_151010_Fact CONWAY JULIO 25.pdf"
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    success = test_extraction(test_file)
    sys.exit(0 if success else 1)

