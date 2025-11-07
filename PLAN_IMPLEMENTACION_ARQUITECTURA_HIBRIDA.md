# 📋 Plan de Implementación - Arquitectura Híbrida OCR

**Fecha**: 2025-10-30  
**Objetivo**: Migrar de arquitectura Ollama-primario a Arquitectura Híbrida (Tesseract números + Ollama texto)  
**Meta**: 100% de fiabilidad en extracción de datos numéricos

---

## 📊 Análisis Completo del Proyecto

### Estructura Actual del Sistema

```
invoice-extractor/
├── src/
│   ├── main.py                    # Punto de entrada principal
│   ├── ocr_extractor.py          # ⚠️ MÓDULO PRINCIPAL A REFACTORIZAR
│   ├── parser_normalizer.py      # Normalización y creación de DTO
│   ├── pdf_utils.py              # Utilidades PDF (sin cambios)
│   ├── drive_client.py           # Cliente Google Drive (sin cambios)
│   ├── db/
│   │   ├── models.py             # Modelos SQLAlchemy
│   │   ├── repositories.py       # Repositorios DB
│   │   └── database.py           # Conexión DB
│   ├── pipeline/
│   │   ├── ingest.py             # ⚠️ PROCESAMIENTO BATCH (ajustes menores)
│   │   └── validate.py           # Validaciones (sin cambios)
│   └── security/
│       └── secrets.py            # Gestión de secrets (sin cambios)
├── tests/
│   └── test_iberdrola_invoice.py # ⚠️ TESTS A ACTUALIZAR
└── scripts/
    └── test_connection.py         # Scripts de prueba
```

### Flujo Actual de Procesamiento

```
1. main.py → InvoiceProcessor.__init__()
   └── Crea InvoiceExtractor()

2. main.py → InvoiceProcessor.run()
   └── Descarga PDFs de Google Drive
   └── Llama a pipeline.ingest.process_batch()

3. pipeline.ingest.process_batch()
   └── Para cada archivo:
       ├── extractor.extract_invoice_data(pdf_path)
       │   └── ⚠️ AQUÍ SE HACE LA EXTRACCIÓN ACTUAL
       │       ├── Intenta Ollama primero
       │       └── Si falta importe_total → Tesseract fallback
       │
       ├── Determina extractor usado (línea 74)
       ├── Crea metadata con extractor
       ├── parser_normalizer.create_factura_dto()
       ├── Valida reglas de negocio
       └── Guarda en BD

4. parser_normalizer.create_factura_dto()
   └── Normaliza datos
   └── Valida reglas fiscales
   └── Crea DTO con campo 'extractor' (línea 237)
```

### Campos Extraídos Actualmente

**Desde OCR (raw_data)**:
- `proveedor_text`: Texto
- `numero_factura`: Texto  
- `fecha_emision`: Fecha (string)
- `moneda`: Texto (3 chars)
- `base_imponible`: **Número** ⚠️
- `impuestos_total`: **Número** ⚠️
- `iva_porcentaje`: **Número** ⚠️
- `importe_total`: **Número** ⚠️ (CRÍTICO)
- `confianza`: 'alta'|'media'|'baja'

**Almacenado en BD (Factura model)**:
- Campo `extractor`: Texto ('ollama' o 'tesseract')
- Campo `confianza`: Texto ('alta'|'media'|'baja')
- Todos los campos numéricos como DECIMAL(18,2)

### Puntos de Integración Críticos

1. **`ocr_extractor.py:extract_invoice_data()`** (línea 248)
   - **Cambio mayor**: Refactorizar para arquitectura híbrida
   - Retorna `dict` con datos extraídos
   - Usado por: `pipeline.ingest.process_batch()` (línea 71)

