#!/usr/bin/env python3

"""
Script detallado para probar OpenAI con una factura que falló
Revisa en profundidad la respuesta completa
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import base64
import logging

sys.path.insert(0, str(Path(__file__).parent / "src"))

load_dotenv()

from src.ocr_extractor import InvoiceExtractor, PROMPT_TEMPLATE
from src.logging_conf import get_logger

# Configurar logging para ver TODO
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = get_logger(__name__)

def test_openai_detailed(pdf_path: str):
    """Probar OpenAI con una factura y mostrar TODA la información detallada"""
    print(f"\n{'='*80}")
    print(f"🔍 PRUEBA DETALLADA DE OPENAI")
    print(f"{'='*80}")
    print(f"📄 PDF: {Path(pdf_path).name}")
    print(f"📁 Ruta: {pdf_path}")
    print(f"{'='*80}\n")
    
    # Verificar que el archivo existe
    if not Path(pdf_path).exists():
        print(f"❌ Error: El archivo no existe: {pdf_path}")
        return
    
    extractor = InvoiceExtractor()
    
    # Paso 1: Convertir PDF a imagen base64
    print("📸 PASO 1: Convirtiendo PDF a imagen base64...")
    print("-" * 80)
    try:
        img_base64 = extractor._pdf_to_base64_image(pdf_path)
        if not img_base64:
            print("❌ Error: No se pudo convertir PDF a imagen")
            return
        
        img_size_bytes = len(base64.b64decode(img_base64))
        print(f"✅ Imagen generada exitosamente")
        print(f"   - Tamaño base64: {len(img_base64):,} caracteres")
        print(f"   - Tamaño binario: {img_size_bytes:,} bytes ({img_size_bytes/1024:.2f} KB)")
        print(f"   - Ratio base64: {len(img_base64)/img_size_bytes:.2f}x")
    except Exception as e:
        print(f"❌ Error convirtiendo PDF: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n")
    
    # Paso 2: Mostrar el prompt que se enviará
    print("📝 PASO 2: Prompt que se enviará a OpenAI")
    print("-" * 80)
    print(PROMPT_TEMPLATE)
    print(f"\nLongitud del prompt: {len(PROMPT_TEMPLATE)} caracteres")
    print(f"\n")
    
    # Paso 3: Llamar a OpenAI
    print("🤖 PASO 3: Llamando a OpenAI API...")
    print("-" * 80)
    print(f"Modelo: {extractor.model}")
    print(f"Max tokens: 300")
    print(f"Temperature: 0.1")
    print(f"Detail: high")
    print(f"\n⏳ Enviando petición...\n")
    
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
        
        print("✅ Respuesta recibida de OpenAI\n")
        
        # Paso 4: Análisis completo de la respuesta
        print("📊 PASO 4: ANÁLISIS COMPLETO DE LA RESPUESTA")
        print("=" * 80)
        
        # 4.1 Metadata básica
        print("\n📋 4.1 METADATA BÁSICA:")
        print("-" * 80)
        print(f"   Modelo: {response.model}")
        print(f"   ID de respuesta: {response.id}")
        print(f"   Created timestamp: {response.created}")
        print(f"   Object type: {response.object}")
        
        # 4.2 Usage (tokens)
        print("\n📊 4.2 USAGE (TOKENS):")
        print("-" * 80)
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            print(f"   Prompt tokens: {usage.prompt_tokens:,}")
            print(f"   Completion tokens: {usage.completion_tokens:,}")
            print(f"   Total tokens: {usage.total_tokens:,}")
            print(f"   Ratio completion/prompt: {usage.completion_tokens/usage.prompt_tokens:.2f}x")
            
            # Análisis de tokens
            if usage.completion_tokens >= 300:
                print(f"   ⚠️  ADVERTENCIA: Se usaron {usage.completion_tokens} tokens de 300 (límite alcanzado)")
        else:
            print("   ⚠️  No hay información de usage disponible")
        
        # 4.3 Choices
        print("\n🎯 4.3 CHOICES:")
        print("-" * 80)
        if not response.choices:
            print("   ❌ ERROR: No hay choices en la respuesta")
            return
        
        choice = response.choices[0]
        print(f"   Número de choices: {len(response.choices)}")
        print(f"   Index: {choice.index}")
        print(f"   Finish reason: {choice.finish_reason}")
        
        # Análisis de finish_reason
        print(f"\n   📌 Análisis de finish_reason:")
        if choice.finish_reason == 'stop':
            print("      ✅ Normal: La respuesta se completó correctamente")
        elif choice.finish_reason == 'length':
            print("      ⚠️  PROBLEMA: La respuesta se cortó por límite de tokens")
            print("      💡 Solución: Aumentar max_tokens o simplificar el prompt")
        elif choice.finish_reason == 'content_filter':
            print("      ⚠️  PROBLEMA: La respuesta fue filtrada por contenido")
        elif choice.finish_reason is None:
            print("      ⚠️  PROBLEMA: finish_reason es None (respuesta incompleta)")
        else:
            print(f"      ⚠️  Finish reason desconocido: {choice.finish_reason}")
        
        # 4.4 Message Content
        print("\n💬 4.4 MESSAGE CONTENT:")
        print("-" * 80)
        
        if not choice.message:
            print("   ❌ ERROR: No hay message en el choice")
            return
        
        message = choice.message
        content = message.content
        
        print(f"   Role: {message.role}")
        print(f"   Content type: {type(content)}")
        print(f"   Content is None: {content is None}")
        print(f"   Content is empty string: {content == ''}")
        
        if content:
            content_stripped = content.strip()
            print(f"   Content length (raw): {len(content)} caracteres")
            print(f"   Content length (stripped): {len(content_stripped)} caracteres")
            print(f"   Content is whitespace only: {content_stripped == ''}")
            
            # Mostrar contenido completo
            print(f"\n   📄 CONTENIDO COMPLETO (sin truncar):")
            print(f"   {'-' * 78}")
            print(f"   [REPR] {repr(content_stripped)}")
            print(f"   {'-' * 78}")
            print(f"   [STRING]")
            print(f"   {content_stripped}")
            print(f"   {'-' * 78}")
            
            # Intentar parsear JSON
            print(f"\n   🔍 4.5 ANÁLISIS DE JSON:")
            print(f"   {'-' * 80}")
            try:
                parsed_json = json.loads(content_stripped)
                print(f"   ✅ JSON VÁLIDO!")
                print(f"   📋 Contenido parseado:")
                print(json.dumps(parsed_json, indent=6, ensure_ascii=False))
                
                # Validar campos esperados
                print(f"\n   ✅ Validación de campos:")
                expected_fields = ['nombre_cliente', 'importe_total', 'confianza']
                for field in expected_fields:
                    value = parsed_json.get(field)
                    if value is not None:
                        print(f"      ✅ {field}: {value}")
                    else:
                        print(f"      ⚠️  {field}: None (faltante)")
                
            except json.JSONDecodeError as e:
                print(f"   ❌ ERROR PARSEANDO JSON:")
                print(f"      Tipo: {type(e).__name__}")
                print(f"      Mensaje: {e}")
                print(f"      Posición del error: {e.pos}")
                print(f"      Línea: {e.lineno}, Columna: {e.colno}")
                
                # Mostrar contexto del error
                if e.pos < len(content_stripped):
                    start = max(0, e.pos - 50)
                    end = min(len(content_stripped), e.pos + 50)
                    context = content_stripped[start:end]
                    print(f"\n      📍 Contexto alrededor del error (posición {e.pos}):")
                    print(f"      {repr(context)}")
                    print(f"      {' ' * (e.pos - start + 7)}^")
                
                # Análisis de qué puede ser
                print(f"\n   🔍 Análisis del contenido:")
                if content_stripped.startswith('{'):
                    print(f"      ✅ Empieza con '{{' (JSON válido al inicio)")
                else:
                    print(f"      ❌ NO empieza con '{{' - puede ser texto plano")
                    print(f"      Primeros 100 caracteres: {repr(content_stripped[:100])}")
                
                if content_stripped.endswith('}'):
                    print(f"      ✅ Termina con '}}' (JSON válido al final)")
                else:
                    print(f"      ⚠️  NO termina con '}}' - puede estar incompleto")
                    print(f"      Últimos 100 caracteres: {repr(content_stripped[-100:])}")
                
                # Buscar patrones comunes
                if '```' in content_stripped:
                    print(f"      ⚠️  Contiene markdown code blocks (```)")
                if content_stripped.startswith('```'):
                    print(f"      ⚠️  Es un code block markdown, no JSON puro")
        else:
            print(f"   ❌ CONTENIDO VACÍO O None")
            print(f"   ⚠️  OpenAI no devolvió ningún contenido")
            print(f"   💡 Posibles causas:")
            print(f"      - La imagen no es legible")
            print(f"      - El modelo no pudo procesar la imagen")
            print(f"      - Error interno de OpenAI")
        
        # Resumen final
        print(f"\n{'='*80}")
        print("📋 RESUMEN FINAL")
        print(f"{'='*80}")
        print(f"✅ Llamada a OpenAI: Exitosa")
        print(f"📊 Tokens usados: {usage.total_tokens if hasattr(response, 'usage') and response.usage else 'N/A'}")
        print(f"🎯 Finish reason: {choice.finish_reason}")
        print(f"📝 Contenido recibido: {'Sí' if content else 'No'}")
        if content:
            try:
                json.loads(content.strip())
                print(f"✅ JSON válido: Sí")
            except:
                print(f"❌ JSON válido: No")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ ERROR llamando a OpenAI:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Usar una factura que falló
    test_file = "data/quarantine/20251102_151010_Fact CONWAY JULIO 25.pdf"
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    test_openai_detailed(test_file)

