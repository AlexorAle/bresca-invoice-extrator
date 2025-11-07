#!/usr/bin/env python3

"""
Prueba final de migración OpenAI
"""

from dotenv import load_dotenv
from src.ocr_extractor import InvoiceExtractor
import os

load_dotenv()

print('🧪 PRUEBA FINAL DE MIGRACIÓN OPENAI')
print('=' * 50)

extractor = InvoiceExtractor()
print('✅ Extractor inicializado correctamente')

# Verificar que usa el modelo correcto
print(f'📋 Modelo configurado: {extractor.model}')

# Verificar que la API key está configurada
api_key = os.getenv('OPENAI_API_KEY')
print(f'🔑 API Key configurada: {"SÍ" if api_key else "NO"}')

print('\n🎯 PRUEBA DE EXTRACCIÓN:')
result = extractor.extract_invoice_data('temp/Iberdrola Junio 2025.pdf')
print(f'👤 Cliente: {result.get("nombre_cliente", "N/A")}')
print(f'💰 Importe: {result.get("importe_total", "N/A")}')
print(f'🎚️  Confianza: {result.get("confianza", "N/A")}')

if result.get('confianza') in ['alta', 'media']:
    print('✅ ¡MIGRACIÓN EXITOSA! OpenAI está funcionando correctamente')
else:
    print('⚠️  Usando fallback Tesseract')

print('\n📊 ESTADÍSTICAS ESPERADAS:')
print('- Procesamiento: 2-5 segundos por factura')
print('- Costo estimado: ~$1-2/mes (100 facturas)')
print('- Precisión: >95% con GPT-4o-mini')
