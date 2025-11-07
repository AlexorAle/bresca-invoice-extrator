#!/usr/bin/env python3
"""
Debug: Mejorar OCR con preprocesamiento
"""
import sys
from pathlib import Path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pdf_utils import pdf_to_image

pdf_path = Path(__file__).parent / 'temp' / 'Iberdrola Junio 2025.pdf'

print("\n🔍 Probando diferentes técnicas de OCR...")

# Técnica 1: Normal
print("\n1️⃣  Normal (DPI 200)...")
img = pdf_to_image(str(pdf_path), page=1, dpi=200)
if img:
    text1 = pytesseract.image_to_string(img, lang='spa+eng')
    
# Técnica 2: Mayor DPI
print("2️⃣  Mayor resolución (DPI 300)...")
img = pdf_to_image(str(pdf_path), page=1, dpi=300)
if img:
    text2 = pytesseract.image_to_string(img, lang='spa+eng')

# Técnica 3: Con preprocesamiento
print("3️⃣  Con preprocesamiento (contraste + nitidez)...")
img = pdf_to_image(str(pdf_path), page=1, dpi=250)
if img:
    # Convertir a escala de grises
    img = img.convert('L')
    # Aumentar contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    # Aumentar nitidez
    img = img.filter(ImageFilter.SHARPEN)
    text3 = pytesseract.image_to_string(img, lang='spa+eng')

# Buscar importes en todos los textos
def find_amounts(text, technique_name):
    print(f"\n📊 {technique_name}:")
    # Buscar patrones de dinero
    patterns = [
        r'(\d+[.,]\d{2})\s*€',
        r'€\s*(\d+[.,]\d{2})',
        r'TOTAL[:\s]+(\d+[.,]\d{2})',
        r'(\d{1,3}[.,]\d{2})',
    ]
    
    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        amounts.extend(matches)
    
    if amounts:
        unique_amounts = list(set(amounts))
        print(f"   Importes encontrados: {unique_amounts}")
        return unique_amounts
    else:
        print("   ❌ No se encontraron importes")
        return []

# Buscar en cada texto
amounts1 = find_amounts(text1, "DPI 200")
amounts2 = find_amounts(text2, "DPI 300")
amounts3 = find_amounts(text3, "Preprocesado")

# Mostrar extracto del texto preprocesado (más detalle)
print("\n" + "="*70)
print("EXTRACTO DEL TEXTO PREPROCESADO (líneas con números):")
print("="*70)
for line in text3.split('\n'):
    if any(c.isdigit() for c in line) and len(line.strip()) > 2:
        if not line.startswith('  →'):  # Evitar duplicar formato
            print(f"  {line.strip()}")

print("\n" + "="*70)


