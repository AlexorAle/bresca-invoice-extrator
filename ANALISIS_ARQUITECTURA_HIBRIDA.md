# 🔄 Análisis: Migración a Arquitectura Híbrida

**Fecha**: 2025-10-30  
**Modelo actual**: Ollama primario + Tesseract fallback  
**Modelo propuesto**: Arquitectura híbrida (Tesseract números + Ollama texto)

---

## 🎯 ¿Por qué Arquitectura Híbrida es Más Robusta?

### ✅ Ventajas para Facturas de Múltiples Proveedores

1. **Precisión en Números**:
   - Tesseract lee dígitos exactos (OCR tradicional)
   - No depende de "interpretación" del modelo
   - Funciona igual en todos los formatos de factura

2. **Flexibilidad en Texto**:
   - Ollama entiende contexto semántico
   - Maneja variaciones en formato de fechas, nombres
   - Mejor con layouts no estándar

3. **Robustez ante Variabilidad**:
   - Si un proveedor cambia formato, números siguen siendo precisos
   - Texto sigue siendo interpretable aunque cambie ubicación

4. **Escalabilidad**:
   - No requiere entrenar modelo nuevo por cada formato
   - Tesseract funciona universalmente
   - Ollama mejora con experiencia pero no depende de formatos específicos

---

## 📋 Cambios Necesarios en el Código

### 1. Modificar `InvoiceExtractor.extract_invoice_data()`

**Estado Actual**:
```python
def extract_invoice_data(self, pdf_path: str) -> dict:
    # 1. Intentar Ollama primero
    # 2. Si falta importe_total → usar Tesseract como fallback
    # 3. Combinar resultados (priorizar Ollama)
```

**Nuevo Diseño**:
```python
def extract_invoice_data(self, pdf_path: str) -> dict:
    # 1. Ejecutar Tesseract y Ollama en paralelo (o secuencial)
    # 2. Extraer campos específicos de cada uno
    # 3. Combinar inteligentemente:
    #    - Números → Tesseract (con validación)
    #    - Texto → Ollama (con fallback a Tesseract si falla)
    # 4. Validar coherencia final
```

### 2. Crear Métodos Especializados

**Nuevos métodos necesarios**:

```python
def _extract_numerical_fields_tesseract(self, pdf_path: str) -> dict:
    """Extraer solo campos numéricos con Tesseract"""
    # importe_total, base_imponible, impuestos_total, iva_porcentaje
    
def _extract_text_fields_ollama(self, image_base64: str) -> dict:
    """Extraer solo campos de texto con Ollama"""
    # proveedor_text, numero_factura, fecha_emision, moneda
    
def _combine_hybrid_results(self, tesseract_data: dict, ollama_data: dict) -> dict:
    """Combinar resultados de ambos extractores inteligentemente"""
    # Lógica de priorización y validación cruzada
```

### 3. Mejorar Extracción Numérica de Tesseract

**Mejoras necesarias**:

```python
def _extract_importe_total_tesseract(self, text: str) -> Optional[float]:
    """Extracción mejorada de importe total"""
    # Múltiples patrones regex más robustos
    # Buscar en diferentes ubicaciones del documento
    # Validar formato numérico
    
def _extract_base_imponible_tesseract(self, text: str) -> Optional[float]:
    """Extracción de base imponible"""
    
def _extract_impuestos_tesseract(self, text: str) -> Optional[float]:
    """Extracción de impuestos"""
```

### 4. Validación Cruzada

**Nueva funcionalidad**:

```python
def _validate_cross_reference(self, tesseract_data: dict, ollama_data: dict) -> dict:
    """Validar coherencia entre ambos extractores"""
    # Si Tesseract encuentra importe_total y Ollama también:
    #   - Comparar valores (tolerancia de redondeo)
    #   - Usar el más confiable
    # Si hay discrepancia grande → marcar para revisión
```

---

## 🔧 Cambios por Archivo

### `src/ocr_extractor.py`

**Cambios principales**:
1. Refactorizar `extract_invoice_data()` para arquitectura híbrida
2. Crear métodos especializados para campos numéricos y de texto
3. Implementar lógica de combinación inteligente
4. Mejorar regex patterns para números en Tesseract
5. Añadir validación cruzada entre extractores

**Líneas estimadas**: ~200-300 líneas nuevas/modificadas

### `src/parser_normalizer.py`

**Cambios menores**:
1. Ajustar normalización para manejar múltiples fuentes
2. Mejorar validación de coherencia numérica
3. Añadir campo `extractor_source` al DTO (indicar de dónde vino cada campo)

**Líneas estimadas**: ~50-100 líneas modificadas

### Tests

**Nuevos tests necesarios**:
1. Test de extracción híbrida completa
2. Test de combinación de resultados
3. Test de validación cruzada
4. Test con diferentes formatos de factura

**Archivos**: `tests/test_hybrid_extraction.py` (nuevo)

---

## ⏱️ Estimación de Esfuerzo

### Desarrollo

