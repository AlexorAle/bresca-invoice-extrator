# Evaluación de Problemas en el Dashboard

**Fecha:** 5 de noviembre de 2025  
**Objetivo:** Identificar y documentar inconsistencias entre datos de BD y visualización en dashboard

---

## 📋 Problemas Identificados

### 1. ❌ Tarjeta "Facturas del Mes" muestra "NaN"

**Síntoma:**
- Dashboard muestra: `NaN`
- Valor esperado: `27` (o `27/27` si se muestra formato)

**Causa raíz:**
- En `frontend/src/hooks/useInvoiceData.js`, función `transformToKPIs()`:
  ```javascript
  facturas: {
    actual: summary.facturas_exitosas || 0,  // ← Esto es 0
    total: summary.total_facturas || 0,        // ← Esto es 27
    cambio: 0
  }
  ```
- En `frontend/src/components/KPIGrid.jsx`:
  ```javascript
  value: `${data.facturas.actual}/${data.facturas.total}`
  ```
- Si `data.facturas.actual` es `undefined` o `NaN`, entonces muestra `NaN/27`

**Datos reales de la API:**
```json
{
  "total_facturas": 27,
  "facturas_exitosas": 0,  // ← PROBLEMA: Debería ser 27
  "facturas_fallidas": 27,  // ← PROBLEMA: Debería ser 1
  ...
}
```

