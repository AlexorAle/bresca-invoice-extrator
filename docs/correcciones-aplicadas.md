# Correcciones Aplicadas - 6 de noviembre de 2025

## 🎯 Problemas Corregidos

### 1. ✅ Filtrado Incorrecto de Facturas Fallidas

**Problema:** El endpoint `/api/facturas/failed` filtraba por fecha de cuarentena, no por fecha de emisión del archivo.

**Solución:**
- Modificado `src/api/routes/facturas.py` para filtrar por fecha de modificación del archivo en Drive (`file_info.modifiedTime`)
- Si no está disponible, usa fecha de cuarentena como fallback
- Ahora el dashboard muestra facturas del mes correcto según la fecha del archivo

**Código modificado:**
```python
# Intentar obtener fecha de modificación del archivo en Drive (preferida)
modified_time = file_info.get('modifiedTime')
if modified_time:
    file_date = datetime.fromisoformat(modified_time.replace('Z', '+00:00')).date()
# Si no hay fecha de modificación, usar fecha de cuarentena como fallback
```

---

### 2. ✅ Validación de Tamaño de Archivo

**Problema:** `file_info.get('size')` desde Drive API viene como string, causando errores en la validación.

**Solución:**
- Modificado `src/pipeline/ingest.py` para convertir el tamaño a int antes de validar
- Maneja errores de conversión correctamente

**Código modificado:**
```python
# Convertir tamaño a int si viene como string desde Drive API
expected_size = file_info.get('size')
if expected_size is not None:
    try:
        expected_size = int(expected_size)
    except (ValueError, TypeError):
        expected_size = None
```

---

### 3. ✅ Validación de Importe Total para BD

**Problema:** Algunas facturas intentaban guardarse con `importe_total` NULL o negativo, causando errores de constraints en BD.

**Solución:**
- Agregada validación crítica en `src/pipeline/ingest.py` antes de intentar guardar
- Si `importe_total` es NULL o <= 0, la factura se mueve a cuarentena con razón específica
- Previene errores de BD antes de intentar insertar

**Código agregado:**
```python
# VALIDACIÓN CRÍTICA: Importe Total debe ser válido para BD
importe_total = factura_dto.get('importe_total')
if importe_total is None or (isinstance(importe_total, (int, float)) and importe_total <= 0):
    error_msg = f"importe_total inválido para BD: {importe_total} (debe ser > 0 y no NULL)"
    # Mover a cuarentena
```

---

## 🧹 Limpieza Realizada

### Base de Datos
- ✅ Eliminadas todas las facturas (4)
- ✅ Eliminados todos los eventos (18)
- ✅ Eliminados todos los proveedores (0)
- ✅ Eliminado SyncState (0)

### Carpetas
- ✅ Carpeta de cuarentena limpiada (0 archivos)
- ✅ Carpeta temporal limpiada (0 archivos)

---

## 📊 Estado Final

**Sistema completamente limpio y listo para nueva carga:**
- BD: 0 facturas, 0 eventos
- Cuarentena: 0 archivos
- Temp: 0 archivos

**Correcciones aplicadas:**
- ✅ Filtrado por fecha de archivo (no cuarentena)
- ✅ Validación de tamaño corregida
- ✅ Validación de importe_total antes de guardar

---

## 🎯 Próximos Pasos

1. **Ejecutar primera carga completa:**
   ```bash
   ./scripts/primera_carga.sh
   ```

2. **Verificar dashboard:**
   - Facturas fallidas deben aparecer en el mes correcto
   - No deben aparecer errores de BD por importe_total

3. **Monitorear:**
   - Validación de archivos
   - Errores de BD
   - Filtrado de facturas fallidas

---

**Estado:** ✅ Correcciones aplicadas y sistema limpio