| Tarea | Complejidad | Tiempo Estimado |
|-------|-------------|-----------------|
| Refactorizar `extract_invoice_data()` | Media | 4-6 horas |
| Crear métodos especializados | Media | 3-4 horas |
| Mejorar regex Tesseract | Baja | 2-3 horas |
| Implementar combinación inteligente | Alta | 4-6 horas |
| Validación cruzada | Media | 3-4 horas |
| Tests | Media | 4-5 horas |
| **TOTAL** | | **20-28 horas** |

### Testing y Validación

| Tarea | Tiempo Estimado |
|-------|-----------------|
| Pruebas con facturas reales | 2-3 horas |
| Ajustes y refinamiento | 2-4 horas |
| Documentación | 1-2 horas |
| **TOTAL** | **5-9 horas** |

**Total General**: ~25-37 horas (3-5 días de trabajo)

---

## 📊 Impacto en Rendimiento

### Tiempo de Procesamiento

**Estado Actual**:
- Ollama: ~45-50s por factura
- Tesseract (fallback): ~5s adicionales si es necesario
- **Total**: ~45-55s promedio

**Arquitectura Híbrida**:
- Tesseract: ~5s (siempre se ejecuta)
- Ollama: ~45-50s (siempre se ejecuta)
- Combinación: ~0.1s
- **Total**: ~50-55s promedio

**Impacto**: ⚠️ Similar o ligeramente más lento (5-10s adicionales), pero más confiable

### Memoria

**Sin cambios**: Mismo uso de memoria (Ollama sigue siendo el cuello de botella)

---

## 🎯 Ventajas vs Desventajas

### ✅ Ventajas

1. **Precisión en números**: Elimina variabilidad de 6000%
2. **Robustez**: Funciona con múltiples formatos sin cambios
3. **Confiabilidad**: Resultados reproducibles en campos críticos
4. **Escalabilidad**: No requiere entrenamiento por formato
5. **Mantenibilidad**: Más fácil de depurar (sabes qué extractor falló)

### ⚠️ Desventajas

1. **Complejidad**: Más código para mantener
2. **Tiempo**: Ligeramente más lento (ejecuta ambos siempre)
3. **Lógica de combinación**: Requiere decisiones sobre priorización
4. **Casos edge**: Algunos formatos pueden necesitar ajustes manuales

---

## 🚀 Plan de Implementación Recomendado

### Fase 1: Preparación (1 día)
1. Crear branch `feature/hybrid-architecture`
2. Documentar diseño detallado
3. Crear tests unitarios para métodos nuevos

### Fase 2: Desarrollo Core (2-3 días)
1. Refactorizar `extract_invoice_data()`
2. Crear métodos especializados
3. Implementar combinación básica

### Fase 3: Mejoras (1 día)
1. Mejorar regex patterns
2. Implementar validación cruzada
3. Ajustar lógica de confianza

### Fase 4: Testing (1 día)
1. Probar con facturas reales de diferentes proveedores
2. Validar precisión vs versión actual
3. Ajustar según resultados

### Fase 5: Migración (0.5 días)
1. Merge a main
2. Actualizar documentación
3. Deploy y monitoreo

**Total**: ~5-6 días de trabajo

---

## 🔄 Alternativa: Implementación Gradual

Si prefieres reducir riesgo, puedes implementar gradualmente:

### Paso 1: Añadir determinismo a Ollama (1 hora)
- Añadir `temperature=0`, `top_p=1`, `seed` fijo
- Ver si mejora consistencia
- Si mejora suficiente → mantener arquitectura actual

### Paso 2: Mejorar Tesseract (medio día)
- Mejorar regex patterns para números
- Añadir validación de coherencia
- Usar Tesseract solo para números si Ollama falla

### Paso 3: Arquitectura híbrida completa (si necesario)
- Solo si pasos anteriores no son suficientes

---

## 💡 Recomendación Final

**Para tu caso** (muchas facturas, múltiples proveedores, diferentes formatos):

✅ **SÍ, arquitectura híbrida es la mejor opción a largo plazo**

**Razones**:
1. El problema de inconsistencia es crítico (6000% variación)
2. Tendrás múltiples formatos → necesitas robustez
3. Los números son críticos → precisión es esencial
4. La inversión de tiempo (5-6 días) vale la pena para estabilidad a largo plazo

**Implementación sugerida**:
- Empezar con Paso 1 (determinismo) como quick win
- Si no resuelve completamente → avanzar a arquitectura híbrida
- Considerar Paso 2 como solución intermedia si híbrida completa es demasiado

---

## 📎 Archivos que Necesitarán Cambios

```
src/
├── ocr_extractor.py          ← CAMBIOS MAYORES
├── parser_normalizer.py      ← CAMBIOS MENORES
└── pdf_utils.py              ← Sin cambios

tests/
├── test_iberdrola_invoice.py ← Actualizar tests existentes
└── test_hybrid_extraction.py ← NUEVO
```

---

**¿Quieres que proceda con la implementación o prefieres empezar con determinismo primero?**



