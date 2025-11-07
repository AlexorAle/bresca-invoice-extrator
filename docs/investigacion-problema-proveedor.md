# Investigación: Problema de Identificación de Proveedor vs Cliente

**Fecha:** 6 de noviembre de 2025  
**Problema:** El sistema está guardando el nombre del CLIENTE en lugar del PROVEEDOR

---

## 🔍 Problema Identificado

### Situación Actual

**En la Base de Datos:**
- `proveedor_text`: Contiene **"MANTUA EAGLE SL"** (el CLIENTE)
- Debería contener: **"Energya-VM comercializadora"** (el PROVEEDOR/EMISOR)

**Ejemplo Real:**
- Factura de Energya-VM del 8/7/2025
- Cliente: MANTUA EAGLE SL (restaurante)
- Emisor: Energya-VM comercializadora
- **Problema:** Se guarda "MANTUA EAGLE SL" como proveedor_text

---

## 📊 Análisis del Sistema Actual

### 1. Prompt de OpenAI

**Estado actual:**
```python
PROMPT_TEMPLATE = """
1. Busca el NOMBRE DEL CLIENTE o EMPRESA (campos como "Cliente:", "Bill to:", "Facturar a:", nombre de empresa)
...
{
  "nombre_cliente": "Nombre exacto del cliente o empresa",
  ...
}
```

**Problema:**
- ✅ Extrae correctamente el CLIENTE (Mantua Eagle SL)
- ❌ NO extrae el PROVEEDOR/EMISOR (Energya-VM)

### 2. Mapeo en parser_normalizer.py

**Código actual:**
```python
# Mapear nombre_cliente a proveedor_text si no existe proveedor_text
if not raw_data.get('proveedor_text') and raw_data.get('nombre_cliente'):
    raw_data['proveedor_text'] = raw_data['nombre_cliente']
```

**Problema:**
- Mapea `nombre_cliente` → `proveedor_text`
- Esto es incorrecto: el cliente NO es el proveedor

### 3. Datos en BD

**Ejemplos encontrados:**
- `proveedor_text: "MANTUA EAGLE, S.L."` → Es el CLIENTE
- `proveedor_text: "MANTUA EAGLE SL"` → Es el CLIENTE
- `proveedor_text: "BRESCA MALAGA"` → Posiblemente también cliente
- `proveedor_text: "RESTAURANTE BRESCA"` → Posiblemente también cliente

**Campos disponibles en BD:**
- ✅ `proveedor_text`: TEXT (actualmente tiene cliente)
- ✅ `metadatos_json`: JSONB (puede tener info adicional)
- ✅ `conceptos_json`: JSONB (puede tener info del emisor)
- ✅ `drive_file_name`: TEXT (puede tener pista: "Fact CONWAY...", "Fact ENERGYA...")

---

## 💡 Propuestas de Solución

### Opción 1: Extraer Ambos Campos (Recomendada)

**Cambios necesarios:**

1. **Actualizar prompt de OpenAI:**
   ```python
   PROMPT_TEMPLATE = """
   1. Busca el NOMBRE DEL PROVEEDOR/EMISOR (empresa que emite la factura)
      - Suele estar en el header/logo de la factura
      - Campos como "Emitido por:", "From:", nombre de la empresa en el encabezado
   2. Busca el NOMBRE DEL CLIENTE (empresa que recibe la factura)
      - Campos como "Cliente:", "Bill to:", "Facturar a:"
   ...
   {
     "nombre_proveedor": "Energya-VM comercializadora",
     "nombre_cliente": "MANTUA EAGLE SL",
     ...
   }
   ```

2. **Actualizar parser_normalizer.py:**
   ```python
   # Usar nombre_proveedor para proveedor_text
   if raw_data.get('nombre_proveedor'):
       raw_data['proveedor_text'] = raw_data['nombre_proveedor']
   elif raw_data.get('proveedor_text'):
       # Ya existe, mantenerlo
       pass
   else:
       # Fallback: intentar extraer del nombre del archivo
       raw_data['proveedor_text'] = extract_proveedor_from_filename(metadata.get('drive_file_name'))
   ```

3. **Agregar campo opcional en BD (futuro):**
   - `cliente_text`: TEXT (para guardar el cliente si es necesario)
   - Mantener `proveedor_text` para el emisor

**Ventajas:**
- ✅ Solución completa y correcta
- ✅ Distingue claramente proveedor vs cliente
- ✅ Permite análisis por proveedor real

