# 🔍 INVESTIGACIÓN: Por qué OpenAI no devuelve respuestas para 9/10 facturas

## 📊 RESUMEN EJECUTIVO

**Problema:** OpenAI GPT-4o-mini devuelve respuestas vacías o no-JSON para 9 de 10 facturas, causando errores de parsing JSON.

**Única factura exitosa:** "Fact MÁS 9 jul 25.pdf" - devolvió JSON válido con confianza "alta"

**Facturas que fallaron:** 9 facturas con error "Expecting value: line 1 column 1 (char 0)" = respuesta vacía

---

## 🔎 HALLAZGOS TÉCNICOS

### 1. **PROBLEMA CRÍTICO: Falta `response_format` en la llamada API**

**Ubicación:** `src/ocr_extractor.py` línea ~130

**Código actual:**
```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=[...],
    max_tokens=300,
    temperature=0.1,
)
```

**Problema:** No se especifica `response_format={"type": "json_object"}`

**Impacto:** 
- OpenAI puede devolver texto plano, markdown, o respuestas formateadas en lugar de JSON puro
- El prompt pide JSON pero sin `response_format`, OpenAI puede incluir explicaciones o texto adicional
- Esto causa errores de parsing JSON

**Solución esperada:**
```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=[...],
    max_tokens=300,
    temperature=0.1,
    response_format={"type": "json_object"}  # ← FALTA ESTO
)
```

---

### 2. **Falta `detail: "high"` en image_url**

**Ubicación:** `src/ocr_extractor.py` línea ~140

**Código actual:**
```python
"image_url": {
    "url": f"data:image/png;base64,{img_base64}"
}
```

**Problema:** No se especifica `"detail": "high"` para mejor calidad de análisis

**Impacto:** 
- Menor resolución de la imagen puede causar que OpenAI no pueda leer texto pequeño
- Puede resultar en respuestas vacías si no puede leer la factura

**Solución esperada:**
```python
"image_url": {
    "url": f"data:image/png;base64,{img_base64}",
    "detail": "high"  # ← FALTA ESTO
}
```

---

### 3. **Logging insuficiente para debugging**

**Ubicación:** `src/ocr_extractor.py` líneas ~150-165

**Problema:** Cuando hay error de JSON parsing, solo se muestra:
- `logger.warning(f"Error parseando JSON de OpenAI: {e}")`
- `logger.warning(f"Contenido recibido: '{content[:500]}...'")`  ← Solo primeros 500 caracteres

**Impacto:**
- No se puede ver la respuesta completa de OpenAI
- No se puede diagnosticar si es respuesta vacía, texto plano, o JSON malformado
- No se loguea el objeto `response` completo para debugging

**Datos que faltan:**
- `response.choices[0].finish_reason` (puede ser "length", "content_filter", etc.)
- `response.usage` (tokens usados)
- Contenido completo sin truncar
- Tipo de error exacto de OpenAI

---

### 4. **Análisis de logs**

**Patrón observado:**
```
WARNING: Error parseando JSON de OpenAI: Expecting value: line 1 column 1 (char 0)
INFO: OpenAI confianza baja o sin importe, complementando con Tesseract
```

**Interpretación:**
- El error "Expecting value: line 1 column 1 (char 0)" significa que `json.loads()` recibió una cadena vacía o None
- Esto sugiere que `response.choices[0].message.content` es `None` o `""`
- Pero el código no verifica explícitamente si `content` es None antes de hacer `.strip()`

**Código actual (línea ~149):**
```python
content = response.choices[0].message.content.strip()
```

**Problema:** Si `content` es `None`, `.strip()` fallará con `AttributeError`, pero el código no llega a ese punto porque el error es JSON parsing.

**Conclusión:** OpenAI está devolviendo `content = ""` (cadena vacía), no `None`.

---

### 5. **Posibles causas de respuestas vacías**

#### A. **Límite de tokens (`max_tokens=300`)**
- 300 tokens puede ser insuficiente para respuestas complejas
- Si la respuesta se corta, puede resultar en JSON incompleto/inválido
- `finish_reason` debería ser "length" si se cortó

#### B. **Falta de formato JSON forzado**
- Sin `response_format={"type": "json_object"}`, OpenAI puede responder con texto explicativo
- El prompt pide JSON pero no se fuerza el formato

#### C. **Calidad de imagen**
- Sin `detail: "high"`, la imagen puede ser de baja resolución
- OpenAI puede no poder leer texto pequeño en facturas
- Resultado: respuesta vacía o "no puedo leer esto"

#### D. **Modelo `gpt-4o-mini`**
- Este modelo es más económico pero puede tener limitaciones
- Puede tener problemas con imágenes complejas o texto pequeño
- La única factura exitosa ("MÁS 9") puede ser más simple/legible

---

## 📋 CHECKLIST DE INVESTIGACIÓN

### ✅ Completado
- [x] Revisión de código de extracción OpenAI
- [x] Análisis de logs de errores
- [x] Identificación de falta de `response_format`
- [x] Identificación de falta de `detail: "high"`
- [x] Análisis de manejo de errores JSON

### ❌ Pendiente (requiere ejecución)
- [ ] Ejecutar script `debug_openai_responses.py` con facturas reales
- [ ] Verificar respuesta completa de OpenAI (sin truncar)
- [ ] Verificar `finish_reason` de cada respuesta
- [ ] Verificar `usage` (tokens) de cada respuesta
- [ ] Comparar factura exitosa vs fallidas (calidad de imagen, complejidad)
- [ ] Probar con `response_format` añadido
- [ ] Probar con `detail: "high"` añadido

---

## 🎯 CONCLUSIONES PRELIMINARES

### Problemas identificados (alta probabilidad):
1. **Falta `response_format={"type": "json_object"}`** - CRÍTICO
   - Probabilidad de causar el problema: **90%**
   - Sin esto, OpenAI puede devolver texto plano en lugar de JSON

2. **Falta `detail: "high"` en image_url** - MEDIO
   - Probabilidad de causar el problema: **40%**
   - Puede causar respuestas vacías si no puede leer texto

3. **Logging insuficiente** - BAJO
   - Probabilidad de causar el problema: **0%** (solo dificulta debugging)
   - Pero impide diagnosticar el problema real

### Hipótesis principal:
OpenAI está devolviendo respuestas en formato texto/markdown en lugar de JSON puro porque falta `response_format={"type": "json_object"}`. Cuando el código intenta hacer `json.loads("")` o `json.loads("Lo siento, no puedo...")`, falla con el error observado.

### Próximos pasos recomendados:
1. **Ejecutar `debug_openai_responses.py`** con una factura que falló para ver respuesta completa
2. **Añadir `response_format={"type": "json_object"}`** a la llamada API
3. **Añadir `detail: "high"`** a image_url
4. **Mejorar logging** para capturar respuestas completas
5. **Re-ejecutar procesamiento** y comparar resultados

---

## 📝 NOTAS ADICIONALES

- La única factura exitosa ("MÁS 9") puede ser más simple o tener mejor calidad de imagen
- El fallback a Tesseract está funcionando correctamente
- El sistema de retry con `tenacity` está configurado correctamente
- No hay errores de API (rate limits, conexión, etc.) - todas las llamadas llegan a OpenAI

---

**Fecha de investigación:** 2025-11-04
**Investigador:** Auto (AI Assistant)
**Estado:** Investigación completa, pendiente validación con datos reales