2. **`pipeline.ingest.py:process_batch()`** (línea 74)
   - **Cambio menor**: Ajustar lógica de determinación de extractor
   - Actualmente: `extractor_used = 'ollama' if confianza in ['alta','media'] else 'tesseract'`
   - Nuevo: `extractor_used = 'hybrid'` (o mantener 'ollama'/'tesseract' con nueva lógica)

3. **`parser_normalizer.py:create_factura_dto()`** (línea 237)
   - **Cambio menor**: Campo `extractor` puede necesitar valores nuevos
   - Actualmente acepta: 'ollama', 'tesseract', 'unknown'
   - Nuevo: Puede necesitar 'hybrid' o tracking más granular

4. **`db.models.py:Factura.extractor`** (línea 50)
   - **Sin cambios necesarios**: Columna Text acepta cualquier valor
   - Pero puede querer añadir constraint o migración para valores válidos

5. **Tests** (`test_iberdrola_invoice.py`)
   - **Cambios necesarios**: Actualizar para nueva arquitectura
   - Asegurar que campos numéricos vienen de Tesseract

---

## 🎯 Diseño de Arquitectura Híbrida

### Principio de Funcionamiento

```
┌─────────────────────────────────────────────────────────┐
│  extract_invoice_data(pdf_path)                         │
└─────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐      ┌───────────────┐
│  TESSERACT    │      │    OLLAMA     │
│  (Números)    │      │   (Texto)     │
└───────────────┘      └───────────────┘
        │                       │
        │                       │
        ▼                       ▼
┌───────────────────────────────────────┐
│  COMBINACIÓN INTELIGENTE              │
│  - Números → Tesseract                │
│  - Texto → Ollama                     │
│  - Validación cruzada                 │
│  - Priorización si conflicto          │
└───────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  Resultado Final      │
         │  (raw_data dict)      │
         └──────────────────────┘
```

### Asignación de Campos por Extractor

| Campo | Extractor Principal | Extractor Fallback | Prioridad |
|-------|---------------------|-------------------|-----------|
| `importe_total` | **Tesseract** | Ollama (validación) | Crítica - Tesseract |
| `base_imponible` | **Tesseract** | Ollama (validación) | Crítica - Tesseract |
| `impuestos_total` | **Tesseract** | Ollama (validación) | Crítica - Tesseract |
| `iva_porcentaje` | **Tesseract** | Ollama (validación) | Crítica - Tesseract |
| `proveedor_text` | **Ollama** | Tesseract (regex) | Media - Ollama |
| `numero_factura` | **Ollama** | Tesseract (regex) | Media - Ollama |
| `fecha_emision` | **Ollama** | Tesseract (regex) | Media - Ollama |
| `moneda` | **Ollama** | Tesseract (regex) | Media - Ollama |

### Estructura de Datos de Retorno

```python
{
    # Campos numéricos (de Tesseract)
    'importe_total': float,          # ✅ SIEMPRE de Tesseract
    'base_imponible': float,         # ✅ SIEMPRE de Tesseract
    'impuestos_total': float,         # ✅ SIEMPRE de Tesseract
    'iva_porcentaje': float,         # ✅ SIEMPRE de Tesseract
    
    # Campos de texto (de Ollama)
    'proveedor_text': str,           # ✅ SIEMPRE de Ollama
    'numero_factura': str,           # ✅ SIEMPRE de Ollama
    'fecha_emision': str,            # ✅ SIEMPRE de Ollama
    'moneda': str,                   # ✅ SIEMPRE de Ollama
    
    # Metadatos de extracción
    'confianza': 'alta'|'media'|'baja',
    'extractor_numeros': 'tesseract',
    'extractor_texto': 'ollama',
    'extractor_used': 'hybrid',
    
    # Opcional: tracking de fuentes
    'fuentes': {
        'numeros': 'tesseract',
        'texto': 'ollama',
        'validacion_cruzada': True/False
    }
}
```

---

## 🔧 Plan de Implementación Detallado

### FASE 1: Preparación y Diseño (4-6 horas)

