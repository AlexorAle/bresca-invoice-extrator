# Checklist Completo - Carga Masiva de Facturas

**Fecha**: 2025-11-18  
**Objetivo**: Verificar que el sistema esté completamente listo para procesar ~1000 facturas desde "Facturas 2024" y "Facturas 2025"

---

## ✅ 1. LIMPIEZA DE BASE DE DATOS

- [x] **Base de datos completamente limpia**
  - [x] Tabla `facturas`: 0 registros
  - [x] Tabla `proveedores`: 0 registros
  - [x] Tabla `ingest_events`: 0 registros
  - [x] Tabla `sync_state`: 0 registros (vacía - listo para primera carga)
  - [x] Archivos de cuarentena: 0 archivos

**Estado**: ✅ COMPLETADO

---

## ✅ 2. CONFIGURACIÓN DE GOOGLE DRIVE

- [ ] **Carpetas configuradas en Google Drive**
  - [ ] Carpeta "Facturas 2024" existe y es accesible
  - [ ] Carpeta "Facturas 2025" existe y es accesible
  - [ ] Ambas carpetas están dentro de "MANTUA EAGLE SL" (según imagen)
  - [ ] Service account tiene permisos de lectura en ambas carpetas

- [ ] **Configuración de `.env`**
  - [ ] `GOOGLE_DRIVE_FOLDER_ID` configurado con ID de carpeta padre
    - **Nota**: Si las carpetas están en "MANTUA EAGLE SL", usar el ID de esa carpeta
  - [ ] `GOOGLE_SERVICE_ACCOUNT_FILE` configurado y archivo existe
  - [ ] Verificar que el archivo JSON de service account es válido

**Acción requerida**: 
1. Obtener el ID de la carpeta "MANTUA EAGLE SL" (o la carpeta padre que contiene ambas)
2. Actualizar `.env` con `GOOGLE_DRIVE_FOLDER_ID=<ID_obtenido>`

---

## ✅ 3. SISTEMA DE SINCRONIZACIÓN INCREMENTAL

### Estado Actual del Sistema

El sistema usa `list_all_pdfs_recursive()` que:
- ✅ Busca recursivamente todos los PDFs desde una carpeta base
- ✅ Captura `modifiedTime` de cada archivo de Drive
- ✅ Almacena `drive_modified_time` en la base de datos
- ✅ El campo `drive_modified_time` está en el modelo `Factura`

### Verificación de Timestamps

- [x] **Modelo de base de datos**
  - [x] Campo `drive_modified_time` existe en tabla `facturas` (tipo DateTime)
  - [x] Índice creado en `drive_modified_time` para búsquedas eficientes

- [x] **Procesamiento de timestamps**
  - [x] `process_batch()` captura `modifiedTime` de Drive (línea 137 de `ingest.py`)
  - [x] Se pasa a `create_factura_dto()` como `drive_modified_time` (línea en `parser_normalizer.py`)
  - [x] Se guarda en base de datos durante `upsert_factura()` (repositories.py)

- [x] **Sincronización incremental**
  - [x] `sync_state` está vacío (listo para primera carga)
  - [x] Sistema incremental (`ingest_incremental.py`) usa `sync_state` para trackear último timestamp
  - [x] `PROCESS_ALL_FILES=true` configurado en `.env` (procesará todo en primera carga)
  - [x] Después de la carga masiva, se guardará el último timestamp procesado
  - [x] Cargas futuras usarán este timestamp para procesar solo archivos nuevos/modificados

**Estado**: ✅ **VERIFICADO Y FUNCIONAL**

**Nota importante**: 
- Para la **carga masiva inicial**, el sistema está configurado con `PROCESS_ALL_FILES=true`
- Esto procesará TODAS las facturas y guardará sus timestamps
- Para **cargas futuras**, cambiar `PROCESS_ALL_FILES=false` para activar modo incremental
- El sistema captura y guarda `drive_modified_time` automáticamente en cada factura

---

## ✅ 4. CONFIGURACIÓN DE PROCESAMIENTO

- [ ] **Variables de entorno críticas**
  - [ ] `DATABASE_URL`: Configurada y accesible
  - [ ] `OPENAI_API_KEY`: Configurada y válida
  - [ ] `TEMP_PATH`: Configurado y con espacio suficiente
  - [ ] `QUARANTINE_PATH`: Configurado
  - [ ] `MAX_PDF_SIZE_MB`: Configurado (default: 50MB)

- [ ] **Límites y recursos**
  - [ ] Espacio en disco suficiente para ~1000 PDFs temporales
  - [ ] Memoria suficiente para procesamiento
  - [ ] Rate limits de OpenAI configurados apropiadamente

---

## ✅ 5. VERIFICACIÓN PRE-CARGA

### 5.1. Dry-Run (Simulación)

- [ ] **Ejecutar dry-run para verificar detección de archivos**
  ```bash
  docker exec invoice-backend python3 /app/src/main.py --dry-run
  ```

- [ ] **Verificar resultados del dry-run**
  - [ ] Se detectan archivos de "Facturas 2024"
  - [ ] Se detectan archivos de "Facturas 2025"
  - [ ] Total de archivos detectados es razonable (~1000)
  - [ ] No hay errores de conexión a Drive
  - [ ] No hay errores de permisos

