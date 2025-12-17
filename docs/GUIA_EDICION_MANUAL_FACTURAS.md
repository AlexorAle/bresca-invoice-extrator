# Guía de Usuario: Edición Manual de Facturas Pendientes

## Introducción

Esta guía explica cómo editar manualmente las facturas que no pudieron ser procesadas automáticamente por el sistema. Cuando una factura falla durante el procesamiento automático (por ejemplo, archivo corrupto, proveedor no encontrado, error de validación), aparece en la sección "Pendientes" y puede ser corregida manualmente.

---

## Flujo de Trabajo Completo

### 1. Acceder a la Sección de Facturas Pendientes

1. Desde el menú lateral izquierdo, haz clic en **"Pendientes"**
2. Se mostrará una tabla con todas las facturas que no pudieron ser procesadas automáticamente
3. Cada fila muestra:
   - **Nombre del archivo**: El nombre del PDF de la factura
   - **Motivo del error**: La razón por la cual no se pudo procesar (ej: "Archivo inválido o corrupto", "Nombre del proveedor no encontrado")
   - **Estado**: Marcado como "Pendiente" (indicador rojo)

### 2. Seleccionar una Factura para Editar

1. Revisa la lista de facturas pendientes
2. Identifica la factura que deseas corregir manualmente
3. Haz clic en el botón **"Editar"** ubicado en la columna "Acciones" de la fila correspondiente

### 3. Abrir el Formulario de Edición

1. Al hacer clic en "Editar", se abrirá un modal (ventana emergente) con el formulario de edición
2. En la parte superior del modal verás:
   - **Nombre del archivo**: El archivo PDF que no se pudo procesar
   - **Motivo del error**: La razón específica del fallo
3. El formulario contiene los siguientes campos:

#### Campos Obligatorios (marcados con *)

- **Proveedor** (*): Nombre del proveedor o emisor de la factura
  - Ejemplo: "NEGRINI S.L.", "REVO", "KLIMER"
  - Puedes escribir cualquier texto

- **Fecha de Emisión** (*): Fecha en que se emitió la factura
  - Formato: AAAA-MM-DD (ej: 2025-09-15)
  - Usa el selector de fecha para elegir la fecha

- **Base Imponible** (*): Importe sin impuestos
  - Ejemplo: 1020.30
  - Debe ser mayor que 0

- **Impuestos Total** (*): Total de impuestos (IVA)
  - Ejemplo: 214.26
  - No puede ser negativo

- **Importe Total** (*): Suma de base imponible + impuestos
  - Ejemplo: 1234.56
  - **Importante**: Debe ser igual a Base Imponible + Impuestos Total
  - El sistema valida automáticamente esta suma

#### Campos Opcionales

- **IVA %**: Porcentaje de IVA aplicado
  - Ejemplo: 21.0
  - Se calcula automáticamente cuando ingresas Base e Impuestos
  - Puedes editarlo manualmente si es necesario

- **Número de Factura**: Número o código de la factura
  - Ejemplo: "FAC-2025-001", "F25-000882"
  - Campo opcional

- **Moneda**: Moneda de la factura
  - Opciones: EUR (Euro), USD (Dólar), GBP (Libra)
  - Por defecto: EUR

### 4. Completar los Campos del Formulario

1. **Proveedor**: Escribe el nombre completo del proveedor tal como aparece en la factura
2. **Fecha de Emisión**: Selecciona la fecha usando el selector de fecha
3. **Base Imponible**: Ingresa el importe sin impuestos (puede tener decimales)
4. **Impuestos Total**: Ingresa el total de impuestos (IVA)
5. **Importe Total**: Ingresa el importe total de la factura
   - **Nota**: El sistema verificará que Importe Total = Base Imponible + Impuestos Total
   - Si hay una diferencia mayor a 0.01, mostrará un error
6. **IVA %**: Se calcula automáticamente, pero puedes ajustarlo si es necesario
7. **Número de Factura**: Opcional, ingresa si lo conoces
8. **Moneda**: Selecciona la moneda (por defecto EUR)

### 5. Validar y Guardar

1. El sistema valida automáticamente:
   - Que todos los campos obligatorios estén completos
   - Que los valores numéricos sean positivos
   - Que el Importe Total coincida con Base + Impuestos
2. Si hay errores, aparecerán mensajes en rojo debajo de cada campo
3. Corrige los errores antes de continuar
4. Una vez que todos los campos son válidos, haz clic en el botón **"Guardar"** (ubicado en la esquina inferior derecha del modal)
5. El botón mostrará "Guardando..." mientras se procesa la solicitud

### 6. Confirmación y Actualización

1. Si la factura se guarda exitosamente:
   - El modal se cerrará automáticamente
   - La tabla de facturas pendientes se actualizará
   - La factura editada **desaparecerá** de la lista de pendientes
   - La factura ahora aparecerá como "procesada" en el sistema

2. Si hay un error al guardar:
   - Se mostrará un mensaje de error en rojo en la parte superior del formulario
   - Revisa el mensaje y corrige el problema
   - Intenta guardar nuevamente

