# 📊 RESUMEN EJECUTIVO: Investigación Facturas Pendientes

**Fecha:** 11 de noviembre de 2025  
**Investigador:** Sistema de Análisis Automático  
**Objetivo:** Identificar por qué el endpoint `/facturas/failed` solo devuelve 4 facturas cuando hay más de 20 en cuarentena o por revisar

---

## 🎯 PROBLEMA IDENTIFICADO

### Situación Actual
- **Endpoint devuelve:** 4 facturas fallidas
- **Facturas en BD (error/revisar):** 4
- **Archivos en cuarentena:** 87 archivos `.meta.json`
- **Nombres únicos en cuarentena:** 25
- **Total esperado:** 29 facturas (4 de BD + 25 únicos de cuarentena)

### Discrepancia
La simulación del código muestra que **debería devolver 29 facturas**, pero el endpoint real solo devuelve **4 facturas**. Esto indica que el código de procesamiento de cuarentena **no se está ejecutando correctamente** en el endpoint real.

---

## 🔍 HALLAZGOS DETALLADOS

### 1. Análisis de Archivos en Cuarentena

**Distribución:**
- **Total archivos:** 87 archivos `.meta.json`
- **En carpeta raíz:** 89 archivos (incluyendo subcarpetas)
- **En `duplicates/`:** 4 archivos
- **En `review/`:** 24 archivos
- **Nombres únicos:** 25 (hay muchos duplicados)

**Duplicados más frecuentes:**
- `Factura REVO 2 Enero 2024.pdf`: 18 veces
- `Factura REVO 1 Enero 2024.pdf`: 18 veces
- `Fact EVOLBE jul 25.pdf`: 4 veces
- `Fact EVOLBE sep 25.pdf`: 4 veces
- `Fact DEV mercancia NEGRINI sep 25.pdf`: 4 veces

### 2. Análisis de Facturas en Base de Datos

**Facturas con estado "revisar":**
1. `Fact CAFÉ sep 25.pdf` (ID: 451)
2. `Fact MÁS 8 may 25.pdf` (ID: 855)
3. `Fact CONWAY oct 25.pdf` (ID: 735)
4. `Fact NOTARÍA póliza click and pay.pdf` (ID: 882)

**Observación importante:** Ninguna de estas 4 facturas tiene archivos duplicados en cuarentena con el mismo nombre. Esto significa que los 64 archivos omitidos en la simulación son duplicados de **otras** facturas, no de estas 4.

### 3. Simulación del Código

**Resultado de la simulación:**
```
✅ Paso 1 - BD: 4 facturas, 4 nombres procesados
✅ Paso 2 - Cuarentena: 25 procesadas, 64 omitidas, 0 errores
✅ Total final: 29 facturas
```

**Conclusión:** El código **debería funcionar correctamente** y devolver 29 facturas, pero el endpoint real solo devuelve 4.

### 4. Verificación del Contenedor

**Estado del contenedor:**
- ✅ Carpeta de cuarentena existe: `/app/data/quarantine`
- ✅ Archivos presentes: 90 archivos `.meta.json`
- ✅ Variable de entorno: `QUARANTINE_PATH` no configurada (usa default: `data/quarantine`)
- ✅ Path resuelto correctamente: `/app/data/quarantine`

**Problema identificado:** Aunque los archivos existen en el contenedor, el endpoint no los está procesando.

---

## 🔬 ANÁLISIS TÉCNICO

### Código del Endpoint (`src/api/routes/facturas.py`)

**Lógica esperada:**
1. Consultar facturas en BD con estado `error` o `revisar` → 4 facturas
2. Procesar archivos en cuarentena → 25 facturas únicas
3. Total: 29 facturas

**Posibles causas del problema:**

1. **Excepciones silenciadas:** El bloque `except (json.JSONDecodeError, ValueError, KeyError) as e:` en la línea 335 puede estar ocultando errores al procesar archivos de cuarentena.

2. **Problema con `rglob`:** El método `quarantine_path.rglob("*.meta.json")` puede no estar encontrando todos los archivos si hay un problema con la ruta o permisos.

