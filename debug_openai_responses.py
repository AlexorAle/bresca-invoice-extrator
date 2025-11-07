#!/usr/bin/env python3

"""
Script de debugging para investigar qué está devolviendo OpenAI realmente
NO hacer cambios, solo investigar
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import base64
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

from src.ocr_extractor import InvoiceExtractor, PROMPT_TEMPLATE
from src.logging_conf import get_logger

logger = get_logger(__name__)

def test_openai_with_pdf(pdf_path: str):
    """Probar OpenAI con un PDF específico y mostrar TODA la respuesta"""
    print(f"\n{'='*70}")
    print(f"🔍 DEBUGGING OpenAI - PDF: {Path(pdf_path).name}")
    print(f"{'='*70}\n")
    
    extractor = InvoiceExtractor()
    
    # Convertir PDF a imagen base64
    print("📸 Convirtiendo PDF a imagen...")
    try:
        img_base64 = extractor._pdf_to_base64_image(pdf_path)
        print(f"✅ Imagen generada: {len(img_base64)} caracteres base64")
        print(f"   (Tamaño aprox: {len(base64.b64decode(img_base64)) // 1024} KB)")
    except Exception as e:
        print(f"❌ Error convirtiendo PDF: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Llamar a OpenAI directamente
    print("\n🤖 Llamando a OpenAI API...")
    try:
        import openai
        
        response = extractor.client.chat.completions.create(
            model=extractor.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT_TEMPLATE},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
            temperature=0.1,
        )
        
        print("\n📊 RESPUESTA COMPLETA DE OPENAI:")
        print("="*70)
        
        # Información del response object
        print(f"\n📋 Metadata del Response:")
        print(f"   Model: {response.model}")
        print(f"   ID: {response.id}")
        print(f"   Created: {response.created}")
        print(f"   Usage: {response.usage}")
        
        # Contenido
        if response.choices:
            choice = response.choices[0]
            print(f"\n📝 Choice:")
            print(f"   Finish reason: {choice.finish_reason}")
            print(f"   Index: {choice.index}")
            
            if choice.message:
                content = choice.message.content
                print(f"\n💬 Message Content:")
                print(f"   Type: {type(content)}")
                print(f"   Length: {len(content) if content else 0}")
                print(f"   Is None: {content is None}")
                print(f"   Is Empty: {content == ''}")
                print(f"   Is Whitespace: {content.strip() == '' if content else 'N/A'}")
                
                print(f"\n📄 CONTENIDO COMPLETO (sin truncar):")
                print("-"*70)
                if content:
                    print(repr(content))  # repr muestra caracteres especiales
                    print("-"*70)
                    print(content)  # Contenido normal
                    print("-"*70)
                    
                    # Intentar parsear JSON
                    print(f"\n🔍 Intentando parsear como JSON...")
                    try:
                        parsed = json.loads(content)
                        print("✅ JSON válido!")
                        print(json.dumps(parsed, indent=2, ensure_ascii=False))
                    except json.JSONDecodeError as e:
                        print(f"❌ Error parseando JSON: {e}")
                        print(f"   Posición del error: {e.pos}")
                        if e.pos < len(content):
                            print(f"   Carácter problemático: {repr(content[max(0, e.pos-20):e.pos+20])}")
                else:
                    print("⚠️  CONTENIDO VACÍO O None")
        else:
            print("⚠️  No hay choices en la respuesta")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Error llamando a OpenAI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    
    # Probar con las facturas que fallaron
    test_files = [
        "temp/Fact CONWAY JULIO 25.pdf",
        "temp/Fact CONWAY JUL 25.pdf",
        "temp/Fact GIRO 1 jul 25.pdf",
        "temp/Fact CBG jul 25.pdf",
        "temp/Fact MÁS 9 jul 25.pdf",  # Esta fue la que funcionó
    ]
    
    # Solo probar con archivos que existan
    existing_files = [f for f in test_files if Path(f).exists()]
    
    if not existing_files:
        print("⚠️  No se encontraron archivos en temp/. ¿Quieres especificar un archivo?")
        if len(sys.argv) > 1:
            test_openai_with_pdf(sys.argv[1])
        else:
            print("Uso: python debug_openai_responses.py <ruta_pdf>")
    else:
        # Probar con el primero que exista
        print(f"📁 Archivos encontrados: {len(existing_files)}")
        print(f"🧪 Probando con: {existing_files[0]}")
        test_openai_with_pdf(existing_files[0])

