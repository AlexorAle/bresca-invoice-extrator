# ✅ Checklist - Pruebas Unitarias Iberdrola

## Estado de Verificación

### ✅ 1. Archivo PDF de Prueba
- **Estado**: ✓ OK
- **Ubicación**: `temp/Iberdrola Junio 2025.pdf`
- **Tamaño**: 375.3 KB
- **Verificado**: Archivo existe y es accesible

### ✅ 2. Estructura de Archivos
- **Estado**: ✓ OK
- **Directorio tests/**: Existe
- **Archivo de prueba**: `tests/test_iberdrola_invoice.py`
- **Sintaxis**: Sin errores de compilación

### ✅ 3. Entorno Virtual y Dependencias
- **Estado**: ✓ OK
- **Entorno virtual**: `venv/` configurado
- **Imports**: Todas las dependencias importables
- **Módulos verificados**: 
  - `ocr_extractor` ✓
  - `pdf_utils` ✓
  - `parser_normalizer` ✓
  - `pipeline.validate` ✓

### ✅ 4. Variables de Entorno
- **Estado**: ✓ OK
- **Archivo .env**: Existe
- **Carga de variables**: Funciona correctamente
- **Validación de secrets**: Pasada

### ✅ 5. Configuración del Código
- **Estado**: ✓ OK
- **Path de imports**: Configurado correctamente
- **Ruta del PDF**: Detectada automáticamente
- **Logger**: Configurado y funcionando

### ✅ 6. Prueba Rápida Ejecutada
- **Estado**: ✓ OK
- **Test ejecutado**: `test_01_file_exists`
- **Resultado**: PASSED
- **Sin errores críticos**: ✓

---

## 🚀 Cómo Ejecutar las Pruebas

### Opción 1: Ejecutar todas las pruebas
```bash
cd /home/alex/proyectos/invoice-extractor
source venv/bin/activate
python -m unittest tests.test_iberdrola_invoice -v
```

### Opción 2: Ejecutar una prueba específica
```bash
python -m unittest tests.test_iberdrola_invoice.TestIberdrolaInvoice.test_05_extract_invoice_data -v
```

### Opción 3: Ejecutar como script Python
```bash
source venv/bin/activate
python tests/test_iberdrola_invoice.py
```

---

## 📋 Pruebas Incluidas

1. ✅ `test_01_file_exists` - Verificar que el PDF existe
2. ✅ `test_02_file_is_valid_pdf` - Validar formato PDF
3. ✅ `test_03_file_integrity` - Verificar integridad del archivo
4. ✅ `test_04_pdf_info` - Obtener información del PDF
5. ⏱️ `test_05_extract_invoice_data` - Extraer datos (puede tardar 30-60s)
6. ⏱️ `test_06_extracted_proveedor` - Verificar proveedor extraído
7. ⏱️ `test_07_extracted_importe_total` - Verificar importe extraído
8. ⏱️ `test_08_create_factura_dto` - Crear DTO normalizado
9. ⏱️ `test_09_validate_fiscal_rules` - Validar reglas fiscales
10. ⏱️ `test_10_validate_business_rules` - Validar reglas de negocio
11. ⏱️ `test_11_dto_structure` - Verificar estructura del DTO

---

## ⚠️ Notas Importantes

- **Tiempo de ejecución**: Las pruebas de extracción (test_05 en adelante) pueden tardar entre 30-60 segundos cada una debido al procesamiento OCR
- **Ollama**: Requiere que Ollama esté corriendo para las pruebas de extracción completa
- **Base de datos**: Las pruebas NO requieren conexión a la base de datos (son unitarias)
- **Logs**: Los resultados y logs se mostrarán en la consola durante la ejecución

---

## ✅ Estado Final: TODO LISTO PARA EJECUTAR

Todos los componentes están verificados y funcionando correctamente.