#### 1.1 Crear Branch y Estructura Base
- [ ] Crear branch `feature/hybrid-architecture`
- [ ] Crear documento de diseño técnico detallado
- [ ] Revisar y documentar casos edge
- [ ] Crear tests unitarios base (TDD approach)

**Archivos nuevos**:
- `docs/arquitectura_hibrida_diseno.md`

#### 1.2 Análisis de Regex Patterns Actuales
- [ ] Revisar regex patterns de Tesseract actuales
- [ ] Identificar mejoras necesarias para números
- [ ] Documentar patrones comunes en facturas españolas

**Archivos a revisar**:
- `src/ocr_extractor.py` (líneas 214-232)

#### 1.3 Definir Estructura de Datos
- [ ] Documentar estructura exacta de retorno
- [ ] Definir cómo manejar casos donde un extractor falla
- [ ] Definir estrategia de validación cruzada

---

### FASE 2: Desarrollo Core - Refactorización (12-16 horas)

#### 2.1 Crear Métodos Especializados de Extracción

**Archivo**: `src/ocr_extractor.py`

**Nuevos métodos**:

```python
def _extract_numerical_fields_tesseract(self, pdf_path: str) -> dict:
    """
    Extraer SOLO campos numéricos con Tesseract
    
    Returns:
        dict con: importe_total, base_imponible, impuestos_total, iva_porcentaje
    """
    # Implementación mejorada de regex para números
    # Múltiples patrones robustos
    # Validación de formato numérico
    
def _extract_text_fields_ollama(self, image_base64: str) -> dict:
    """
    Extraer SOLO campos de texto con Ollama
    
    Returns:
        dict con: proveedor_text, numero_factura, fecha_emision, moneda
    """
    # Prompt modificado para solo campos de texto
    # Sin campos numéricos en el prompt
    
def _combine_hybrid_results(
    self, 
    tesseract_data: dict, 
    ollama_data: dict
) -> dict:
    """
    Combinar resultados de ambos extractores
    
    Returns:
        dict combinado con validación cruzada
    """
    # Lógica de combinación
    # Validación cruzada si ambos tienen el mismo campo
    # Priorización según reglas
```

**Tareas**:
- [ ] Implementar `_extract_numerical_fields_tesseract()`
- [ ] Mejorar regex patterns para números (múltiples patrones)
- [ ] Implementar `_extract_text_fields_ollama()`
- [ ] Modificar prompt de Ollama (eliminar campos numéricos)
- [ ] Implementar `_combine_hybrid_results()`
- [ ] Añadir validación cruzada

**Estimación**: 8-10 horas

#### 2.2 Refactorizar Método Principal

**Archivo**: `src/ocr_extractor.py`

**Método a refactorizar**: `extract_invoice_data()` (línea 248)

**Nueva implementación**:

```python
def extract_invoice_data(self, pdf_path: str) -> dict:
    """
    Extraer datos usando arquitectura híbrida
    
    Estrategia:
    1. Ejecutar Tesseract y Ollama (ambos siempre)
    2. Extraer campos específicos de cada uno
    3. Combinar resultados
    4. Validar coherencia
    """
    try:
        logger.info(f"Iniciando extracción híbrida de: {pdf_path}")
        
        # Preparar imagen para ambos extractores
        img_base64 = pdf_to_base64(pdf_path, page=1, dpi=200)
        
        if img_base64 is None:
            logger.warning("No se pudo convertir PDF, usando solo Tesseract")
            tesseract_data = self._extract_numerical_fields_tesseract(pdf_path)
            text_data = self._extract_text_fields_tesseract_fallback(pdf_path)
            return self._combine_hybrid_results(tesseract_data, text_data)
        
        # Ejecutar ambos extractores
        # (Pueden ejecutarse en paralelo si se usa threading, pero 
        #  para simplicidad inicial: secuencial)
        
        tesseract_data = self._extract_numerical_fields_tesseract(pdf_path)
        
        try:
            ollama_data = self._extract_text_fields_ollama(img_base64)
        except Exception as ollama_error:
            logger.warning(f"Ollama falló: {ollama_error}, usando Tesseract para texto")
            ollama_data = self._extract_text_fields_tesseract_fallback(pdf_path)
        
        # Combinar resultados
        combined = self._combine_hybrid_results(tesseract_data, ollama_data)
        
        # Marcar como híbrido
        combined['extractor_used'] = 'hybrid'
        combined['extractor_numeros'] = 'tesseract'
        combined['extractor_texto'] = 'ollama' if ollama_data else 'tesseract'
        
        return combined
        
    except Exception as e:
        logger.error(f"Error en extracción híbrida: {e}")
        return self._empty_result()
```