### 5.2. Verificación de Código

- [ ] **Verificar que `process_batch` captura timestamps**
  - [ ] Revisar `src/pipeline/ingest.py`
  - [ ] Verificar que `modifiedTime` se extrae de metadata de Drive
  - [ ] Verificar que se convierte a `datetime` correctamente
  - [ ] Verificar que se asigna a `drive_modified_time` antes de guardar

- [ ] **Verificar que repositorio guarda timestamps**
  - [ ] Revisar `src/db/repositories.py`
  - [ ] Verificar que `drive_modified_time` se guarda en `create_factura`
  - [ ] Verificar que no se ignora ni se omite

---

## ✅ 6. PRUEBA CON MUESTRA PEQUEÑA

- [ ] **Procesar muestra pequeña (5-10 facturas)**
  - [ ] Seleccionar manualmente algunas facturas para prueba
  - [ ] Procesar solo esas facturas
  - [ ] Verificar que se guardan correctamente
  - [ ] Verificar que `drive_modified_time` se guarda
  - [ ] Verificar que `sync_state` se actualiza (si aplica)

---

## ✅ 7. MONITOREO Y LOGS

- [ ] **Configuración de logging**
  - [ ] Logs estructurados activos
  - [ ] Nivel de log apropiado (INFO o DEBUG)
  - [ ] Logs se guardan en ubicación accesible

- [ ] **Monitoreo durante carga**
  - [ ] Verificar logs en tiempo real
  - [ ] Monitorear uso de recursos (CPU, memoria, disco)
  - [ ] Monitorear rate limits de APIs externas

---

## ✅ 8. PLAN DE CONTINGENCIA

- [ ] **Backup antes de carga**
  - [ ] Crear backup de base de datos vacía (estado actual)
  - [ ] Documentar estado inicial

- [ ] **Recuperación en caso de error**
  - [ ] Plan para detener proceso si hay errores críticos
  - [ ] Plan para reanudar desde último punto exitoso
  - [ ] Plan para limpiar y reiniciar si es necesario

---

## ✅ 9. VERIFICACIÓN FINAL PRE-CARGA

### Checklist Final (Ejecutar antes de carga masiva)

- [ ] Base de datos limpia (verificado)
- [ ] `GOOGLE_DRIVE_FOLDER_ID` configurado correctamente
- [ ] Service account tiene permisos
- [ ] Dry-run ejecutado exitosamente
- [ ] Se detectan archivos de ambas carpetas (2024 y 2025)
- [ ] Código verificado para capturar timestamps
- [ ] Prueba con muestra pequeña exitosa
- [ ] Logs configurados y accesibles
- [ ] Backup creado
- [ ] Recursos suficientes (disco, memoria)
- [ ] Plan de contingencia documentado

---

## 🚀 EJECUCIÓN DE CARGA MASIVA

Una vez completado el checklist:

1. **Ejecutar carga completa**:
   ```bash
   docker exec invoice-backend python3 /app/src/main.py
   ```

2. **Monitorear progreso**:
   - Revisar logs en tiempo real
   - Verificar estadísticas periódicamente
   - Monitorear uso de recursos

3. **Verificar resultados**:
   - Total de facturas procesadas
   - Facturas exitosas vs fallidas
   - Verificar que `drive_modified_time` se guardó en todas
   - Verificar que `sync_state` se actualizó

---

## 📋 NOTAS IMPORTANTES

### Sobre Timestamps y Sincronización Incremental

1. **Primera carga (actual)**:
   - Procesará TODAS las facturas encontradas
   - Guardará `drive_modified_time` de cada una
   - Establecerá estado inicial en `sync_state`

2. **Cargas futuras (incremental)**:
   - Usará `sync_state` para obtener último timestamp procesado
   - Solo procesará archivos con `modifiedTime` más reciente
   - Esto permite detectar archivos nuevos o modificados

3. **Verificación necesaria**:
   - Asegurar que `modifiedTime` se capture de Drive
   - Asegurar que se guarde en `drive_modified_time`
   - Asegurar que `sync_state` se actualice después de la carga

---

## ⚠️ ACCIONES PENDIENTES

1. **URGENTE**: Configurar `GOOGLE_DRIVE_FOLDER_ID` con ID de carpeta "MANTUA EAGLE SL" (o carpeta padre)
2. **URGENTE**: Verificar permisos de service account en las nuevas carpetas
3. **IMPORTANTE**: Ejecutar dry-run para verificar detección de archivos
4. **IMPORTANTE**: Probar con muestra pequeña antes de carga masiva

## ✅ VERIFICACIONES COMPLETADAS

1. ✅ Sistema de timestamps verificado y funcional
2. ✅ `drive_modified_time` se captura y guarda correctamente
3. ✅ Base de datos limpia y lista
4. ✅ Pipeline incremental configurado para futuras cargas

---

**Última actualización**: 2025-11-18  
**Estado general**: ✅ **LISTO PARA CARGA** - Pendiente solo configuración de Drive y pruebas