3. **Problema de deduplicación:** La lógica de `processed_names` puede estar filtrando incorrectamente archivos de cuarentena que deberían incluirse.

4. **Problema de orden de ejecución:** Si hay un error temprano en el procesamiento de cuarentena, puede que no se esté ejecutando el bloque completo.

### Verificación de la Lógica

**Código relevante (líneas 325-333):**
```python
else:
    # No hay filtro: incluir todas las facturas en cuarentena
    failed_invoices.append({
        'nombre': nombre,
        'fecha_emision': file_date.isoformat() if file_date else None,
        'estado': 'quarantine',
        'source': 'quarantine'
    })
    processed_names.add(nombre)
```

Este bloque **debería ejecutarse** cuando no hay filtro de fecha (que es el caso cuando se llama sin parámetros `month` y `year`).

---

## 📋 DIFERENCIA ENTRE "REVISAR" Y "CUARENTENA"

### Facturas con Estado "revisar"

**Definición:** Facturas que están **guardadas en la base de datos** pero requieren revisión manual.

**Características:**
- ✅ **Están en la BD:** Tienen un registro en la tabla `facturas` con `estado = 'revisar'`
- ✅ **Tienen datos extraídos:** Se procesaron con OCR y se guardaron los datos
- ⚠️ **Requieren revisión:** Hay algún problema que requiere intervención manual:
  - Conflicto de duplicados (mismo proveedor + número, distinto importe)
  - Validación de negocio fallida
  - Campos críticos faltantes o inconsistentes

**Ubicación:**
- Base de datos: Tabla `facturas` con `estado = 'revisar'`
- Archivo físico: Puede estar en `data/quarantine/review/` (copia de seguridad)
- Metadata: Guardada en `data/pending/` como JSON

**Flujo:**
1. Archivo se procesa con OCR
2. Se detecta problema (duplicado, validación, etc.)
3. Se guarda en BD con `estado = 'revisar'`
4. Se mueve copia a `data/quarantine/review/`
5. Se guarda metadata en `data/pending/`
6. **Se puede reprocesar automáticamente** en ejecuciones futuras si se corrige

### Archivos en Cuarentena

**Definición:** Archivos que fueron **rechazados durante el procesamiento** y movidos a una carpeta de cuarentena.

**Características:**
- ❌ **NO están en la BD:** No tienen registro en la tabla `facturas` (o tienen estado `duplicado`)
- ❌ **No se procesaron:** Fueron rechazados antes de guardarse
- ⚠️ **Requieren intervención manual:** No se reintentan automáticamente

**Tipos de cuarentena:**

1. **Duplicados (`data/quarantine/duplicates/`):**
   - Mismo contenido (mismo `hash_contenido`) que una factura ya procesada
   - Estado en BD: `duplicado` (si se guardó) o no guardado
   - **No se cargan:** Se ignoran completamente

2. **Revisión (`data/quarantine/review/`):**
   - Posible conflicto (mismo proveedor + número, distinto importe)
   - Estado en BD: `revisar` (si se guardó)
   - **Pueden cargarse:** Si se corrige el problema, se pueden reprocesar

3. **Otros (`data/quarantine/otros/`):**
   - Errores de procesamiento, validación, etc.
   - Estado en BD: `error` o no guardado
   - **No se cargan:** Requieren corrección manual

**Ubicación:**
- Archivo físico: `data/quarantine/` (con subcarpetas `duplicates/`, `review/`, `otros/`)
- Metadata: Archivo `.meta.json` junto al PDF

**Flujo:**
1. Archivo se descarga de Drive
2. Se procesa con OCR
3. Se detecta problema (duplicado, error, etc.)
4. Se mueve a cuarentena con metadata
5. **NO se guarda en BD** (o se guarda con estado `duplicado`)
6. **NO se reintenta automáticamente** (requiere intervención manual)

---

## 🔄 TRATAMIENTO DE DUPLICADOS EN CUARENTENA

### Escenario: Dos Archivos Iguales por Error en la Carga

