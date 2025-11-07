# 🔍 Análisis de Propuesta de Optimización Ollama

## ❌ Problema Identificado en las Pruebas

**Error**: `cannot unpack non-iterable bool object`

**Causa**: Las funciones `validate_fiscal_rules()` y `validate_business_rules()` retornan solo `bool`, no tupla `(bool, str)`. El script de prueba intentaba desempaquetar como tupla.

**Estado**: ✅ **CORREGIDO** - El script ahora maneja correctamente los retornos booleanos.

---

## 📊 Análisis de la Propuesta de Optimización

### ✅ **1. Reducir context window (num_ctx: 2048)**

**Opción**: Excelente ✅

**Razón**:
- Para OCR de facturas no necesitamos tanto contexto
- Reduce memoria de ~7GB → ~4.5GB según la propuesta
- Compatible con nuestra factura JSON que es corta

**Implementación**:
- Añadir a `payload` en `ocr_extractor.py`: `"options": {"num_ctx": 2048}`
- O en `.env`: `OLLAMA_NUM_CTX=2048` (si Ollama lo soporta como env)

**Recomendación**: ✅ **IMPLEMENTAR**

---

### ✅ **2. Limitar threads de CPU (num_thread: 4)**

**Opción**: Muy buena ✅

**Razón**:
- En servidor de 8GB con PostgreSQL y otros servicios corriendo
- Evita saturación del sistema
- Recomendado: `num_thread: 2` o `3` para dejar margen

**Implementación**:
- Añadir a `payload`: `"options": {"num_thread": 2}`
- O verificar con `nproc` cuántos cores tenemos disponibles

**Recomendación**: ✅ **IMPLEMENTAR** (con valor conservador: 2-3 threads)

---

### ⚠️ **3. low_vram y f16_kv en modelo**

**Opción**: Potencialmente útil, pero requiere verificación ⚠️

**Razón**:
- `low_vram: true` y `f16_kv: true` son parámetros de modelo/compilación
- Pueden requerir recrear el modelo o configurar en `Modelfile`
- No todos los parámetros están disponibles en la API `/api/generate`

**Implementación**:
- Verificar si Ollama soporta estos parámetros vía API `options`
- Alternativa: Crear modelo custom con `ollama create` y `Modelfile`

**Recomendación**: ⚠️ **VERIFICAR PRIMERO** si funciona vía API antes de crear modelo custom

---

### ✅ **4. Cuantización 4-bit (Q4_K_M)**

**Opción**: Excelente para reducir memoria ✅

**Razón**:
- Reduce modelo de 4.7GB → ~3.2GB
- Pérdida de precisión mínima para OCR
- Compatible con nuestro caso de uso

**Implementación**:
```bash
# Verificar si existe versión cuantizada
ollama pull llava:7b-q4_K_M

# O crear modelo custom
ollama create llava7b-q4 -f Modelfile
# Modelfile:
# FROM llava:7b
# PARAMETER quantize q4_K_M
```

**Recomendación**: ✅ **IMPLEMENTAR** - Es la optimización más efectiva

---

### ✅ **5. Limitar tokens de salida (num_predict: 200)**

**Opción**: Muy buena ✅

**Razón**:
- Nuestro JSON de salida es corto (~100-150 tokens)
- Evita procesamiento innecesario
- Reduce tiempo de respuesta

**Implementación**:
- Añadir a `payload`: `"options": {"num_predict": 200}`

**Recomendación**: ✅ **IMPLEMENTAR**

---

### ✅ **6. Procesamiento secuencial**

**Opción**: Ya implementado ✅

**Estado**: 
- ✅ El código actual procesa facturas una por una
- ✅ No usa ThreadPoolExecutor concurrente
- ✅ Cada request espera respuesta antes de siguiente

**Recomendación**: ✅ **MANTENER** - Ya está bien implementado

---

### ✅ **7. Monitoreo en tiempo real**

**Opción**: Útil para diagnóstico ✅

**Implementación**:
```bash
# Ver memoria de Ollama
watch -n 2 "ps aux | grep ollama | grep -v grep | awk '{print \$4, \$11}'"

# O con htop
htop
```

**Recomendación**: ✅ **USAR** para monitorear durante pruebas

---

## 🎯 Plan de Implementación Recomendado

### Fase 1: Optimizaciones inmediatas (vía API)

1. ✅ Añadir `num_ctx: 2048` en payload
2. ✅ Añadir `num_thread: 2` en payload  
3. ✅ Añadir `num_predict: 200` en payload

**Impacto esperado**: 
- Memoria: ~7GB → ~4.5GB
- Velocidad: 20-25s → 15-18s por factura

### Fase 2: Optimización de modelo (requiere recrear)

4. ✅ Probar cuantización Q4_K_M (requiere nuevo modelo)

**Impacto esperado**:
- Memoria: ~4.5GB → ~3.2GB
- Velocidad: Similar o ligeramente más lento
- Precisión: Mínima pérdida (aceptable para OCR)

### Fase 3: Verificación avanzada (opcional)

5. ⚠️ Investigar `low_vram` y `f16_kv` vía API o Modelfile

---

## 📝 Parámetros Recomendados para Nuestro Caso

```python
payload = {
    "model": "llava:7b",
    "prompt": prompt,
    "images": [image_base64],
    "format": "json",
    "stream": False,
    "options": {
        "num_ctx": 2048,        # Reducir contexto
        "num_thread": 2,         # Limitar threads (conservador)
        "num_predict": 200,      # Limitar salida
        # "low_vram": True,      # Verificar si funciona
        # "f16_kv": True         # Verificar si funciona
    }
}
```

---

## 🚨 Notas Importantes

1. **num_thread**: Empezar con valor conservador (2). Si el sistema responde bien, podemos aumentar a 3-4.

2. **Cuantización**: Requiere descargar/crear nuevo modelo. Asegurarse de tener espacio en disco.

3. **Validación**: Probar cada cambio individualmente para medir impacto real.

4. **Compatibility**: Algunos parámetros pueden no estar disponibles en todas las versiones de Ollama. Verificar con `ollama --version`.

---

## ✅ Conclusión

**Implementar ahora**:
- ✅ num_ctx: 2048
- ✅ num_thread: 2  
- ✅ num_predict: 200

**Probar después**:
- ✅ Cuantización Q4_K_M
- ⚠️ low_vram / f16_kv (si están disponibles)

**Ya implementado**:
- ✅ Procesamiento secuencial

**Impacto esperado total**: Reducción de memoria de ~7GB → ~3-3.5GB, con mejora en velocidad del 20-30%.