### 7. Verificación de Duplicados

El sistema verifica automáticamente si la factura ya existe en la base de datos:

- **Si la factura existe y está en estado 'error' o 'revisar'**: Se actualizará con los nuevos datos manuales
- **Si la factura existe y ya está 'procesada'**: Se mostrará un error indicando que no se puede crear un duplicado
- **Si la factura no existe**: Se creará una nueva entrada en la base de datos

### 8. Protección contra Duplicados Futuros

Una vez que una factura ha sido guardada manualmente:

- Si el mismo archivo se escanea nuevamente en el futuro, el sistema lo detectará como duplicado
- El archivo será omitido automáticamente durante el procesamiento
- No se creará una factura duplicada

---

## Ejemplo Práctico

### Escenario: Factura con Proveedor No Encontrado

1. **Situación inicial**:
   - Archivo: "Fact NEGRINI sep 25.pdf"
   - Error: "Nombre del proveedor/emisor no encontrado en la factura"
   - Estado: Pendiente

2. **Acción del usuario**:
   - Hace clic en "Editar"
   - Completa el formulario:
     - Proveedor: "NEGRINI S.L."
     - Fecha: 2025-09-15
     - Base Imponible: 1020.30
     - Impuestos: 214.26
     - Importe Total: 1234.56
     - IVA %: 21.0 (calculado automáticamente)
   - Hace clic en "Guardar"

3. **Resultado**:
   - La factura se guarda exitosamente
   - Desaparece de la lista de pendientes
   - Aparece como procesada en el sistema
   - Si el mismo archivo se escanea nuevamente, será omitido como duplicado

---

## Campos Autocompletados Automáticamente

El sistema completa automáticamente los siguientes campos cuando guardas una factura manualmente:

- **Estado**: Se marca como "procesado"
- **Fecha de Recepción**: Fecha y hora actual
- **Fecha de Creación**: Fecha y hora actual
- **Fecha de Actualización**: Fecha y hora actual
- **Extractor**: Se marca como "manual"
- **Confianza**: Se establece en 100% (por ser entrada manual)
- **Moneda**: EUR (si no se especifica otra)
- **Revisión**: 1 (primera versión)

---

## Consejos y Mejores Prácticas

1. **Revisa el motivo del error**: Antes de editar, lee el "Motivo del error" para entender qué falló
2. **Verifica los cálculos**: Asegúrate de que Importe Total = Base Imponible + Impuestos
3. **Usa nombres consistentes**: Escribe el nombre del proveedor de forma consistente (ej: siempre "NEGRINI S.L." y no "Negrini" o "NEGRINI SL")
4. **Completa el número de factura si es posible**: Ayuda a identificar facturas duplicadas en el futuro
5. **Guarda solo cuando estés seguro**: Una vez guardada, la factura se procesa y no se puede deshacer fácilmente

---

## Solución de Problemas

### Error: "El importe total debe ser igual a base + impuestos"

**Causa**: Los valores no coinciden exactamente.

**Solución**: 
- Verifica que Importe Total = Base Imponible + Impuestos Total
- Ajusta uno de los valores para que coincidan
- El sistema permite diferencias de hasta 0.01 por redondeo

### Error: "La factura ya fue procesada correctamente"

**Causa**: Ya existe una factura con el mismo nombre de archivo en estado 'procesado'.

**Solución**: 
- No es necesario crear esta factura manualmente
- La factura ya está en el sistema
- Si necesitas corregir datos, contacta al administrador

### Error: "El proveedor es obligatorio"

**Causa**: El campo Proveedor está vacío.

**Solución**: 
- Completa el campo "Proveedor" con el nombre del proveedor
- Puede ser cualquier texto

### El modal no se cierra después de guardar

**Causa**: Puede haber un error de conexión o validación.

**Solución**: 
- Revisa el mensaje de error en la parte superior del modal
- Verifica tu conexión a internet
- Intenta guardar nuevamente

---

## Preguntas Frecuentes

**P: ¿Puedo editar múltiples facturas a la vez?**  
R: No, solo puedes editar una factura a la vez. Completa y guarda una antes de editar la siguiente.

**P: ¿Qué pasa si cometo un error al guardar?**  
R: Puedes editar la factura nuevamente si está en estado 'error' o 'revisar'. Si ya está 'procesada', contacta al administrador.

**P: ¿Puedo ver el PDF original de la factura?**  
R: Actualmente no está disponible en el modal, pero puedes acceder al archivo desde el sistema de archivos si tienes permisos.

**P: ¿Los datos se guardan automáticamente?**  
R: No, debes hacer clic en "Guardar" para que los cambios se apliquen.

**P: ¿Qué pasa si cierro el modal sin guardar?**  
R: Los cambios no se guardarán. Debes hacer clic en "Guardar" antes de cerrar.

---

## Soporte

Si encuentras problemas o tienes preguntas sobre la edición manual de facturas, contacta al administrador del sistema.

---

**Última actualización**: Noviembre 2025