**Solución propuesta:**
- Cambiar `actual: summary.facturas_exitosas || 0` por `actual: summary.total_facturas || 0`
- O corregir el cálculo de `facturas_exitosas` en el backend (ver problema #2)

---

### 2. ❌ Tarjeta "Calidad del Procesamiento" muestra valores incorrectos

**Síntoma:**
- "Procesadas exitosamente": `0 ✅` (debería ser `27`)
- "Fallidas / Corruptas": `27 ⚠️` (debería ser `1`)

**Causa raíz:**
- En `src/db/repositories.py`, función `get_summary_by_month()`:
  ```python
  facturas_exitosas = facturas_query.filter(Factura.estado == 'procesado').count()
  facturas_fallidas = facturas_query.filter(
      Factura.estado.in_(['error', 'revisar'])
  ).count()
  ```

**Datos reales en BD:**
- Total de facturas en BD: **29**
- Facturas de julio 2025: **27**
- **TODAS las facturas tienen `estado = 'revisar'`** (ninguna tiene `estado = 'procesado'`)

**¿Por qué todas están en 'revisar'?**
- Según los logs del procesamiento, todas las facturas fallaron la validación fiscal:
  ```
  WARNING: Validación fiscal falló: fecha_emision (2025-07-31) tiene formato inválido
  WARNING: DTO no pasó validación fiscal
  ```
- Aunque la fecha se guarda correctamente, la validación fiscal está fallando porque espera un string pero recibe un objeto `date`
- **Nota:** Ya corregimos la validación fiscal, pero las facturas ya procesadas quedaron con estado 'revisar'

**Datos reales de IngestEvent:**
- Total eventos: 141
- Eventos exitosos: (no se pudo contar, campo 'estado' no existe en IngestEvent)
- Eventos fallidos: 1 (solo EVOLBE que estaba corrupto)

**Solución propuesta:**
1. **Opción A (Recomendada):** Cambiar la lógica de `get_summary_by_month()`:
   - `facturas_exitosas`: contar facturas con `importe_total > 0` Y `estado != 'error'`
   - `facturas_fallidas`: contar facturas con `estado == 'error'` O `importe_total IS NULL`
   
2. **Opción B:** Actualizar el estado de las facturas existentes:
   - Cambiar de `estado = 'revisar'` a `estado = 'procesado'` para facturas con `importe_total > 0`

3. **Opción C:** Usar IngestEvent para contar exitosas/fallidas:
   - Contar eventos exitosos vs fallidos en lugar de usar el campo `estado` de Factura

---

### 3. ⚠️ Tilde verde en "Procesadas exitosamente" cuando muestra 0

**Síntoma:**
- Muestra `0 ✅` con tilde verde
- Debería mostrar indicador rojo o amarillo cuando es 0

**Causa:**
- En `frontend/src/components/QualityPanel.jsx`:
  ```javascript
  {
    label: 'Procesadas exitosamente',
    value: `${formatNumber(quality.exitosas)} ✅`,  // ← Siempre muestra ✅
    badgeClass: 'bg-green-100 text-green-700'       // ← Siempre verde
  }
  ```
- No hay lógica condicional para cambiar el color según el valor

**Solución propuesta:**
- Agregar lógica condicional:
  ```javascript
  badgeClass: quality.exitosas > 0 
    ? 'bg-green-100 text-green-700' 
    : 'bg-red-100 text-red-700'
  ```

---

## 📊 Resumen de Datos Reales

### Base de Datos:
- **Total facturas:** 29
- **Facturas de julio 2025:** 27
- **Con fecha_emision:** 29 (100%)
- **Importe total julio:** 8,534.73 €
- **Promedio:** 316.10 €
- **Proveedores únicos:** 11

### Estado de Facturas:
- **Todas tienen `estado = 'revisar'`** (ninguna tiene 'procesado')
- **Razón:** Validación fiscal falló durante el procesamiento (ya corregida)

### IngestEvent:
- **Total eventos:** 141
- **Eventos fallidos:** 1 (solo EVOLBE corrupto)

### API Response:
```json
{
  "total_facturas": 27,        // ✅ Correcto
  "facturas_exitosas": 0,      // ❌ Incorrecto (debería ser 27)
  "facturas_fallidas": 27,     // ❌ Incorrecto (debería ser 1)
  "importe_total": 8534.73,    // ✅ Correcto
  "promedio_factura": 316.10,   // ✅ Correcto
  "proveedores_activos": 11,    // ✅ Correcto
  "confianza_extraccion": 100.0 // ✅ Correcto
}
```

---

## 🔧 Correcciones Necesarias

### Prioridad Alta:

1. **Corregir cálculo de `facturas_exitosas` y `facturas_fallidas` en `get_summary_by_month()`**
   - Archivo: `src/db/repositories.py`
   - Cambiar lógica para usar `importe_total > 0` en lugar de `estado == 'procesado'`

2. **Corregir transformación de datos en `transformToKPIs()`**
   - Archivo: `frontend/src/hooks/useInvoiceData.js`
   - Usar `total_facturas` para `actual` si `facturas_exitosas` es 0

3. **Agregar lógica condicional para colores en QualityPanel**
   - Archivo: `frontend/src/components/QualityPanel.jsx`
   - Cambiar color según valor de métricas

### Prioridad Media:

4. **Actualizar estado de facturas existentes**
   - Cambiar `estado = 'revisar'` a `estado = 'procesado'` para facturas válidas
   - Script SQL o Python para migración

5. **Agregar espera de 3 segundos entre facturas en OpenAI**
   - Archivo: `src/pipeline/ingest.py` o `src/ocr_extractor.py`
   - Evitar rate limiting

---

## 📝 Notas Técnicas

### Campo `estado` en Factura:
- Valores válidos: `'procesado'`, `'pendiente'`, `'error'`, `'revisar'`, `'duplicado'`
- Default: `'procesado'`
- **Problema:** Las facturas se están guardando con `'revisar'` porque falla la validación fiscal

### Validación Fiscal:
- Ya corregida para aceptar objetos `date`
- Pero las facturas ya procesadas quedaron con estado 'revisar'
- Necesita migración de datos o cambio en lógica de conteo

---

## ✅ Checklist de Verificación

- [x] Identificar problema en "Facturas del Mes" (NaN)
- [x] Identificar problema en "Calidad del Procesamiento" (0 exitosas, 27 fallidas)
- [x] Verificar datos reales en BD
- [x] Verificar respuesta de API
- [x] Revisar código de transformación de datos
- [x] Revisar código de cálculo en backend
- [x] Documentar todas las inconsistencias
- [ ] **PENDIENTE:** Implementar correcciones (según instrucciones del usuario)

---

**Estado:** ✅ Evaluación completada - Esperando aprobación para implementar correcciones