**Desventajas:**
- ⚠️ Requiere reprocesar facturas existentes
- ⚠️ OpenAI puede confundirse en algunos casos

---

### Opción 2: Extraer Proveedor del Nombre del Archivo (Temporal)

**Cambios necesarios:**

1. **Función para extraer proveedor del filename:**
   ```python
   def extract_proveedor_from_filename(filename):
       # "Fact CONWAY JULIO 25.pdf" → "CONWAY"
       # "Fact ENERGYA jul 25.pdf" → "ENERGYA"
       # "Fact CAFÉ JUL 25.pdf" → "CAFÉ"
       if filename.startswith("Fact "):
           parts = filename.replace("Fact ", "").split()
           return parts[0]  # Primera palabra después de "Fact"
       return None
   ```

2. **Usar como fallback:**
   ```python
   # Si no hay proveedor_text, intentar del filename
   if not raw_data.get('proveedor_text'):
       proveedor = extract_proveedor_from_filename(metadata.get('drive_file_name'))
       if proveedor:
           raw_data['proveedor_text'] = proveedor
   ```

**Ventajas:**
- ✅ Rápido de implementar
- ✅ Funciona con el patrón actual de nombres
- ✅ No requiere reprocesar

**Desventajas:**
- ⚠️ Depende del formato del nombre del archivo
- ⚠️ No es 100% confiable
- ⚠️ No distingue proveedor real del cliente

---

### Opción 3: Híbrida (Recomendada para Producción)

**Combinar ambas opciones:**

1. **Actualizar prompt** para extraer `nombre_proveedor`
2. **Fallback al filename** si OpenAI no lo encuentra
3. **Validación**: Si el proveedor extraído es "MANTUA EAGLE" o similar, usar filename

**Lógica:**
```python
# 1. Intentar extraer del prompt (nombre_proveedor)
proveedor = raw_data.get('nombre_proveedor')

# 2. Si no existe o es el cliente conocido, usar filename
if not proveedor or proveedor.upper() in ['MANTUA EAGLE', 'MANTUA EAGLE SL', 'MANTUA EAGLE, S.L.']:
    proveedor = extract_proveedor_from_filename(metadata.get('drive_file_name'))

# 3. Asignar a proveedor_text
raw_data['proveedor_text'] = proveedor or raw_data.get('nombre_cliente', 'Desconocido')
```

---

## 📋 Información Disponible en Facturas

### En la Factura de Energya-VM:

**Emisor/Proveedor (lo que necesitamos):**
- "Energya-VM comercializadora" (header/logo)
- CIF: B-83393006
- Dirección: C/Federico Mompoun 5, Madrid

**Cliente (lo que estamos guardando):**
- "MANTUA EAGLE SL" (en "Datos cliente")
- CIF: B44806545
- Dirección: CALLE TRINIDAD GRUND, NUM 28, Málaga

**Campos en la factura:**
- Header: Nombre del emisor
- "Datos cliente": Nombre del cliente
- Footer: Información legal del emisor

---

## 🎯 Recomendación Final

### Solución Propuesta: Opción 3 (Híbrida)

1. **Actualizar prompt** para extraer:
   - `nombre_proveedor`: Emisor de la factura
   - `nombre_cliente`: Receptor de la factura (opcional, para referencia)

2. **Implementar fallback**:
   - Si `nombre_proveedor` no existe o es "MANTUA EAGLE", usar filename
   - Extraer primera palabra después de "Fact " en el nombre del archivo

3. **Validación inteligente**:
   - Lista de clientes conocidos: ["MANTUA EAGLE", "MANTUA EAGLE SL", ...]
   - Si el proveedor extraído está en la lista de clientes → usar filename

4. **Migración de datos existentes**:
   - Script para reprocesar facturas existentes
   - O actualizar manualmente las más importantes

---

## ⚠️ Consideraciones

1. **Reprocesamiento**: Las facturas ya procesadas tendrán el cliente como proveedor
2. **Confianza de OpenAI**: Puede confundirse en facturas complejas
3. **Nombres de archivo**: Dependen del formato de nombrado en Drive
4. **Validación**: Necesitamos una lista de clientes conocidos para validar

---

## 📝 Próximos Pasos (Solo Investigación)

1. ✅ Identificar el problema (completado)
2. ⏳ Proponer solución detallada (este documento)
3. ⏳ Validar con ejemplos reales
4. ⏳ Implementar cuando se apruebe

---

**Estado:** 🔍 Investigación completada - Esperando aprobación para implementar