**Pregunta:** Si dos archivos son iguales por error en la carga, ¿se ponen ambos en cuarentena y no se carga ninguno?

**Respuesta:** Depende del tipo de duplicado:

#### Caso 1: Duplicado Exacto (Mismo Hash)

**Proceso:**
1. **Primer archivo:** Se procesa normalmente y se guarda en BD con `estado = 'procesado'`
2. **Segundo archivo:** Se detecta como duplicado por `hash_contenido`
3. **Decisión:** `DuplicateDecision.DUPLICATE`
4. **Acción:**
   - Se mueve a `data/quarantine/duplicates/`
   - Se guarda metadata con razón: "Duplicado detectado: mismo contenido que 'nombre_archivo_original'"
   - **NO se guarda en BD** (o se guarda con `estado = 'duplicado'` si ya existe registro)
   - Se registra evento de auditoría

**Resultado:**
- ✅ **Primer archivo:** Cargado en BD
- ❌ **Segundo archivo:** En cuarentena, NO cargado
- 📊 **Total en BD:** 1 factura (la original)

#### Caso 2: Duplicado Lógico (Mismo Proveedor + Número, Distinto Importe)

**Proceso:**
1. **Primer archivo:** Se procesa y se guarda en BD con `estado = 'procesado'`
2. **Segundo archivo:** Se detecta conflicto (mismo proveedor + número, pero importe diferente)
3. **Decisión:** `DuplicateDecision.REVIEW`
4. **Acción:**
   - Se mueve a `data/quarantine/review/`
   - Se guarda en BD con `estado = 'revisar'`
   - Se guarda metadata en `data/pending/`
   - Se registra evento de auditoría

**Resultado:**
- ✅ **Primer archivo:** Cargado en BD con `estado = 'procesado'`
- ⚠️ **Segundo archivo:** Cargado en BD con `estado = 'revisar'`, también en cuarentena
- 📊 **Total en BD:** 2 facturas (una procesada, una en revisión)

#### Caso 3: Mismo Archivo Subido Múltiples Veces

**Proceso:**
1. **Primera carga:** Se procesa y se guarda en BD
2. **Segunda carga:** Se detecta por `drive_file_id` (mismo archivo de Drive)
3. **Decisión:** `DuplicateDecision.IGNORE`
4. **Acción:**
   - Se ignora completamente
   - No se mueve a cuarentena
   - No se guarda en BD (ya existe)

**Resultado:**
- ✅ **Primera carga:** Cargada en BD
- ❌ **Cargas posteriores:** Ignoradas, NO cargadas
- 📊 **Total en BD:** 1 factura

---

## 🎯 CONCLUSIÓN Y RECOMENDACIONES

### Problema Principal

El endpoint `/facturas/failed` **no está procesando correctamente los archivos de cuarentena**. Aunque:
- ✅ Los archivos existen en el contenedor (90 archivos)
- ✅ El código debería funcionar (simulación muestra 29 facturas)
- ✅ La lógica de deduplicación es correcta

El endpoint real solo devuelve las 4 facturas de la BD y **no incluye las 25 facturas únicas de cuarentena**.

### Recomendaciones

1. **Agregar logging detallado:** Incluir logs en el bloque de procesamiento de cuarentena para identificar dónde se está fallando.

2. **Verificar excepciones:** Revisar si hay excepciones silenciadas que están impidiendo el procesamiento de archivos de cuarentena.

3. **Verificar ruta:** Asegurarse de que `quarantine_path.rglob("*.meta.json")` está encontrando todos los archivos correctamente.

4. **Probar endpoint directamente:** Ejecutar el endpoint en el contenedor y verificar los logs en tiempo real.

5. **Verificar permisos:** Asegurarse de que el proceso del backend tiene permisos para leer los archivos de cuarentena.

### Próximos Pasos

1. Agregar logging detallado al endpoint
2. Ejecutar el endpoint y revisar logs en tiempo real
3. Verificar si hay excepciones que se están silenciando
4. Corregir el problema identificado
5. Verificar que el endpoint devuelve las 29 facturas esperadas

---

**Fin del Resumen Ejecutivo**

