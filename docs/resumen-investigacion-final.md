# Resumen Final: Investigación de Inconsistencias en Dashboard

**Fecha:** 6 de noviembre de 2025  
**Investigador:** Agente Arquitecto  
**Estado:** ✅ Investigación completada

---

## 🎯 Problema Reportado

El usuario reportó:
1. Dashboard muestra **5 facturas** en "Facturas No Procesadas" para **noviembre**
2. Factura **"Fact EVOLBE jul 25.pdf"** aparece como no procesada pero es legible en Drive
3. Inconsistencias entre datos procesados y datos mostrados

---

## 🔍 Hallazgos Principales

### 1. **Problema Crítico: Filtrado Incorrecto por Fecha**

**El endpoint `/api/facturas/failed` filtra por fecha de CUARENTENA, no por fecha de EMISIÓN.**

**Situación actual:**
- Todas las facturas fueron puestas en cuarentena el **6 de noviembre de 2025** (hoy)
- El dashboard está mostrando el mes de **noviembre**
- Por lo tanto, muestra **5 facturas** (todas las que están en cuarentena con fecha de hoy)

**Pero:**
- Estas facturas son de **julio 2025** (según su nombre y fecha de emisión)
- No deberían aparecer en el dashboard de noviembre

**Código problemático:**
```python
# En src/api/routes/facturas.py
quarantined_at = datetime.fromisoformat(quarantined_at_str).date()
if start_date <= quarantined_at <= end_date:  # ← Filtra por fecha de cuarentena
    # Incluir en resultados
```

**Impacto:** 🔴 **ALTO** - Dashboard muestra información incorrecta

---

### 2. **Problema con EVOLBE: Validación Incorrecta**

**Archivo:** `Fact EVOLBE jul 25.pdf`
- **Tamaño:** 102,064 bytes
- **Estado:** Marcado como "Archivo inválido o corrupto"
- **Realidad:** ✅ El PDF es **VÁLIDO** y se puede convertir a imagen sin problemas

**Pruebas realizadas:**
```python
# El PDF se convierte correctamente
images = convert_from_path(pdf_path, first_page=1, last_page=1)
# Resultado: ✅ 1 página convertida, dimensiones 1654x2339
```

**Causa del problema:**
- La función `validate_file_integrity` está fallando en la validación de magic bytes
- El archivo parece tener un formato no estándar o hay un problema con la lectura de bytes
- **Necesita investigación adicional** del código de validación

**Impacto:** 🔴 **ALTO** - Factura legible no se procesa

---

### 3. **Facturas en Cuarentena: Análisis Detallado**

**Total de archivos en cuarentena:** 5 archivos

| Archivo | Fecha Cuarentena | Razón | Tipo de Error |
|---------|------------------|-------|---------------|
| Fact EVOLBE jul 25.pdf | 2025-11-06 09:56:57 | "Archivo inválido o corrupto" | Validación PDF |
| Fact EVOLBE jul 25.pdf | 2025-11-06 07:31:24 | "Archivo inválido o corrupto" | Validación PDF (duplicado) |
| Fact NEGRINI del mercancía 3 jul 25.pdf | 2025-11-06 07:35:33 | `importe_total` negativo (-58.30) | Error BD - CheckViolation |
| Fact REVO 1 jul 25.pdf | 2025-11-06 07:40:04 | `importe_total` es NULL | Error BD - NotNullViolation |
| Fact REVO 2 jul 25.pdf | 2025-11-06 07:40:01 | `importe_total` es NULL | Error BD - NotNullViolation |

**Observaciones:**
- **EVOLBE aparece 2 veces** (fue procesada 2 veces, ambas fallaron)
- **3 facturas** fueron a cuarentena por **errores de BD**, no por problemas con el archivo
- Todas las facturas son de **julio 2025**, pero fueron procesadas/falladas en **noviembre**

---

### 4. **Datos en Base de Datos**

