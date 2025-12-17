# Resumen Ejecutivo - Limpieza de Base de Datos

## Fecha: $(date +"%Y-%m-%d %H:%M:%S")

## Objetivo
Limpiar completamente todas las tablas de la base de datos y archivos de cuarentena para preparar una carga nueva desde las carpetas "facturas 2024" y "facturas 2025" de Google Drive.

## Tablas Limpiadas

### 1. `facturas`
- **Descripción**: Tabla principal que almacena todas las facturas procesadas
- **Registros eliminados**: Ver logs de ejecución

### 2. `proveedores`
- **Descripción**: Tabla de proveedores/emisores de facturas
- **Registros eliminados**: Ver logs de ejecución

### 3. `ingest_events`
- **Descripción**: Tabla de eventos de ingesta/procesamiento
- **Registros eliminados**: Ver logs de ejecución

### 4. `sync_state`
- **Descripción**: Tabla de estado de sincronización con Google Drive
- **Registros eliminados**: Ver logs de ejecución

## Archivos de Cuarentena

- **Ubicación**: `data/quarantine` (configurable via `QUARANTINE_PATH`)
- **Archivos eliminados**: Ver logs de ejecución

## Estado Final

✅ **Base de datos completamente limpia**
✅ **Archivos de cuarentena eliminados**
✅ **Sistema listo para nueva carga**

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

#### Opción A: Carpeta Base con Subcarpetas (Recomendada)
- Configurar `GOOGLE_DRIVE_FOLDER_ID` con el ID de una carpeta padre que contenga ambas subcarpetas
- El sistema buscará recursivamente en todas las subcarpetas
- **Ventaja**: Una sola configuración, busca automáticamente en ambas carpetas

#### Opción B: Múltiples Carpetas (Requiere Modificación)
- Modificar el código para soportar múltiples `GOOGLE_DRIVE_FOLDER_ID`
- Procesar cada carpeta por separado
- **Ventaja**: Control granular sobre qué carpetas procesar

### 3. Cambios Necesarios en el Código

El código actual usa `list_all_pdfs_recursive()` que busca recursivamente desde una carpeta base. 

**Si las carpetas están en diferentes ubicaciones**, necesitarás:

1. **Modificar `src/main.py`**:
   - Agregar soporte para múltiples folder IDs
   - O configurar una carpeta padre que contenga ambas

2. **Actualizar `.env`**:
   ```bash
   # Opción A: Carpeta padre que contiene ambas
   GOOGLE_DRIVE_FOLDER_ID=<ID_de_carpeta_padre>
   
   # Opción B: Múltiples IDs (requiere modificación de código)
   GOOGLE_DRIVE_FOLDER_ID_2024=<ID_facturas_2024>
   GOOGLE_DRIVE_FOLDER_ID_2025=<ID_facturas_2025>
   ```

### 4. Verificación

Después de configurar:
1. Ejecutar en modo `--dry-run` para verificar que encuentra los archivos:
   ```bash
   python src/main.py --dry-run
   ```
2. Verificar que los archivos encontrados pertenecen a las carpetas correctas
3. Proceder con la carga completa

## Notas Importantes

⚠️ **Backup**: Se recomienda crear un backup antes de la limpieza (ya ejecutado)

⚠️ **Carpetas de Drive**: Asegúrate de tener acceso a las nuevas carpetas con las credenciales configuradas

⚠️ **Permisos**: Verifica que el servicio account de Google Drive tenga permisos en las nuevas carpetas