**Tareas**:
- [ ] Refactorizar `extract_invoice_data()`
- [ ] Añadir método `_extract_text_fields_tesseract_fallback()` para cuando Ollama falla
- [ ] Manejar errores de cada extractor independientemente
- [ ] Añadir logging detallado

**Estimación**: 4-6 horas

#### 2.3 Mejorar Regex Patterns para Números

**Archivo**: `src/ocr_extractor.py`

**Mejoras necesarias**:

```python
def _extract_importe_total_tesseract(self, text: str) -> Optional[float]:
    """
    Extracción mejorada y robusta de importe total
    """
    patterns = [
        # Patrón principal: "Total" seguido de número
        r'(?:Total|TOTAL|Importe\s+Total|Amount\s+Total)[:\s]*€?\s*(\d+[.,]\d{2})',
        
        # Patrón alternativo: "Total" al final de línea
        r'Total[:\s]*€?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
        
        # Patrón: Solo número grande al final
        r'€\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*$',
        
        # Patrón: Buscar en múltiples ubicaciones del texto
        # (buscar en últimas líneas donde suele estar el total)
    ]
    
    # Intentar cada patrón
    # Validar que el número tiene sentido (no muy pequeño/grande)
    # Retornar el más probable
```

**Tareas**:
- [ ] Mejorar `_extract_importe_total_tesseract()`
- [ ] Crear `_extract_base_imponible_tesseract()`
- [ ] Crear `_extract_impuestos_tesseract()`
- [ ] Crear `_extract_iva_porcentaje_tesseract()`
- [ ] Añadir validación de rangos razonables

**Estimación**: 3-4 horas

---

### FASE 3: Validación Cruzada y Lógica de Combinación (6-8 horas)

#### 3.1 Implementar Validación Cruzada

**Archivo**: `src/ocr_extractor.py`

**Nuevo método**:

```python
def _validate_cross_reference(
    self, 
    tesseract_data: dict, 
    ollama_data: dict
) -> dict:
    """
    Validar coherencia entre ambos extractores
    
    Si ambos extrajeron el mismo campo:
    - Comparar valores
    - Si hay discrepancia grande → marcar para revisión
    - Si discrepancia pequeña → usar Tesseract (más confiable para números)
    """
    warnings = []
    
    # Validar importe_total si ambos lo tienen
    if tesseract_data.get('importe_total') and ollama_data.get('importe_total'):
        tess_val = tesseract_data['importe_total']
        ollama_val = ollama_data['importe_total']
        
        diferencia = abs(tess_val - ollama_val)
        diferencia_porcentual = (diferencia / max(tess_val, ollama_val)) * 100
        
        if diferencia_porcentual > 5:  # Más del 5% de diferencia
            warnings.append({
                'campo': 'importe_total',
                'tesseract': tess_val,
                'ollama': ollama_val,
                'diferencia': diferencia_porcentual,
                'accion': 'revisar'
            })
    
    return {
        'warnings': warnings,
        'coherente': len(warnings) == 0
    }
```

**Tareas**:
- [ ] Implementar `_validate_cross_reference()`
- [ ] Definir umbrales de tolerancia
- [ ] Añadir logging de discrepancias