**Total de facturas en BD:** 4 facturas
- **Estado:** Todas con `estado = 'revisar'`
- **Distribución por mes:**
  - Julio 2025: 3 facturas ✅
  - Agosto 2025: 1 factura ✅
  - **Noviembre 2025: 0 facturas** ⚠️

**Facturas procesadas exitosamente (de la prueba de 5):**
1. ✅ Fact CONWAY JUL 25.pdf
2. ✅ Fact GIRO 1 jul 25.pdf
3. ✅ Fact HONORARIOS laboral jul 25.pdf
4. ✅ Fact CONWAY JULIO 25.pdf
5. ❌ Fact EVOLBE jul 25.pdf (marcada como corrupta)

---

## 📊 Resumen de Inconsistencias

| # | Problema | Impacto | Prioridad | Estado |
|---|----------|---------|-----------|--------|
| 1 | Filtrado por fecha de cuarentena (no emisión) | Dashboard muestra facturas del mes incorrecto | 🔴 Alta | ⚠️ Detectado |
| 2 | EVOLBE marcada como corrupta (pero es válida) | Factura legible no se procesa | 🔴 Alta | ⚠️ Detectado |
| 3 | Facturas duplicadas en cuarentena | Confusión en visualización | 🟡 Media | ⚠️ Detectado |
| 4 | Errores de BD (importe_total NULL/negativo) | Facturas válidas rechazadas | 🟡 Media | ⚠️ Detectado |

---

## 🎯 Recomendaciones Prioritarias

### 1. **Corregir Filtrado de Facturas Fallidas** (🔴 CRÍTICO)

**Cambiar el endpoint `/api/facturas/failed` para filtrar por:**
- Fecha de emisión de la factura (si está disponible en metadatos)
- O fecha de modificación del archivo en Drive (`file_info.modifiedTime`)
- Mostrar ambas fechas en el frontend (emisión y cuarentena)

**Código sugerido:**
```python
# Intentar obtener fecha de emisión del archivo
file_info = meta_data.get('file_info', {})
modified_time = file_info.get('modifiedTime')
if modified_time:
    # Parsear fecha de modificación de Drive
    file_date = datetime.fromisoformat(modified_time.replace('Z', '+00:00')).date()
    # Filtrar por fecha de archivo, no por fecha de cuarentena
    if start_date <= file_date <= end_date:
        # Incluir en resultados
```

### 2. **Investigar y Corregir Validación de PDF** (🔴 CRÍTICO)

**Revisar `src/pdf_utils.py` y `src/pipeline/validate.py`:**
- Verificar por qué EVOLBE falla la validación de magic bytes
- El archivo es válido (se puede convertir a imagen)
- Agregar logs más detallados
- Considerar validación alternativa (intentar convertir a imagen)

### 3. **Mejorar Manejo de Errores de BD** (🟡 MEDIA)

**Validar constraints antes de insertar:**
- Verificar `importe_total > 0` antes de guardar
- Rechazar facturas con `importe_total` NULL
- Mover a cuarentena con razón específica

### 4. **Detectar Duplicados en Cuarentena** (🟡 MEDIA)

**Antes de mover a cuarentena:**
- Verificar si ya existe un archivo con el mismo `drive_file_id`
- Consolidar o actualizar en lugar de duplicar

---

## 📝 Notas Adicionales

- El usuario puede ver EVOLBE perfectamente en Drive
- El archivo no tiene contraseña
- El problema parece ser con la validación, no con el archivo en sí
- El PDF se puede convertir a imagen sin problemas (1654x2339 píxeles)
- Necesita corrección del código de validación

---

## ✅ Próximos Pasos

1. **Corregir filtrado** en `/api/facturas/failed` para usar fecha de emisión/modificación
2. **Investigar validación de PDF** para EVOLBE
3. **Mejorar validación de BD** para evitar errores de constraints
4. **Probar con EVOLBE** después de correcciones

---

**Estado:** 🔍 Investigación completada - **Pendiente de correcciones**

**Archivos generados:**
- `docs/investigacion-inconsistencias-dashboard.md` (análisis detallado)
- `docs/resumen-investigacion-final.md` (este documento)

