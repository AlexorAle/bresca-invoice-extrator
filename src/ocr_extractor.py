"""
Extracción de datos de facturas usando OpenAI GPT-4.1 Vision API y Tesseract OCR como fallback
"""
import base64
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from tenacity import retry, wait_random_exponential, stop_after_attempt
import openai
import pytesseract
from PIL import Image
import io

from src.pdf_utils import pdf_to_base64, pdf_to_image
from src.logging_conf import get_logger

logger = get_logger(__name__)

# Prompt optimizado para extracción de facturas
PROMPT_TEMPLATE = """Eres un experto en análisis de facturas. Analiza esta imagen de factura y extrae la información en formato JSON.

INSTRUCCIONES CRÍTICAS:

1. Busca el NOMBRE DEL PROVEEDOR/EMISOR (la empresa que EMITE la factura):
   - Suele estar en el header/logo de la factura
   - Campos como "Emitido por:", "From:", nombre de la empresa en el encabezado
   - Es la empresa que vende/presta el servicio (ej: "Energya-VM comercializadora", "CONWAY", etc.)
   - ⚠️ CRÍTICO: Este campo es OBLIGATORIO. Si no lo encuentras, usa null pero la factura será marcada como problemática

2. Busca el NIF/CIF/VAT DEL PROVEEDOR (identificación fiscal del proveedor):
   - Campos como "NIF:", "CIF:", "VAT:", "Tax ID:", "N.I.F.:", "Identificación fiscal:"
   - Suele estar cerca del nombre del proveedor en el header
   - Formato típico: letra seguida de 8 dígitos (ej: "B12345678", "A28123456")
   - NUEVO CAMPO CRÍTICO: Este campo es MUY IMPORTANTE para identificar proveedores únicos
   - Si no lo encuentras, usa null

3. Busca el NOMBRE DEL CLIENTE (la empresa que RECIBE la factura):
   - Campos como "Cliente:", "Bill to:", "Facturar a:", "Datos cliente"
   - Es la empresa que compra/recibe el servicio (ej: "MANTUA EAGLE SL", etc.)

3. Busca el IMPORTE TOTAL (campos como "Total:", "Total a pagar:", "Amount Due:", la cifra final más grande)

4. Busca la FECHA DE EMISIÓN (campos como "Fecha:", "Fecha de emisión:", "Date:", "Issue date:", "Emitida el:", etc.)

5. Busca la BASE IMPONIBLE (campos como "Base imponible:", "Base:", "Subtotal:", "Base IVA:", "Base sin IVA:")
   - Es el importe SIN impuestos/IVA
   - Si no encuentras este campo explícito, puedes calcularlo: base_imponible = importe_total / (1 + iva_porcentaje/100)

6. Busca el TOTAL DE IMPUESTOS/IVA (campos como "IVA:", "Impuestos:", "Tax:", "Total IVA:", "Impuesto:")
   - Es la suma de todos los impuestos aplicados
   - Si no encuentras este campo explícito, puedes calcularlo: impuestos_total = importe_total - base_imponible

7. Busca el PORCENTAJE DE IVA (campos como "IVA 21%", "21% IVA", "Tax rate:", "Tipo IVA:")
   - Es el porcentaje de IVA aplicado (ej: 21, 10, 4)
   - Si no encuentras este campo explícito pero tienes base_imponible e impuestos_total, calcula: iva_porcentaje = (impuestos_total / base_imponible) * 100

8. Si encuentras varios totales, usa el ÚLTIMO o el que indica "Total final" o "Total con IVA"

9. Para los importes, devuelve SOLO el número (sin símbolos de moneda)

10. Para la fecha, devuelve en formato YYYY-MM-DD (ejemplo: 2025-07-15)

11. Indica tu nivel de confianza: "alta" si los datos son claros, "media" si hay ambigüedad, "baja" si hay dudas significativas

FORMATO DE RESPUESTA (devuelve SOLO este JSON, sin texto adicional):

{
  "nombre_proveedor": "Nombre exacto del proveedor/emisor de la factura",
  "proveedor_nif": "B12345678",
  "nombre_cliente": "Nombre exacto del cliente que recibe la factura",
  "importe_total": 1234.56,
  "base_imponible": 1020.30,
  "impuestos_total": 214.26,
  "iva_porcentaje": 21.0,
  "fecha_emision": "2025-07-15",
  "confianza": "alta"
}

REGLAS:
- nombre_proveedor: ⚠️ OBLIGATORIO - Empresa que emite la factura (header/logo). Si no encuentras, usa null
- proveedor_nif: ⚠️ MUY IMPORTANTE - NIF/CIF/VAT del proveedor. Busca cerca del nombre del proveedor. Si no encuentras, usa null
- nombre_cliente: Empresa que recibe la factura (opcional, puede ser null)
- importe_total: Número decimal (usa punto como separador decimal) - OBLIGATORIO
- base_imponible: Número decimal - Base sin IVA. Si no encuentras, intenta calcular desde importe_total e iva_porcentaje
- impuestos_total: Número decimal - Total de IVA/impuestos. Si no encuentras, intenta calcular desde importe_total y base_imponible
- iva_porcentaje: Número decimal - Porcentaje de IVA (ej: 21.0 para 21%). Si no encuentras, intenta calcular desde base_imponible e impuestos_total
- fecha_emision: Fecha en formato YYYY-MM-DD (si no encuentras fecha, usa null)
- confianza: Valores válidos: "alta", "media", "baja"
- Si no encuentras algún dato, usa null
- IMPORTANTE: Si solo tienes importe_total, intenta calcular base_imponible e impuestos_total asumiendo un IVA común (21%, 10%, 4%)
"""

