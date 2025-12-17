# Resumen Ejecutivo - Limpieza Completa de Base de Datos

**Fecha**: 2025-11-18  
**Estado**: ✅ COMPLETADO

---

## Objetivo

Limpiar completamente todas las tablas de la base de datos y archivos de cuarentena para preparar una carga nueva desde las carpetas "facturas 2024" y "facturas 2025" de Google Drive.

---

## Resultados de la Limpieza

### Base de Datos

| Tabla | Registros Eliminados | Estado |
|-------|---------------------|--------|
| `facturas` | 409 | ✅ Limpia |
| `proveedores` | 88 | ✅ Limpia |
| `ingest_events` | 15,374 | ✅ Limpia |
| `sync_state` | 1 | ✅ Limpia |
| **TOTAL** | **15,872** | ✅ **COMPLETO** |

### Archivos de Cuarentena

- **Ubicación**: `data/quarantine`
- **Archivos eliminados**: Todos los archivos en cuarentena
- **Estado**: ✅ Limpio

---

## Estado Final

✅ **Base de datos completamente limpia**  
✅ **Archivos de cuarentena eliminados**  
✅ **Sistema listo para nueva carga**

---

## Próximos Pasos - Configuración de Nuevas Carpetas

### 1. Obtener IDs de las Nuevas Carpetas en Google Drive

Necesitas obtener los **Folder IDs** de:
- `facturas 2024`
- `facturas 2025`

**Cómo obtener el Folder ID:**
1. Abre Google Drive en el navegador
2. Navega a la carpeta (ej: "facturas 2024")
3. Abre la URL en la barra de direcciones
4. El ID es la parte después de `/folders/` en la URL
   - Ejemplo: `https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j`
   - ID: `1a2b3c4d5e6f7g8h9i0j`

### 2. Opciones de Configuración

#### Opción A: Carpeta Base con Subcarpetas (Recomendada) ⭐

**Configuración:**
- Crear una carpeta padre en Google Drive (ej: "Facturas Totales")
- Mover o crear dentro de ella las carpetas "facturas 2024" y "facturas 2025"
- Configurar `GOOGLE_DRIVE_FOLDER_ID` con el ID de la carpeta padre

**Ventajas:**
- ✅ Una sola configuración
- ✅ El sistema busca automáticamente en ambas carpetas recursivamente
- ✅ No requiere modificación de código
- ✅ Fácil de mantener

**Pasos:**
1. Crear carpeta padre en Drive (si no existe)
2. Asegurar que "facturas 2024" y "facturas 2025" estén dentro
3. Obtener el ID de la carpeta padre
4. Actualizar `.env`:
   ```bash
   GOOGLE_DRIVE_FOLDER_ID=<ID_de_carpeta_padre>
   ```

#### Opción B: Múltiples Carpetas (Requiere Modificación de Código)

**Configuración:**
- Modificar el código para soportar múltiples `GOOGLE_DRIVE_FOLDER_ID`
- Procesar cada carpeta por separado

**Ventajas:**
- ✅ Control granular sobre qué carpetas procesar
- ✅ Permite procesar carpetas en ubicaciones diferentes

**Desventajas:**
- ❌ Requiere modificación de código
- ❌ Más complejo de mantener

**Si eliges esta opción**, necesitarás:
1. Modificar `src/main.py` para soportar múltiples folder IDs
2. Actualizar `.env`:
   ```bash
   GOOGLE_DRIVE_FOLDER_ID_2024=<ID_facturas_2024>
   GOOGLE_DRIVE_FOLDER_ID_2025=<ID_facturas_2025>
   ```

### 3. Cómo Funciona el Sistema Actual

El código actual usa el método `list_all_pdfs_recursive()` que:

1. **Toma un folder ID base** (desde `GOOGLE_DRIVE_FOLDER_ID`)
2. **Busca recursivamente** todas las carpetas dentro de esa carpeta base
3. **Lista todos los PDFs** encontrados en todas las subcarpetas
4. **No depende de nombres específicos** de carpetas

**Esto significa que:**
- Si configuras una carpeta padre que contiene "facturas 2024" y "facturas 2025", el sistema las encontrará automáticamente
- No necesitas modificar código si las carpetas están dentro de una carpeta padre común

### 4. Verificación Después de Configurar

1. **Ejecutar en modo `--dry-run`** para verificar que encuentra los archivos:
   ```bash
   docker exec invoice-backend python3 /app/src/main.py --dry-run
   ```

2. **Verificar que los archivos encontrados** pertenecen a las carpetas correctas:
   - Revisar los logs para ver qué archivos se encontraron
   - Verificar que aparecen archivos de ambas carpetas (2024 y 2025)

3. **Proceder con la carga completa**:
   ```bash
   docker exec invoice-backend python3 /app/src/main.py
   ```

---

## Notas Importantes

⚠️ **Backup**: La limpieza se ejecutó sin crear backup previo. Si necesitas recuperar datos, deberás usar backups anteriores.

⚠️ **Carpetas de Drive**: Asegúrate de tener acceso a las nuevas carpetas con las credenciales configuradas en `GOOGLE_SERVICE_ACCOUNT_FILE`.

⚠️ **Permisos**: Verifica que el servicio account de Google Drive tenga permisos de lectura en las nuevas carpetas.

⚠️ **Estructura de Carpetas**: Si las carpetas "facturas 2024" y "facturas 2025" están en ubicaciones diferentes (no comparten carpeta padre), necesitarás usar la Opción B o reorganizar las carpetas en Drive.

---

## Resumen de Cambios Necesarios

### Si eliges Opción A (Recomendada):

1. ✅ Crear carpeta padre en Drive (si no existe)
2. ✅ Mover/crear "facturas 2024" y "facturas 2025" dentro de la carpeta padre
3. ✅ Obtener ID de la carpeta padre
4. ✅ Actualizar `.env` con `GOOGLE_DRIVE_FOLDER_ID=<ID_carpeta_padre>`
5. ✅ Verificar con `--dry-run`
6. ✅ Ejecutar carga completa

### Si eliges Opción B:

1. ⚠️ Modificar `src/main.py` para soportar múltiples folder IDs
2. ⚠️ Actualizar `.env` con `GOOGLE_DRIVE_FOLDER_ID_2024` y `GOOGLE_DRIVE_FOLDER_ID_2025`
3. ✅ Verificar con `--dry-run`
4. ✅ Ejecutar carga completa

---

## Archivos Creados

- `scripts/limpiar_bd.py`: Script de limpieza de base de datos
- `docs/RESUMEN_LIMPIEZA_BD.md`: Documentación técnica detallada
- `docs/RESUMEN_EJECUTIVO_LIMPIEZA.md`: Este documento

---

**Sistema listo para nueva carga** 🚀

