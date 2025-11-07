#!/usr/bin/env python3
"""
Debug: Ver texto extraído por Tesseract
"""
import sys
from pathlib import Path
import pytesseract

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pdf_utils import pdf_to_image

pdf_path = Path(__file__).parent / 'temp' / 'Iberdrola Junio 2025.pdf'

print("\n🔍 Extrayendo texto con Tesseract...")

img = pdf_to_image(str(pdf_path), page=1, dpi=200)

if img:
    text = pytesseract.image_to_string(img, lang='spa+eng')
    
    print("\n" + "="*70)
    print("TEXTO EXTRAÍDO POR TESSERACT:")
    print("="*70)
    print(text)
    print("="*70)
    
    # Buscar líneas que contengan números grandes
    print("\n🔍 Líneas con números (posibles importes):")
    for line in text.split('\n'):
        if any(c.isdigit() for c in line):
            # Si tiene dígitos y tiene más de 2 caracteres
            if len(line.strip()) > 2:
                print(f"  → {line.strip()}")
else:
    print("❌ No se pudo convertir PDF a imagen")


