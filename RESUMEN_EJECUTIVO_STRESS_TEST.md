# 📋 Resumen Ejecutivo - Prueba de Stress Ollama llava:7b

**Para**: ChatGPT  
**Fecha**: 2025-10-30  
**Versión Ollama**: 0.12.6  
**Modelo**: llava:7b (Q4_0, 4.7 GB)

---

## 🎯 Objetivo

Evaluar consistencia del modelo `llava:7b` procesando la misma factura PDF 10 veces para identificar problemas de estabilidad y precisión.

---

## ✅ Resultados Principales

### Éxito Técnico
- ✅ **10/10 iteraciones exitosas** (100%)
- ✅ **Tiempo promedio**: 46.5s (rango: 41.9s - 52.0s)
- ✅ **Sin errores de memoria o timeouts**
- ✅ **Optimizaciones funcionando**: num_ctx: 2048, num_thread: 2, num_predict: 200

### Problema Crítico Detectado
- ❌ **INCONSISTENCIA EXTREMA**: 10 valores distintos de importe_total para la misma factura
- ❌ **Rango**: €5.05 - €300.93 (variación de **6000%**)
- ❌ **Sin patrón**: Valores aleatorios, no reproducibles

---

## 📊 Datos Clave

### Importes Extraídos (10 iteraciones)
```
€5.05, €6.05, €7.94, €8.45, €10.0, €23.46, €43.76, €83.9, €235.0, €300.93
```

### Estadísticas
- **Media**: €72.75
- **Mediana**: €9.45
- **Desviación estándar**: €108.23
- **Coeficiente de variación**: 148.8%

### Confianza del Modelo
- **Alta**: 70% (7 iteraciones)
- **Media**: 20% (2 iteraciones)
- **Baja**: 10% (1 iteración)

---

## ⚠️ Problemas Identificados

1. **Inconsistencia del Modelo** (CRÍTICO)
   - Mismo input produce outputs muy diferentes
   - Variación de 6000% en importes
   - Modelo no confiable sin mitigaciones

2. **Variabilidad en Confianza** (MEDIO)
   - Mismo archivo produce diferentes niveles de confianza
   - Puede llevar a decisiones incorrectas

---

## 💡 Recomendaciones

### Inmediatas
1. Implementar sistema de consenso (procesar 3-5 veces, usar mediana)
2. Añadir validación de consistencia (marcar para revisión si variabilidad > 20%)
3. Mejorar prompt con ejemplos y restricciones

### Mediano Plazo
4. Evaluar modelos alternativos especializados en OCR
5. Ajustar parámetros de sampling (temperature, top_p, seed)
6. Implementar cache de resultados

### Largo Plazo
7. Fine-tuning con dataset de facturas reales
8. Arquitectura híbrida (Tesseract para números + Ollama para texto)
9. Monitoreo y alertas de calidad

---

## 📎 Archivos

- **Reporte completo**: `REPORTE_DETALLADO_STRESS_TEST_OLLAMA.md`
- **Datos JSON**: `resultados_stress_test_20251030_181027.json`
- **Script de prueba**: `test_stress_modelo.py`

---

**Conclusión**: El modelo funciona técnicamente pero tiene **inconsistencia crítica** que requiere mitigaciones antes de producción.