class InvoiceExtractor:
    """Extractor de datos de facturas con OpenAI GPT-4.1 Vision API y fallback a Tesseract"""
    
    def __init__(self, api_key: str = None):
        """
        Inicializar extractor con OpenAI
        
        Args:
            api_key: API key de OpenAI (default: desde env)
        """
        # Inicializar cliente OpenAI sin proxies para evitar conflictos de versión
        api_key_value = api_key or os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key_value)
        self.model = "gpt-4o-mini"  # Modelo más económico con capacidades de visión
        self.tesseract_cmd = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
        self.tesseract_lang = os.getenv('TESSERACT_LANG', 'spa+eng')
        
        # Configurar Tesseract
        if os.path.exists(self.tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        
        logger.info(f"InvoiceExtractor inicializado - OpenAI modelo: {self.model}")

    def _pdf_to_base64_image(self, pdf_path: str) -> Optional[str]:
        """
        Convertir primera página de PDF a imagen base64

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Imagen en formato base64 o None si falla
        """
        try:
            from pdf2image import convert_from_path

            # Convertir primera página a imagen
            images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=1)

            if not images:
                logger.error("No se pudo convertir PDF a imagen")
                return None

            img = images[0]

            # Convertir a RGB si es necesario
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Redimensionar si es demasiado grande (límite de OpenAI)
            max_size = 1024  # Máximo 1024x1024 para evitar problemas
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.debug(f"Imagen redimensionada a: {img.size}")

            # Convertir a base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.debug(f"PDF convertido a base64 ({len(img_base64)} caracteres)")
            return img_base64

        except Exception as e:
            logger.error(f"Error convirtiendo PDF a base64: {e}")
            return None
    
    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6)
    )
    def _extract_with_openai(self, img_base64: str) -> dict:
        """
        Extraer datos usando OpenAI GPT-4 Vision API con retry automático
        
        Args:
            img_base64: Imagen en formato base64
        
        Returns:
            Diccionario con datos extraídos
        """
        try:
            logger.debug("Enviando imagen a OpenAI Vision API")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT_TEMPLATE},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}",
                                    "detail": "high"  # Alta resolución para mejor lectura de texto
                                }
                            }
                        ]
                    }
                ],
                max_tokens=400,  # Aumentado para incluir nombre_proveedor y nombre_cliente
                temperature=0.1,  # Baja para respuestas deterministas
                response_format={"type": "json_object"}  # Forzar JSON puro sin markdown
            )

            # Extraer información de la respuesta
            choice = response.choices[0]
            finish_reason = choice.finish_reason
            content = choice.message.content
            
            # Logging de metadata de la respuesta
            logger.debug(f"OpenAI response metadata - Model: {response.model}, ID: {response.id}")
            if hasattr(response, 'usage') and response.usage:
                logger.debug(f"OpenAI usage - Prompt tokens: {response.usage.prompt_tokens}, "
                           f"Completion tokens: {response.usage.completion_tokens}, "
                           f"Total tokens: {response.usage.total_tokens}")
            logger.debug(f"OpenAI finish_reason: {finish_reason}")
            
            # Validar que hay contenido
            if not content:
                logger.warning("OpenAI devolvió respuesta vacía (content es None o vacío)")
                logger.warning(f"Finish reason: {finish_reason}")
                if hasattr(response, 'usage'):
                    logger.warning(f"Tokens usados: {response.usage.total_tokens if response.usage else 'N/A'}")
                return {
                    'nombre_proveedor': None,
                    'proveedor_nif': None,
                    'nombre_cliente': None, 
                    'importe_total': None,
                    'base_imponible': None,
                    'impuestos_total': None,
                    'iva_porcentaje': None,
                    'confianza': 'baja'
                }
            
            # Verificar si la respuesta se cortó por límite de tokens
            if finish_reason == 'length':
                logger.warning(f"OpenAI respuesta cortada por límite de tokens (max_tokens=400). "
                             f"Considera aumentar max_tokens si esto ocurre frecuentemente.")
            
            # Logging del contenido (solo primeros 200 chars para debug normal)
            content_stripped = content.strip()
            logger.debug(f"OpenAI raw response (primeros 200 chars): '{content_stripped[:200]}...'")
            logger.debug(f"OpenAI response length: {len(content_stripped)} caracteres")

            # Limpiar markdown code blocks si existen (respaldo por si OpenAI no respeta response_format)
            if content_stripped.startswith('```'):
                logger.debug("Detectado markdown code block, limpiando...")
                # Eliminar ```json o ``` al inicio
                if content_stripped.startswith('```json'):
                    content_stripped = content_stripped[7:].strip()
                elif content_stripped.startswith('```'):
                    content_stripped = content_stripped[3:].strip()
                # Eliminar ``` al final
                if content_stripped.endswith('```'):
                    content_stripped = content_stripped[:-3].strip()
                logger.debug(f"Contenido después de limpiar markdown: '{content_stripped[:200]}...'")

            # Parsear JSON
            try:
                data = json.loads(content_stripped)
            except json.JSONDecodeError as e:
                logger.warning(f"Error parseando JSON de OpenAI: {e}")
                logger.warning(f"Finish reason: {finish_reason}")
                logger.warning(f"Longitud del contenido: {len(content_stripped)} caracteres")
                # Log contenido completo cuando hay error (sin truncar)
                logger.warning(f"Contenido completo recibido (sin truncar): {repr(content_stripped)}")
                # Log también como string normal para debugging visual
                logger.warning(f"Contenido como string: {content_stripped}")
                return {
                    'nombre_proveedor': None,
                    'proveedor_nif': None,
                    'nombre_cliente': None, 
                    'importe_total': None,
                    'base_imponible': None,
                    'impuestos_total': None,
                    'iva_porcentaje': None,
                    'confianza': 'baja'
                }

            # Validación y conversión de campos numéricos
            if data.get('importe_total') is not None:
                data['importe_total'] = float(data['importe_total'])
            
            if data.get('base_imponible') is not None:
                data['base_imponible'] = float(data['base_imponible'])
            
            if data.get('impuestos_total') is not None:
                data['impuestos_total'] = float(data['impuestos_total'])
            
            if data.get('iva_porcentaje') is not None:
                data['iva_porcentaje'] = float(data['iva_porcentaje'])

            logger.info(f"Extracción OpenAI exitosa - Confianza: {data.get('confianza', 'desconocida')}")

            return data
    
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit alcanzado: {e}")
            raise  # Retry automático por tenacity
        except openai.APIConnectionError as e:
            logger.warning(f"Error de conexión: {e}")
            raise  # Retry automático
        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON de OpenAI: {e}")
            return {
                'nombre_proveedor': None,
                'proveedor_nif': None,
                'nombre_cliente': None, 
                'importe_total': None,
                'base_imponible': None,
                'impuestos_total': None,
                'iva_porcentaje': None,
                'confianza': 'baja'
            }
        except Exception as e:
            logger.error(f"Error inesperado en OpenAI: {e}")
            raise

    def _extract_with_tesseract(self, pdf_path: str) -> dict:
        """
        Extraer datos usando Tesseract OCR (fallback)
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            Diccionario con datos extraídos (confianza siempre 'baja')
        """
        logger.info("Usando Tesseract como fallback")
        
        try:
            # Convertir PDF a imagen
            img = pdf_to_image(pdf_path, page=1, dpi=150)
            
            if img is None:
                logger.error("No se pudo convertir PDF a imagen para Tesseract")
                return self._empty_result()
            
            # Extraer texto
            text = pytesseract.image_to_string(img, lang=self.tesseract_lang)
            
            logger.debug(f"Texto extraído por Tesseract ({len(text)} caracteres)")
            
            # Aplicar regex para extraer campos básicos
            data = {
                'nombre_cliente': self._extract_cliente(text),
                'importe_total': self._extract_importe_total(text),
                'confianza': 'baja'  # Tesseract es aproximado
            }
            
            logger.info(f"Extracción Tesseract completada - Cliente: {data.get('nombre_cliente', 'N/A')}")
            
            return data
        
        except Exception as e:
            logger.error(f"Error en extracción Tesseract: {e}")
            return self._empty_result()
    
    def _extract_cliente(self, text: str) -> Optional[str]:
        """Extraer nombre del cliente con regex"""
        import re

        patterns = [
            r'(Cliente|Bill to|Facturar a|Razón Social):?\s*([A-Z][^\n]{5,})',
            r'(Empresa|Company|Proveedor):?\s*([A-Z][^\n]{5,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(2).strip()
        
        return None
    
    def _extract_importe_total(self, text: str) -> Optional[float]:
        """Extraer importe total con regex"""
        import re

        patterns = [
            r'(Total|TOTAL|Importe Total|Amount|Total a pagar):?\s*€?\s*(\d+[.,]?\d*)',
            r'€\s*(\d+[.,]\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Obtener el último grupo que contiene el número
                amount_str = match.groups()[-1]
                amount_str = amount_str.replace(',', '.')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def _is_pdf_protected(self, pdf_path: str) -> bool:
        """
        Verificar si un PDF está protegido con contraseña

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            True si está protegido, False en caso contrario
        """
        try:
            from pypdf import PdfReader

            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                # Verificar si está encriptado
                return reader.is_encrypted
        except Exception as e:
            logger.warning(f"Error verificando protección PDF {pdf_path}: {e}")
            # Si no podemos verificar, asumimos que no está protegido para continuar
            return False

    def _protected_pdf_result(self, pdf_path: str) -> dict:
        """
        Retornar resultado específico para PDFs protegidos

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Diccionario indicando que el PDF está protegido
        """
        return {
            'nombre_cliente': None,
            'importe_total': None,
            'confianza': 'baja',
            'estado': 'protegido',
            'error_msg': f'PDF protegido con contraseña: {Path(pdf_path).name}'
        }

    def _empty_result(self) -> dict:
        """Retornar resultado vacío cuando falla todo"""
        return {
            'nombre_proveedor': None,
            'proveedor_nif': None,
            'nombre_cliente': None,
            'importe_total': None,
            'base_imponible': None,
            'impuestos_total': None,
            'iva_porcentaje': None,
            'confianza': 'baja'
        }
    
    def extract_invoice_data(self, pdf_path: str) -> dict:
        """
        Extraer datos de factura (primero OpenAI, fallback Tesseract)
        
        Args:
            pdf_path: Ruta al archivo PDF
        
        Returns:
            Diccionario con datos extraídos
        """
        try:
            logger.info(f"Iniciando extracción de: {pdf_path}")

            # Verificar si el PDF está protegido con contraseña
            if self._is_pdf_protected(pdf_path):
                logger.warning(f"PDF protegido con contraseña: {pdf_path} - omitiendo procesamiento")
                return self._protected_pdf_result(pdf_path)

            # Convertir PDF a base64
            img_base64 = self._pdf_to_base64_image(pdf_path)

            if img_base64 is None:
                logger.warning("No se pudo convertir PDF a base64, usando Tesseract")
                return self._extract_with_tesseract(pdf_path)

            try:
                # Intentar con OpenAI primero
                data = self._extract_with_openai(img_base64)

                # Si OpenAI dio confianza baja o no encontró importe, intentar Tesseract como complemento
                if data.get('confianza') == 'baja' or not data.get('importe_total'):
                    logger.info("OpenAI confianza baja o sin importe, complementando con Tesseract")
                    tesseract_data = self._extract_with_tesseract(pdf_path)

                    # Combinar resultados (priorizar OpenAI pero llenar campos faltantes)
                    for key, value in tesseract_data.items():
                        if key != 'confianza' and not data.get(key) and value:
                            data[key] = value

                return data

            except Exception as openai_error:
                logger.warning(f"Error en OpenAI: {openai_error}, usando Tesseract")
                return self._extract_with_tesseract(pdf_path)
        
        except Exception as e:
            logger.error(f"Error en extracción de factura {pdf_path}: {e}")
            return self._empty_result()
    
    def batch_extract(self, pdf_paths: List[str]) -> Dict[str, dict]:
        """
        Extraer datos de múltiples PDFs con delay entre llamadas para evitar rate limits
        
        Args:
            pdf_paths: Lista de rutas a archivos PDF
        
        Returns:
            Diccionario {ruta: datos_extraídos}
        """
        results = {}
        total = len(pdf_paths)
        
        logger.info(f"Iniciando extracción batch de {total} archivos")
        
        for idx, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"Procesando {idx}/{total}: {pdf_path}")
            results[pdf_path] = self.extract_invoice_data(pdf_path)
        
            # Delay para prevenir rate limits en batch processing
            if idx < total:  # No esperar después del último
                time.sleep(0.5)

        logger.info(f"Extracción batch completada: {total} archivos procesados")
        
        return results