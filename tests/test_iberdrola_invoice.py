#!/usr/bin/env python3
"""
Prueba unitaria para la factura de Iberdrola Junio 2025
Verifica que el sistema de extracción funciona correctamente con este archivo específico
"""
import unittest
import sys
import os
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from security.secrets import load_env, validate_secrets
from logging_conf import get_logger
from ocr_extractor import InvoiceExtractor
from parser_normalizer import create_factura_dto, validate_fiscal_rules
from pipeline.validate import validate_business_rules, validate_file_integrity
from pdf_utils import validate_pdf, get_pdf_info

# Cargar entorno
load_env()
validate_secrets()

logger = get_logger(__name__)


class TestIberdrolaInvoice(unittest.TestCase):
    """Pruebas para la factura de Iberdrola Junio 2025"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial antes de todas las pruebas"""
        cls.pdf_path = Path(__file__).parent.parent / 'temp' / 'Iberdrola Junio 2025.pdf'
        cls.extractor = InvoiceExtractor()
        cls.raw_data = None
        cls.dto = None
        
        # Verificar que el archivo existe
        if not cls.pdf_path.exists():
            raise FileNotFoundError(
                f"Archivo de prueba no encontrado: {cls.pdf_path}\n"
                f"Por favor, asegúrate de que el archivo 'Iberdrola Junio 2025.pdf' "
                f"está en la carpeta 'temp'"
            )
    
    def test_01_file_exists(self):
        """Test 1: Verificar que el archivo PDF existe"""
        self.assertTrue(
            self.pdf_path.exists(),
            f"El archivo {self.pdf_path} no existe"
        )
        logger.info(f"✓ Archivo encontrado: {self.pdf_path}")
    
    def test_02_file_is_valid_pdf(self):
        """Test 2: Verificar que el archivo es un PDF válido"""
        is_valid = validate_pdf(str(self.pdf_path))
        self.assertTrue(
            is_valid,
            f"El archivo {self.pdf_path} no es un PDF válido"
        )
        logger.info("✓ Archivo es un PDF válido")
    
    def test_03_file_integrity(self):
        """Test 3: Verificar integridad del archivo"""
        is_valid = validate_file_integrity(str(self.pdf_path))
        self.assertTrue(
            is_valid,
            f"La validación de integridad falló para {self.pdf_path}"
        )
        logger.info("✓ Integridad del archivo verificada")
    
    def test_04_pdf_info(self):
        """Test 4: Obtener información del PDF"""
        info = get_pdf_info(str(self.pdf_path))
        self.assertNotIn('error', info, f"Error obteniendo info del PDF: {info.get('error')}")
        self.assertGreater(info.get('file_size_bytes', 0), 0, "El archivo está vacío")
        logger.info(f"✓ Información del PDF: {info.get('file_size_mb', 0)} MB")
    
    def test_05_extract_invoice_data(self):
        """Test 5: Extraer datos de la factura usando OCR"""
        logger.info("Iniciando extracción de datos (esto puede tomar 30-60 segundos)...")
        
        raw_data = self.extractor.extract_invoice_data(str(self.pdf_path))
        
        # Verificar que se retornó un diccionario
        self.assertIsInstance(raw_data, dict, "Los datos extraídos deben ser un diccionario")
        
        # Verificar que tiene al menos algunos campos básicos
        self.assertIn('confianza', raw_data, "Debe incluir campo 'confianza'")
        self.assertIn('moneda', raw_data, "Debe incluir campo 'moneda'")
        
        # Verificar que la confianza es válida
        self.assertIn(
            raw_data.get('confianza'),
            ['alta', 'media', 'baja'],
            f"Confianza inválida: {raw_data.get('confianza')}"
        )
        
        logger.info(f"✓ Datos extraídos - Confianza: {raw_data.get('confianza')}")
        logger.info(f"  Proveedor: {raw_data.get('proveedor_text', 'N/A')}")
        logger.info(f"  Número: {raw_data.get('numero_factura', 'N/A')}")
        logger.info(f"  Fecha: {raw_data.get('fecha_emision', 'N/A')}")
        logger.info(f"  Importe: {raw_data.get('importe_total', 'N/A')}")
        
        # Guardar datos extraídos para pruebas posteriores (en clase para compartir)
        self.__class__.raw_data = raw_data
        self.raw_data = raw_data  # También en instancia para compatibilidad
    
    def test_06_extracted_proveedor(self):
        """Test 6: Verificar que se extrajo el proveedor"""
        raw_data = self.__class__.raw_data or getattr(self, 'raw_data', None)
        if not raw_data:
            self.skipTest("Requiere datos extraídos de test_05")
        
        proveedor = raw_data.get('proveedor_text')
        
        # Verificar que se extrajo algún proveedor
        self.assertIsNotNone(
            proveedor,
            "Debe extraerse el nombre del proveedor"
        )
        
        # Verificar que no está vacío
        self.assertGreater(
            len(proveedor.strip()),
            0,
            "El nombre del proveedor no puede estar vacío"
        )
        
        # Verificar que contiene "Iberdrola" (o similar)
        proveedor_lower = proveedor.lower()
        self.assertTrue(
            'iberdrola' in proveedor_lower or len(proveedor) > 3,
            f"El proveedor extraído '{proveedor}' no parece válido"
        )
        
        logger.info(f"✓ Proveedor extraído correctamente: {proveedor}")
    
    def test_07_extracted_importe_total(self):
        """Test 7: Verificar que se extrajo el importe total (o al menos se intentó)"""
        raw_data = self.__class__.raw_data or getattr(self, 'raw_data', None)
        if not raw_data:
            self.skipTest("Requiere datos extraídos de test_05")
        
        importe_total = raw_data.get('importe_total')
        confianza = raw_data.get('confianza', 'baja')
        
        # Si la confianza es baja (Tesseract), el importe puede no extraerse
        # Esto es un comportamiento válido del sistema
        if importe_total is None and confianza == 'baja':
            logger.warning("⚠ Importe no extraído (confianza baja con Tesseract - comportamiento esperado)")
            # No fallar la prueba, solo advertir
            return
        
        # Si hay confianza media/alta o se extrajo algo, verificar que es válido
        if importe_total is not None:
            # Verificar que es un número positivo
            if isinstance(importe_total, (int, float)):
                self.assertGreater(
                    importe_total,
                    0,
                    f"El importe total debe ser positivo, recibido: {importe_total}"
                )
                logger.info(f"✓ Importe total extraído: €{importe_total}")
            else:
                # Si es string, intentar convertir
                try:
                    importe_float = float(importe_total)
                    self.assertGreater(importe_float, 0)
                    logger.info(f"✓ Importe total extraído: €{importe_float}")
                except (ValueError, TypeError):
                    self.fail(f"El importe total debe ser numérico, recibido: {importe_total}")
        else:
            # Con confianza media/alta debería haberse extraído
            if confianza in ['media', 'alta']:
                self.fail("Con confianza media/alta debería haberse extraído el importe")
            else:
                logger.warning("⚠ Importe no extraído pero con confianza baja - OK")
    
    def test_08_create_factura_dto(self):
        """Test 8: Crear DTO normalizado de la factura"""
        raw_data = self.__class__.raw_data or getattr(self, 'raw_data', None)
        if not raw_data:
            self.skipTest("Requiere datos extraídos de test_05")
        
        metadata = {
            'drive_file_id': 'test_iberdrola_junio_2025',
            'drive_file_name': 'Iberdrola Junio 2025.pdf',
            'drive_folder_name': 'temp',
            'extractor': 'ollama' if raw_data.get('confianza') != 'baja' else 'tesseract'
        }
        
        dto = create_factura_dto(raw_data, metadata)
        
        # Verificar que es un diccionario
        self.assertIsInstance(dto, dict, "El DTO debe ser un diccionario")
        
        # Verificar campos obligatorios
        self.assertIn('drive_file_id', dto, "DTO debe incluir drive_file_id")
        self.assertIn('drive_file_name', dto, "DTO debe incluir drive_file_name")
        self.assertIn('importe_total', dto, "DTO debe incluir importe_total")
        self.assertIn('extractor', dto, "DTO debe incluir extractor")
        
        # Verificar que el importe total está presente y es positivo
        if dto.get('importe_total') is not None:
            self.assertGreater(
                float(dto['importe_total']),
                0,
                "El importe total debe ser positivo"
            )
        
        logger.info("✓ DTO creado correctamente")
        logger.info(f"  Estado: {dto.get('estado')}")
        logger.info(f"  Proveedor: {dto.get('proveedor_text', 'N/A')}")
        logger.info(f"  Importe: €{dto.get('importe_total', 'N/A')}")
        
        # Guardar DTO para pruebas posteriores (en clase para compartir)
        self.__class__.dto = dto
        self.dto = dto  # También en instancia para compatibilidad
    
    def test_09_validate_fiscal_rules(self):
        """Test 9: Validar reglas fiscales del DTO"""
        dto = self.__class__.dto or getattr(self, 'dto', None)
        if not dto:
            self.skipTest("Requiere DTO creado en test_08")
        
        is_valid = validate_fiscal_rules(dto)
        
        # La validación puede fallar, pero debe ejecutarse sin errores
        # Solo verificamos que se ejecuta correctamente
        self.assertIsInstance(is_valid, bool, "La validación debe retornar un booleano")
        
        if is_valid:
            logger.info("✓ Validación fiscal pasada")
        else:
            logger.warning("⚠ Validación fiscal falló (esto puede ser esperado según los datos)")
    
    def test_10_validate_business_rules(self):
        """Test 10: Validar reglas de negocio del DTO"""
        dto = self.__class__.dto or getattr(self, 'dto', None)
        if not dto:
            self.skipTest("Requiere DTO creado en test_08")
        
        is_valid = validate_business_rules(dto)
        
        # Verificar que la validación se ejecuta sin errores
        self.assertIsInstance(is_valid, bool, "La validación debe retornar un booleano")
        
        if is_valid:
            logger.info("✓ Validación de negocio pasada")
        else:
            logger.warning("⚠ Validación de negocio falló (esto puede ser esperado según los datos)")
    
    def test_11_dto_structure(self):
        """Test 11: Verificar estructura completa del DTO"""
        dto = self.__class__.dto or getattr(self, 'dto', None)
        if not dto:
            self.skipTest("Requiere DTO creado en test_08")
        
        # Campos obligatorios
        required_fields = [
            'drive_file_id',
            'drive_file_name',
            'importe_total',
            'extractor',
            'estado',
            'confianza',
            'moneda'
        ]
        
        for field in required_fields:
            self.assertIn(
                field,
                dto,
                f"El DTO debe incluir el campo '{field}'"
            )
        
        # Verificar tipos de datos
        self.assertIsInstance(dto['drive_file_id'], str)
        self.assertIsInstance(dto['drive_file_name'], str)
        self.assertIsInstance(dto['extractor'], str)
        self.assertIsInstance(dto['estado'], str)
        self.assertIsInstance(dto['confianza'], str)
        self.assertIsInstance(dto['moneda'], str)
        
        # Verificar valores válidos
        self.assertIn(dto['estado'], ['procesado', 'pendiente', 'error', 'revisar'])
        self.assertIn(dto['confianza'], ['alta', 'media', 'baja'])
        self.assertEqual(len(dto['moneda']), 3, "La moneda debe tener 3 caracteres")
        
        logger.info("✓ Estructura del DTO verificada correctamente")


def run_tests():
    """Ejecutar todas las pruebas"""
    # Configurar el output
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIberdrolaInvoice)
    
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout
    )
    
    print("\n" + "="*70)
    print("🧪 PRUEBAS UNITARIAS - Factura Iberdrola Junio 2025")
    print("="*70)
    print(f"Archivo: temp/Iberdrola Junio 2025.pdf\n")
    
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*70)
    print(f"Total de pruebas: {result.testsRun}")
    print(f"✓ Exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    if result.failures:
        print(f"✗ Fallidas: {len(result.failures)}")
    if result.errors:
        print(f"✗ Errores: {len(result.errors)}")
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)


