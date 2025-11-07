# 📋 Resumen Ejecutivo - Plan Arquitectura Híbrida

**Fecha**: 2025-10-30  
**Objetivo**: Migrar a arquitectura híbrida para 100% fiabilidad en números

---

## 🎯 Objetivo Principal

**Problema actual**: Modelo Ollama tiene inconsistencia crítica (6000% variación en importes)  
**Solución**: Arquitectura híbrida donde:
- **Tesseract** extrae números (precisión absoluta)
- **Ollama** extrae texto (comprensión semántica)

**Resultado esperado**: 100% de fiabilidad y consistencia en datos numéricos

---

## 📊 Análisis del Proyecto

### Archivos Críticos Identificados

| Archivo | Tipo Cambio | Impacto | Complejidad |
|---------|-------------|---------|-------------|
| `src/ocr_extractor.py` | **Mayor** | Crítico | Alta |
| `src/pipeline/ingest.py` | Menor | Medio | Baja |
| `src/parser_normalizer.py` | Menor | Medio | Baja |
| `tests/test_iberdrola_invoice.py` | Medio | Medio | Media |
| `tests/test_hybrid_extraction.py` | **Nuevo** | Alto | Media |

### Puntos de Integración

1. **`extract_invoice_data()`** - Método principal a refactorizar
2. **`process_batch()`** - Ajustar lógica de extractor usado
3. **`create_factura_dto()`** - Compatibilidad con nuevos campos
4. **Modelo BD** - Sin cambios necesarios (compatible)

---

## 🔧 Cambios Principales

### 1. Nuevos Métodos en `ocr_extractor.py`

```
_extract_numerical_fields_tesseract()  → Solo números (Tesseract)
_extract_text_fields_ollama()          → Solo texto (Ollama)
_combine_hybrid_results()              → Combinación inteligente
_validate_cross_reference()            → Validación cruzada
```

### 2. Refactorización de `extract_invoice_data()`

**Antes**: Ollama primero → Tesseract fallback  
**Después**: Ambos siempre → Combinación inteligente

### 3. Mejoras en Regex Patterns

- Múltiples patrones para números
- Validación de rangos razonables
- Búsqueda en múltiples ubicaciones del texto

---

## ⏱️ Estimación de Tiempo

| Fase | Descripción | Horas |
|------|-------------|-------|
| 1. Preparación | Diseño y análisis | 4-6h |
| 2. Desarrollo Core | Refactorización principal | 12-16h |
| 3. Validación | Validación cruzada | 6-8h |
| 4. Ajustes Pipeline | Integración | 4-6h |
| 5. Testing | Tests exhaustivos | 8-10h |
| 6. Documentación | Docs y refinamiento | 4-6h |
| **TOTAL** | | **38-52h** |

**Tiempo estimado**: 5-7 días de trabajo a tiempo completo

---

## ✅ Criterios de Éxito

### Funcionales
- ✅ Números extraídos con Tesseract (100% consistencia)
- ✅ Texto extraído con Ollama
- ✅ Sistema funciona aunque un extractor falle
- ✅ Validación cruzada detecta discrepancias

### Técnicos
- ✅ Tests pasan al 100%
- ✅ Sin regresiones
- ✅ Tiempo ≤ 60s por factura
- ✅ Sin problemas de memoria

### Calidad
- ✅ Consistencia: misma factura = mismos resultados
- ✅ Precisión: números correctos
- ✅ Robustez: múltiples formatos

---

## ⚠️ Riesgos Principales

1. **Tesseract no extrae números correctamente**
   - Mitigación: Mejorar regex patterns, múltiples variantes

2. **Tiempo de procesamiento aumenta**
   - Mitigación: Ejecutar en paralelo si es posible

3. **Ollama falla para texto**
   - Mitigación: Fallback robusto a Tesseract

---

## 🔄 Compatibilidad

- ✅ **Sin migración de BD** requerida
- ✅ **Compatibilidad hacia atrás** con datos existentes
- ✅ **Sin reprocesar** facturas antiguas
- ✅ **Nuevas facturas** usan híbrida automáticamente

---

## 📝 Próximos Pasos

1. **Revisar este plan** (este documento)
2. **Revisar plan detallado** (`PLAN_IMPLEMENTACION_ARQUITECTURA_HIBRIDA.md`)
3. **Aprobar o solicitar cambios**
4. **Una vez aprobado**: Comenzar Fase 1

---

## 📎 Documentos Relacionados

- **Plan Detallado**: `PLAN_IMPLEMENTACION_ARQUITECTURA_HIBRIDA.md`
- **Análisis Arquitectura**: `ANALISIS_ARQUITECTURA_HIBRIDA.md`
- **Reporte Stress Test**: `REPORTE_DETALLADO_STRESS_TEST_OLLAMA.md`

---

**¿Listo para revisar el plan detallado y dar el OK para comenzar?**



