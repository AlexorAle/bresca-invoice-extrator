# Resumen Ejecutivo: Implementación de Edición Manual de Facturas Pendientes

## Objetivo
Permitir la edición manual de facturas que no pudieron ser procesadas automáticamente, completando los campos obligatorios y guardándolas en la base de datos.

## Componentes Implementados

### 1. Backend (Python/FastAPI)

#### Endpoint: `POST /api/facturas/manual-create`
- **Ubicación**: `src/api/routes/facturas.py`
- **Schema**: `ManualFacturaCreate` en `src/api/schemas/facturas.py`
- **Funcionalidad**:
  - Recibe datos de factura manual (proveedor, fechas, importes)
  - Valida campos obligatorios y cálculos
  - Busca factura existente por `drive_file_name`
  - **Si existe en estado 'error'/'revisar'**: Actualiza la factura existente
  - **Si existe en estado 'procesado'**: Rechaza (evita duplicados)
  - **Si no existe**: Crea nueva factura manual
  - Autocompleta campos: estado='procesado', fechas, extractor='manual', confianza=100

#### Validaciones Implementadas:
- Campos obligatorios: proveedor, fecha, importe_total, base_imponible, impuestos_total
- Valores positivos para importes
- Importe Total = Base Imponible + Impuestos Total (tolerancia ±0.01)
- IVA % entre 0 y 100 (se calcula automáticamente si no se proporciona)

### 2. Frontend (React)

#### Componente: `ManualInvoiceForm.jsx`
- **Ubicación**: `frontend/src/components/ManualInvoiceForm.jsx`
- **Tipo**: Modal (Dialog de Material-UI)
- **Funcionalidad**:
  - Formulario con campos obligatorios y opcionales
  - Validación en tiempo real
  - Cálculo automático de IVA %
  - Validación de importe total vs base + impuestos
  - Loading states durante guardado
  - Mensajes de error claros
  - Cierre automático después de guardar exitosamente

#### Integración en `FacturasTable.jsx`
- **Botón "Editar"**: Agregado en columna "Acciones" de tabla de pendientes
- **Estado**: Maneja factura seleccionada y apertura/cierre del modal
- **Callback**: `onRefresh` para actualizar tabla después de guardar

#### Función API: `createManualInvoice()`
- **Ubicación**: `frontend/src/utils/api.js`
- **Método**: POST a `/api/facturas/manual-create`
- **Manejo de errores**: Captura y muestra mensajes del servidor

### 3. Autocompletado Automático

Cuando se guarda una factura manualmente, el sistema completa automáticamente:

| Campo | Valor | Justificación |
|-------|-------|---------------|
| `estado` | `'procesado'` | Factura manual = procesada |
| `fecha_recepcion` | `datetime.utcnow()` | Fecha de carga manual |
| `creado_en` | `datetime.utcnow()` | Timestamp de creación |
| `actualizado_en` | `datetime.utcnow()` | Timestamp de actualización |
| `moneda` | `'EUR'` | Default del sistema |
| `extractor` | `'manual'` | Identificar origen manual |
| `confianza` | `'100'` | Manual = 100% confiable |
| `revision` | `1` | Primera versión |
| `drive_file_id` | `f"manual_{timestamp}_{hash}"` | ID único para facturas manuales |
| `drive_folder_name` | `'manual'` | Carpeta de origen |

### 4. Detección de Duplicados

- **Por `drive_file_name`**: El sistema verifica si ya existe una factura con el mismo nombre de archivo
- **Lógica**:
  - Si existe en estado 'error'/'revisar': Se actualiza (permite corregir)
  - Si existe en estado 'procesado': Se rechaza (evita duplicados)
  - Si no existe: Se crea nueva
- **Protección futura**: El pipeline automático detectará facturas manuales por `drive_file_name` y las omitirá

## Flujo de Usuario

1. Usuario accede a sección "Pendientes"
2. Ve tabla con facturas no procesadas (nombre y razón del error)
3. Hace clic en botón "Editar" de una factura
4. Se abre modal con formulario
5. Completa campos obligatorios:
   - Proveedor
   - Fecha de Emisión
   - Base Imponible
   - Impuestos Total
   - Importe Total
6. El sistema valida automáticamente:
   - Campos obligatorios completos
   - Importe Total = Base + Impuestos
   - Valores positivos
7. Usuario hace clic en "Guardar"
8. Backend procesa:
   - Busca factura existente
   - Actualiza o crea según corresponda
   - Autocompleta campos adicionales
9. Modal se cierra, tabla se actualiza
10. Factura desaparece de pendientes (ahora está procesada)

## Archivos Modificados/Creados

### Backend:
- `src/api/routes/facturas.py` - Nuevo endpoint `manual-create`
- `src/api/schemas/facturas.py` - Nuevo schema `ManualFacturaCreate`

### Frontend:
- `frontend/src/components/ManualInvoiceForm.jsx` - **NUEVO** componente modal
- `frontend/src/components/FacturasTable.jsx` - Agregado botón "Editar" y modal
- `frontend/src/utils/api.js` - Nueva función `createManualInvoice()`
- `frontend/src/admin/resources/reportes/ReportePendientes.jsx` - Agregado callback `onRefresh`

### Documentación:
- `docs/GUIA_EDICION_MANUAL_FACTURAS.md` - **NUEVO** guía completa para usuarios

## Testing

### Pruebas Recomendadas:
1. ✅ Crear factura manual nueva (no existe en BD)
2. ✅ Actualizar factura existente en estado 'error'
3. ✅ Rechazar factura ya procesada (duplicado)
4. ✅ Validar campos obligatorios
5. ✅ Validar cálculo de importes
6. ✅ Verificar autocompletado de campos
7. ✅ Verificar actualización de tabla después de guardar

## URLs de Prueba

- **Frontend**: http://82.25.101.32/invoice-dashboard/pendientes
- **Backend**: http://82.25.101.32/invoice-api/api/facturas/manual-create

## Estado de Despliegue

✅ Backend desplegado y funcionando
✅ Frontend desplegado y funcionando
✅ Documentación creada

## Próximos Pasos (Opcionales)

- [ ] Agregar visualización de PDF original en el modal
- [ ] Implementar búsqueda de proveedor por autocompletado
- [ ] Agregar historial de ediciones manuales
- [ ] Implementar exportación de facturas pendientes a CSV
