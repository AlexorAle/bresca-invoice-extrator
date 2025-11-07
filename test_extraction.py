#!/usr/bin/env python3

"""
Script de prueba para validar la migración a OpenAI GPT-4.1 Vision API
Uso: python test_extraction.py <ruta_pdf>
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ocr_extractor import InvoiceExtractor

def test_extraction(pdf_path: str):
    """
    Probar extracción con OpenAI GPT-4.1-mini

    Args:
        pdf_path: Ruta al archivo PDF de prueba
    """
    print(f"Probando extracción con OpenAI GPT-4.1-mini...")
    print(f"Archivo: {pdf_path}")

    # Verificar que el archivo existe
    if not Path(pdf_path).exists():
        print(f"ERROR: Archivo no encontrado: {pdf_path}")
        return

    try:
        extractor = InvoiceExtractor()

        result = extractor.extract_invoice_data(pdf_path)

        print("\n=== RESULTADO ===")
        print(f"Cliente: {result.get('nombre_cliente')}")
        print(f"Importe: {result.get('importe_total')}")
        print(f"Confianza: {result.get('confianza')}")
        print(f"Método: {'OpenAI' if result.get('confianza') != 'baja' else 'Tesseract (fallback)'}")

        # Validaciones
        if result.get('confianza') in ['alta', 'media']:
            print("✅ OpenAI funcionó correctamente")
        else:
            print("⚠️  Usando fallback Tesseract - revisar configuración OpenAI")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Posibles causas:")
        print("- API key de OpenAI no configurada o inválida")
        print("- Dependencias faltantes (pip install -r requirements.txt)")
        print("- Archivo PDF corrupto")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_extraction.py <ruta_pdf>")
        print("Ejemplo: python test_extraction.py temp/factura_test.pdf")
        sys.exit(1)

    test_extraction(sys.argv[1])