**Estimación**: 2-3 horas

#### 3.2 Mejorar Lógica de Combinación

**Archivo**: `src/ocr_extractor.py`

**Mejoras a `_combine_hybrid_results()`**:

```python
def _combine_hybrid_results(
    self, 
    tesseract_data: dict, 
    ollama_data: dict
) -> dict:
    """
    Combinar resultados con lógica inteligente
    """
    combined = {}
    
    # Números: SIEMPRE de Tesseract (prioridad absoluta)
    for campo in ['importe_total', 'base_imponible', 'impuestos_total', 'iva_porcentaje']:
        combined[campo] = tesseract_data.get(campo)
    
    # Texto: Priorizar Ollama, fallback a Tesseract
    for campo in ['proveedor_text', 'numero_factura', 'fecha_emision', 'moneda']:
        combined[campo] = ollama_data.get(campo) or tesseract_data.get(campo)
    
    # Validación cruzada
    validation = self._validate_cross_reference(tesseract_data, ollama_data)
    
    # Determinar confianza global
    if validation['coherente']:
        confianza = 'alta'
    elif len(validation['warnings']) <= 1:
        confianza = 'media'
    else:
        confianza = 'baja'
    
    combined['confianza'] = confianza
    combined['validacion_cruzada'] = validation
    
    return combined
```

**Tareas**:
- [ ] Implementar lógica de combinación mejorada
- [ ] Añadir métricas de confianza
- [ ] Manejar casos donde un extractor falla completamente

**Estimación**: 3-4 horas

---

### FASE 4: Ajustes en Pipeline y Normalización (4-6 horas)

#### 4.1 Actualizar `pipeline.ingest.py`

**Archivo**: `src/pipeline/ingest.py`

**Cambios necesarios** (línea 74):

```python
# ANTES:
extractor_used = 'ollama' if raw_data.get('confianza') in ['alta', 'media'] else 'tesseract'

# DESPUÉS:
extractor_used = raw_data.get('extractor_used', 'hybrid')
# O mantener lógica simple:
if raw_data.get('extractor_used') == 'hybrid':
    extractor_used = 'hybrid'
elif raw_data.get('confianza') in ['alta', 'media']:
    extractor_used = 'ollama'
else:
    extractor_used = 'tesseract'
```

**Tareas**:
- [ ] Actualizar lógica de determinación de extractor
- [ ] Añadir logging específico para arquitectura híbrida
- [ ] Actualizar eventos de auditoría si es necesario

**Estimación**: 1-2 horas

#### 4.2 Actualizar `parser_normalizer.py`

**Archivo**: `src/parser_normalizer.py`

**Cambios necesarios** (línea 237):

```python
# Campo extractor puede tener nuevos valores:
# 'hybrid', 'tesseract', 'ollama', 'unknown'

# Opcional: Añadir tracking más granular
if metadata.get('extractor_numeros') and metadata.get('extractor_texto'):
    dto['extractor'] = 'hybrid'
    dto['extractor_numeros'] = metadata.get('extractor_numeros')
    dto['extractor_texto'] = metadata.get('extractor_texto')
else:
    dto['extractor'] = metadata.get('extractor', 'unknown')
```

**Tareas**:
- [ ] Actualizar creación de DTO para nuevos campos
- [ ] Asegurar compatibilidad con datos existentes
- [ ] Considerar almacenar tracking granular en `metadatos_json`

**Estimación**: 2-3 horas

#### 4.3 Actualizar Modelo de BD (Opcional)

**Archivo**: `src/db/models.py`

**Consideraciones**:
- Campo `extractor` es `Text`, acepta cualquier valor ✅
- No requiere migración de BD
- Opcional: Añadir constraint para valores válidos

**Tareas**:
- [ ] Decidir si añadir constraint o validación en código
- [ ] Si se añade constraint: crear migración

