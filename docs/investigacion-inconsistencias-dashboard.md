# Investigación: Inconsistencias en Dashboard

**Fecha:** 6 de noviembre de 2025  
**Problema reportado:** 
- Dashboard muestra 5 facturas en "Facturas No Procesadas" para noviembre
- Factura "Fact EVOLBE jul 25.pdf" aparece como no procesada pero es legible
- Inconsistencias entre datos procesados y datos mostrados

---

## 🔍 Hallazgos de la Investigación

### 1. Datos en Base de Datos

**Total de facturas en BD:** 4 facturas
- **Estado:** Todas con `estado = 'revisar'`
- **Distribución por mes:**
  - Julio 2025: 3 facturas
  - Agosto 2025: 1 factura
  - **Noviembre 2025: 0 facturas** ⚠️

**Facturas procesadas (de la prueba de 5):**
1. Fact CONWAY JUL 25.pdf ✅
2. Fact GIRO 1 jul 25.pdf ✅
3. Fact HONORARIOS laboral jul 25.pdf ✅
4. Fact CONWAY JULIO 25.pdf ✅
5. Fact EVOLBE jul 25.pdf ❌ (marcada como corrupta)

---

### 2. Archivos en Cuarentena

**Total de archivos en cuarentena:** 5 archivos

**Archivos puestos en cuarentena el 6 de noviembre (hoy):**

1. **Fact EVOLBE jul 25.pdf** (2 veces)
   - Primera vez: 2025-11-06 07:31:24
   - Segunda vez: 2025-11-06 09:56:57
   - **Razón:** "Archivo inválido o corrupto"
   - **Tamaño:** 102,064 bytes
   - **Observación:** El archivo parece ser válido según el usuario

2. **Fact NEGRINI del mercancía 3 jul 25.pdf**
   - Fecha: 2025-11-06 07:35:33
   - **Razón:** Error de BD - `importe_total` negativo (-58.30) viola constraint
   - **Error:** `CheckViolation: facturas_importe_total_check`

3. **Fact REVO 1 jul 25.pdf**
   - Fecha: 2025-11-06 07:40:04
   - **Razón:** Error de BD - `importe_total` es NULL, viola constraint NOT NULL
   - **Error:** `NotNullViolation: null value in column "importe_total"`

4. **Fact REVO 2 jul 25.pdf**
   - Fecha: 2025-11-06 07:40:01
   - **Razón:** Error de BD - `importe_total` es NULL, viola constraint NOT NULL
   - **Error:** `NotNullViolation: null value in column "importe_total"`

---

### 3. Problema Principal: Filtrado por Fecha Incorrecta

**El endpoint `/api/facturas/failed` está filtrando por fecha de cuarentena, no por fecha de emisión.**

**Código actual:**
```python
# Filtra por fecha de cuarentena (cuando se movió a cuarentena)
quarantined_at = datetime.fromisoformat(quarantined_at_str).date()
if start_date <= quarantined_at <= end_date:
    # Incluir en resultados
```

**Problema:**
- Todas las facturas fueron puestas en cuarentena el **6 de noviembre de 2025**
- El dashboard está mostrando el mes de **noviembre**
- Por lo tanto, muestra **5 facturas** (todas las que están en cuarentena con fecha de hoy)

**Pero:**
- Estas facturas son de **julio 2025** (según su nombre y fecha de emisión)
- No deberían aparecer en el dashboard de noviembre

---

### 4. Problema con EVOLBE

**Archivo:** `Fact EVOLBE jul 25.pdf`
- **Tamaño:** 102,064 bytes (aparentemente válido)
- **MIME type:** `application/pdf`
- **Estado:** Marcado como "Archivo inválido o corrupto"

**Posibles causas:**
1. Error en la validación de PDF (`validate_pdf`)
2. El archivo puede tener un formato no estándar
3. Error en la conversión a imagen (pdf2image)

**Necesita investigación:**
- Verificar si el PDF es realmente válido
- Revisar el código de `validate_pdf` en `src/pdf_utils.py`
- Verificar si hay algún problema con la librería `pdf2image` o `python-magic`

---

### 5. Inconsistencias Identificadas

#### A. Filtrado de Facturas Fallidas

**Problema:** El endpoint filtra por fecha de cuarentena, no por fecha de emisión.

**Impacto:**
- Si una factura de julio se procesa en noviembre y falla, aparece en el dashboard de noviembre
- Esto es confuso porque el usuario espera ver facturas del mes seleccionado (julio), no del mes actual (noviembre)

**Solución propuesta:**
- Filtrar por fecha de emisión de la factura (si está disponible en metadatos)
- O filtrar por fecha de modificación del archivo en Drive
- O mostrar ambas fechas (emisión y cuarentena)

#### B. Facturas Duplicadas en Cuarentena

**Problema:** EVOLBE aparece 2 veces en cuarentena.

**Causa:**
- Fue procesada 2 veces (7:31 y 9:56)
- Ambas veces falló la validación
- Se crearon 2 archivos en cuarentena

**Solución propuesta:**
- Detectar duplicados antes de mover a cuarentena
- O consolidar archivos duplicados en la visualización

#### C. Errores de Base de Datos

**Problema:** 3 facturas fueron a cuarentena por errores de BD, no por problemas con el archivo.

**Facturas afectadas:**
1. NEGRINI: `importe_total` negativo (-58.30)
2. REVO 1: `importe_total` es NULL
3. REVO 2: `importe_total` es NULL

**Causa:**
- La validación de negocio permite estos valores
- Pero la BD tiene constraints que los rechazan

**Solución propuesta:**
- Validar constraints de BD antes de intentar insertar
- O ajustar la validación de negocio para rechazar estos casos

---

## 📊 Resumen de Inconsistencias

| Problema | Impacto | Prioridad |
|----------|---------|-----------|
| Filtrado por fecha de cuarentena (no emisión) | Dashboard muestra facturas del mes incorrecto | 🔴 Alta |
| EVOLBE marcada como corrupta (pero es válida) | Factura legible no se procesa | 🔴 Alta |
| Facturas duplicadas en cuarentena | Confusión en visualización | 🟡 Media |
| Errores de BD (importe_total NULL/negativo) | Facturas válidas rechazadas | 🟡 Media |

---

## 🎯 Recomendaciones

### 1. Corregir Filtrado de Facturas Fallidas

**Cambiar el endpoint `/api/facturas/failed` para filtrar por:**
- Fecha de emisión de la factura (si está disponible)
- O fecha de modificación del archivo en Drive
- Mostrar ambas fechas en el frontend

### 2. Investigar Validación de PDF

**Revisar `src/pdf_utils.py`:**
- Verificar por qué EVOLBE falla la validación
- Probar con diferentes métodos de validación
- Agregar logs más detallados

### 3. Mejorar Manejo de Errores de BD

**Validar constraints antes de insertar:**
- Verificar `importe_total > 0` antes de guardar
- Rechazar facturas con `importe_total` NULL
- Mover a cuarentena con razón específica

### 4. Detectar Duplicados en Cuarentena

**Antes de mover a cuarentena:**
- Verificar si ya existe un archivo con el mismo nombre
- Consolidar o actualizar en lugar de duplicar

---

## 📝 Notas Adicionales

- El usuario puede ver EVOLBE perfectamente en Drive
- El archivo no tiene contraseña
- El problema parece ser con la validación, no con el archivo en sí
- Necesita prueba manual del PDF para confirmar

---

**Estado:** 🔍 Investigación completada - Pendiente de correcciones

