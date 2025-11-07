# Resumen de Implementación: Corrección Proveedor vs Cliente

**Fecha:** 6 de noviembre de 2025  
**Estado:** ✅ Implementado

---

## 📋 Problema Resuelto

**Antes:**
- `proveedor_text` contenía el CLIENTE (MANTUA EAGLE SL)
- No se distinguía entre emisor y receptor de la factura

**Ahora:**
- `proveedor_text` contiene el PROVEEDOR/EMISOR (Energya-VM, CONWAY, etc.)
- `nombre_cliente` se guarda en `metadatos_json` (no se muestra en dashboard)
- Si no hay proveedor, la factura se marca como problemática y va a cuarentena

---

## 🔧 Cambios Implementados

### 1. ✅ Prompt de OpenAI Actualizado

**Archivo:** `src/ocr_extractor.py`

**Cambios:**
- Ahora extrae `nombre_proveedor` (OBLIGATORIO) - emisor de la factura
- También extrae `nombre_cliente` (opcional) - receptor de la factura
- Instrucciones claras sobre dónde buscar cada campo
- `max_tokens` aumentado a 400

**Formato de respuesta:**
```json
{
  "nombre_proveedor": "Energya-VM comercializadora",
  "nombre_cliente": "MANTUA EAGLE SL",
  "importe_total": 2067.67,
  "fecha_emision": "2025-07-08",
  "confianza": "alta"
}
```

### 2. ✅ Parser Normalizer Actualizado

**Archivo:** `src/parser_normalizer.py`

**Cambios:**
- Usa `nombre_proveedor` para `proveedor_text` (correcto)
- Guarda `nombre_cliente` en `metadatos_json` (no visible en dashboard)
- Validación fiscal: `proveedor_text` es obligatorio

**Código:**
```python
# Usar nombre_proveedor para proveedor_text
if raw_data.get('nombre_proveedor'):
    raw_data['proveedor_text'] = raw_data['nombre_proveedor']
else:
    raw_data['proveedor_text'] = None  # Será validado después
```

### 3. ✅ Validación Fiscal Actualizada

**Archivo:** `src/parser_normalizer.py`

**Nueva validación:**
```python
# Proveedor/Emisor debe existir (OBLIGATORIO)
proveedor_text = data.get('proveedor_text')
if not proveedor_text or not proveedor_text.strip():
    errors.append("proveedor_text es obligatorio (nombre del emisor de la factura)")
```

### 4. ✅ Validación en Pipeline de Ingest

**Archivo:** `src/pipeline/ingest.py`

**Nueva validación crítica:**
- Si `proveedor_text` es None o vacío después de crear DTO:
  - Marca como `estado = 'error'`
  - Mueve a cuarentena (carpeta `review`)
  - Registra evento de error
  - Aparece en "Facturas No Procesadas" del dashboard

**Código:**
```python
if not factura_dto.get('proveedor_text') or not factura_dto.get('proveedor_text').strip():
    error_msg = "Nombre del proveedor/emisor no encontrado en la factura"
    # Mover a cuarentena y marcar como error
    duplicate_manager.move_to_quarantine(file_info, DuplicateDecision.REVIEW, factura_dto, error_msg)
    continue  # Saltar este archivo
```

### 5. ✅ Almacenamiento de nombre_cliente

**Archivo:** `src/parser_normalizer.py`

**Cambio:**
- `nombre_cliente` se guarda en `metadatos_json`
- No se muestra en el dashboard
- Disponible para consultas futuras si es necesario

**Código:**
```python
'metadatos_json': {
    **metadata,
    'nombre_cliente': raw_data.get('nombre_cliente')  # Cliente que recibe la factura
}
```

---

## 📊 Flujo de Procesamiento

### Caso 1: Factura con Proveedor ✅

```
1. OpenAI extrae: nombre_proveedor = "Energya-VM comercializadora"
2. parser_normalizer: proveedor_text = "Energya-VM comercializadora"
3. Validación: ✅ proveedor_text existe
4. Procesamiento: ✅ Continúa normalmente
5. Guardado en BD: ✅ proveedor_text = "Energya-VM comercializadora"
```

### Caso 2: Factura sin Proveedor ❌

```
1. OpenAI extrae: nombre_proveedor = null
2. parser_normalizer: proveedor_text = None
3. Validación en ingest: ❌ proveedor_text es None
4. Acción: 
   - estado = 'error'
   - error_msg = "Nombre del proveedor/emisor no encontrado en la factura"
   - Mover a cuarentena (data/quarantine/review/)
   - Registrar evento de error
5. Resultado: Aparece en "Facturas No Procesadas" del dashboard
```

---

## 🎯 Resultados Esperados

### Dashboard

**Antes:**
- "Desglose por Categorías": Todas mostraban "MANTUA EAGLE SL"

**Ahora:**
- "Desglose por Categorías": Muestra proveedores reales:
  - Energya-VM comercializadora
  - CONWAY
  - GIRO
  - CBG
  - etc.

### Facturas No Procesadas

**Nuevas facturas que aparecerán:**
- Facturas donde OpenAI no pudo extraer el nombre del proveedor
- Se mostrarán en el panel "Facturas No Procesadas"
- Requerirán revisión manual

---

## ⚠️ Consideraciones

### Facturas Ya Procesadas

**Problema:**
- Las facturas ya procesadas tienen `proveedor_text = "MANTUA EAGLE SL"` (cliente)

**Solución:**
- Opción A: Reprocesar todas las facturas (recomendado para producción limpia)
- Opción B: Script de migración para actualizar proveedor_text basado en nombre del archivo
- Opción C: Dejar como están y solo corregir nuevas facturas

### Validación de OpenAI

**Riesgo:**
- OpenAI puede confundirse en facturas complejas
- Puede extraer cliente en lugar de proveedor

**Mitigación:**
- Prompt muy específico sobre qué buscar
- Validación estricta: si no hay proveedor → cuarentena
- Revisión manual de facturas en cuarentena

---

## ✅ Checklist de Verificación

- [x] Prompt actualizado para extraer nombre_proveedor
- [x] Parser normalizer usa nombre_proveedor
- [x] Validación fiscal incluye proveedor_text obligatorio
- [x] Validación en ingest mueve a cuarentena si no hay proveedor
- [x] nombre_cliente guardado en metadatos_json
- [x] max_tokens aumentado a 400
- [ ] **PENDIENTE:** Probar con facturas reales
- [ ] **PENDIENTE:** Verificar que aparecen en "Facturas No Procesadas" si fallan

---

## 🚀 Próximos Pasos

1. **Probar con primera carga:**
   ```bash
   ./scripts/primera_carga.sh
   ```

2. **Verificar resultados:**
   - Dashboard debe mostrar proveedores reales
   - Facturas sin proveedor deben aparecer en "Facturas No Procesadas"

3. **Si hay facturas en cuarentena:**
   - Revisar manualmente
   - Corregir el prompt si es necesario
   - Reprocesar si es posible

---

**Estado:** ✅ Implementación completada - Lista para probar