**Estimación**: 1 hora (si se hace)

---

### FASE 5: Testing Exhaustivo (8-10 horas)

#### 5.1 Actualizar Tests Existentes

**Archivo**: `tests/test_iberdrola_invoice.py`

**Cambios necesarios**:
- [ ] Actualizar `test_05_extract_invoice_data()` para verificar arquitectura híbrida
- [ ] Verificar que números vienen de Tesseract
- [ ] Verificar que texto viene de Ollama
- [ ] Añadir test de validación cruzada

**Estimación**: 2-3 horas

#### 5.2 Crear Tests Nuevos

**Archivo nuevo**: `tests/test_hybrid_extraction.py`

**Tests a crear**:
- [ ] `test_extract_numerical_fields_tesseract()` - Verificar extracción numérica
- [ ] `test_extract_text_fields_ollama()` - Verificar extracción de texto
- [ ] `test_combine_hybrid_results()` - Verificar combinación
- [ ] `test_validate_cross_reference()` - Verificar validación cruzada
- [ ] `test_hybrid_fallback_when_ollama_fails()` - Caso de fallo
- [ ] `test_hybrid_fallback_when_tesseract_fails()` - Caso de fallo
- [ ] `test_stress_hybrid_consistency()` - Prueba de consistencia (10 iteraciones)

**Estimación**: 4-5 horas

#### 5.3 Pruebas con Facturas Reales

**Tareas**:
- [ ] Probar con factura de Iberdrola (ya disponible)
- [ ] Probar con diferentes formatos de factura (si disponibles)
- [ ] Verificar consistencia en múltiples ejecuciones
- [ ] Comparar resultados antes/después

**Estimación**: 2 horas

---

### FASE 6: Documentación y Refinamiento (4-6 horas)

#### 6.1 Documentación Técnica

**Archivos a crear/actualizar**:
- [ ] `docs/arquitectura_hibrida.md` - Documentación completa
- [ ] Actualizar `README.md` con nueva arquitectura
- [ ] Actualizar `docs/developer.md` si es necesario

**Estimación**: 2-3 horas

#### 6.2 Refinamiento y Optimización

**Tareas**:
- [ ] Revisar y optimizar regex patterns según resultados
- [ ] Ajustar umbrales de validación cruzada
- [ ] Optimizar logging para debugging
- [ ] Revisar manejo de errores

**Estimación**: 2-3 horas

---

## 📊 Resumen de Esfuerzo

| Fase | Tareas | Horas Estimadas | Prioridad |
|------|--------|-----------------|-----------|
| **Fase 1: Preparación** | Diseño, análisis | 4-6h | Alta |
| **Fase 2: Desarrollo Core** | Refactorización principal | 12-16h | Crítica |
| **Fase 3: Validación** | Validación cruzada | 6-8h | Alta |
| **Fase 4: Ajustes Pipeline** | Integración | 4-6h | Media |
| **Fase 5: Testing** | Tests exhaustivos | 8-10h | Crítica |
| **Fase 6: Documentación** | Docs y refinamiento | 4-6h | Media |
| **TOTAL** | | **38-52 horas** | |

**Estimación total**: ~5-7 días de trabajo a tiempo completo

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Tesseract no extrae números correctamente
**Probabilidad**: Media  
**Impacto**: Alto  
**Mitigación**: 
- Mejorar regex patterns con múltiples variantes
- Probar con facturas reales antes de deploy
- Mantener fallback a Ollama si Tesseract falla completamente

### Riesgo 2: Ollama falla para texto y no hay fallback robusto
**Probabilidad**: Baja  
**Impacto**: Medio  
**Mitigación**: 
- Implementar `_extract_text_fields_tesseract_fallback()` robusto
- Asegurar que sistema funciona aunque Ollama falle

### Riesgo 3: Tiempo de procesamiento aumenta significativamente
**Probabilidad**: Media  
**Impacto**: Medio  
**Mitigación**: 
- Ejecutar en paralelo si es posible (threading)
- Optimizar regex patterns para velocidad
- Monitorear tiempos en pruebas

### Riesgo 4: Incompatibilidad con datos existentes
**Probabilidad**: Baja  
**Impacto**: Bajo  
**Mitigación**: 
- Mantener compatibilidad en estructura de datos
- Campo `extractor` acepta nuevos valores sin migración

---

## ✅ Criterios de Éxito

### Funcionales
- [ ] Todos los campos numéricos extraídos con Tesseract
- [ ] Todos los campos de texto extraídos con Ollama
- [ ] Sistema funciona aunque un extractor falle
- [ ] Validación cruzada detecta discrepancias

### Técnicos
- [ ] Tests pasan al 100%
- [ ] Sin regresiones en funcionalidad existente
- [ ] Tiempo de procesamiento ≤ 60s por factura
- [ ] Sin errores de memoria o recursos

### Calidad
- [ ] Consistencia: misma factura produce mismos resultados
- [ ] Precisión: números extraídos son correctos
- [ ] Robustez: maneja diferentes formatos de factura

---

## 🚀 Plan de Rollout

### Paso 1: Desarrollo en Branch
- Trabajar en `feature/hybrid-architecture`
- Commits frecuentes con mensajes descriptivos
- Pull requests internos para revisión de código

### Paso 2: Testing Local
- Ejecutar todos los tests
- Probar con facturas reales
- Validar métricas de rendimiento

### Paso 3: Testing en Staging (si existe)
- Deploy a ambiente de prueba
- Procesar batch pequeño de facturas reales
- Monitorear resultados

### Paso 4: Merge a Main
- Code review completo
- Merge cuando todos los criterios de éxito se cumplan
- Tag de versión

### Paso 5: Deploy a Producción
- Deploy gradual si es posible
- Monitoreo intensivo primeras 24h
- Rollback plan preparado

---

## 📝 Checklist de Implementación

### Pre-Implementación
- [ ] Revisar y aprobar este plan
- [ ] Crear branch de desarrollo
- [ ] Backup de código actual
- [ ] Preparar ambiente de pruebas

### Durante Implementación
- [ ] Seguir plan fase por fase
- [ ] Commits frecuentes y descriptivos
- [ ] Tests después de cada fase
- [ ] Documentar decisiones técnicas

### Post-Implementación
- [ ] Ejecutar suite completa de tests
- [ ] Pruebas con facturas reales
- [ ] Validar métricas de rendimiento
- [ ] Actualizar documentación
- [ ] Code review final

---

## 📎 Archivos que Serán Modificados

### Cambios Mayores
- `src/ocr_extractor.py` - Refactorización completa

### Cambios Menores
- `src/pipeline/ingest.py` - Ajuste lógica extractor
- `src/parser_normalizer.py` - Ajuste creación DTO

### Archivos Nuevos
- `tests/test_hybrid_extraction.py` - Tests nuevos
- `docs/arquitectura_hibrida.md` - Documentación

### Sin Cambios
- `src/main.py`
- `src/db/models.py` (posible migración opcional)
- `src/pdf_utils.py`
- `src/drive_client.py`
- `src/pipeline/validate.py`

---

## 🔄 Compatibilidad con Sistema Actual

### Compatibilidad Hacia Atrás
- ✅ Estructura de datos de retorno compatible
- ✅ Campo `extractor` acepta nuevos valores sin migración
- ✅ Pipeline existente funciona sin cambios mayores
- ✅ Tests existentes pueden actualizarse gradualmente

### Migración de Datos
- ❌ No requiere migración de BD
- ❌ No requiere reprocesar facturas existentes
- ✅ Nuevas facturas usarán arquitectura híbrida automáticamente

---

**Fin del Plan**

*Este documento debe ser revisado y aprobado antes de comenzar la implementación.*



