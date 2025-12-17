# Guía de Secciones del Sistema de Gestión de Facturas

## Descripción General

Sistema integral de gestión y procesamiento automático de facturas que permite importar, procesar, analizar y gestionar facturas de forma centralizada y eficiente.

---

## 📊 Dashboard

**¿Qué es?**  
Vista principal del sistema que proporciona una panorámica completa del estado de las facturas y métricas clave del negocio.

**¿Para qué sirve?**  
- Visualizar el estado general de las facturas procesadas
- Consultar métricas financieras clave (total facturado, impuestos, etc.)
- Ver el resumen de facturas por categoría
- Acceder rápidamente a las facturas más recientes
- Exportar datos a Excel para análisis externos

**Características principales:**
- **KPIs en tiempo real**: Total facturado, base imponible, impuestos, número de facturas
- **Gráficos por categoría**: Distribución visual de gastos por tipo de proveedor
- **Tabla de facturas recientes**: Últimas facturas procesadas con información resumida
- **Filtros por mes y año**: Análisis temporal de los datos
- **Exportación a Excel**: Descarga de reportes completos para análisis detallado

**Cuándo usarlo:**  
Ideal para comenzar cada sesión de trabajo, obtener una visión general rápida del estado financiero y tomar decisiones basadas en datos actualizados.

---

## ⚠️ Pendientes

**¿Qué es?**  
Sección dedicada a identificar y gestionar facturas que requieren atención, revisión o corrección antes de ser procesadas completamente.

**¿Para qué sirve?**  
- Identificar facturas con errores de procesamiento
- Revisar facturas que no pudieron ser procesadas automáticamente
- Gestionar facturas en cuarentena (archivos con problemas de formato o contenido)
- Exportar listado de pendientes para revisión externa
- Priorizar la corrección de facturas críticas

**Características principales:**
- **Listado completo de pendientes**: Todas las facturas que requieren atención
- **Información detallada**: Nombre de archivo, proveedor, categoría, importes
- **Estados claros**: Identificación de errores, cuarentena o problemas de procesamiento
- **Exportación a Excel**: Generación de reporte completo para seguimiento externo
- **Filtros y búsqueda**: Localización rápida de facturas específicas

**Cuándo usarlo:**  
Diariamente para revisar y resolver facturas con problemas, asegurando que todas las facturas sean procesadas correctamente y no queden pendientes sin atención.

---

## 📈 Reportes

**¿Qué es?**  
Módulo de generación de informes y análisis detallados sobre las facturas procesadas, con múltiples opciones de visualización y exportación, incluyendo análisis de rentabilidad.

**¿Para qué sirve?**  
- Generar reportes personalizados por período
- Analizar tendencias de gastos y facturación
- Realizar análisis de rentabilidad mensual
- Exportar datos para análisis financiero externo
- Crear informes para contabilidad o auditoría
- Visualizar estadísticas históricas
- Comparar ingresos vs gastos por mes

**Características principales:**
- **Múltiples formatos de exportación**: Excel, CSV y otros formatos estándar
- **Filtros avanzados**: Por fecha, proveedor, categoría, estado
- **Análisis comparativo**: Comparación entre períodos
- **Gráficos y visualizaciones**: Representación gráfica de los datos con gráficos de barras
- **Análisis de Rentabilidad**: 
  - KPIs de rentabilidad (margen bruto, margen neto, porcentaje de rentabilidad)
  - Gráfico comparativo de ingresos vs gastos por mes
  - Tabla mensual con edición inline de ingresos
  - Cálculo automático de rentabilidad
- **Reportes por categoría**: Análisis de gastos por tipo de proveedor
- **Reportes por proveedor**: Estadísticas detalladas por proveedor
- **Selector de año**: Filtrar reportes por año específico

**Cuándo usarlo:**  
Al finalizar períodos contables, para auditorías, análisis mensuales, evaluación de rentabilidad del negocio, o cuando se necesite información consolidada para toma de decisiones estratégicas.

---

## 🧾 Facturas

**¿Qué es?**  
Gestión completa del catálogo de facturas procesadas, con acceso detallado a cada factura individual y capacidades de búsqueda y filtrado avanzadas.

**Estado actual:**  
Esta sección está temporalmente oculta en el menú principal, pero las facturas se pueden visualizar y gestionar desde el Dashboard principal.

**¿Para qué sirve?**  
- Consultar el historial completo de facturas
- Buscar facturas específicas por múltiples criterios
- Ver detalles completos de cada factura procesada
- Filtrar facturas por mes, año, proveedor o categoría
- Verificar información extraída automáticamente de cada factura

**Características principales:**
- **Vista de lista completa**: Todas las facturas con información resumida (disponible en Dashboard)
- **Vista detallada**: Información completa de cada factura
- **Búsqueda avanzada**: Por proveedor, fecha, importe, número de factura
- **Filtros múltiples**: Combinación de criterios para búsquedas precisas (estado, fecha, importe)
- **Información extraída**: Datos automáticamente capturados (proveedor, importes, fechas, NIF/CIF)
- **Chips de estado**: Indicadores visuales de estado (procesada/pendiente)

**Cuándo usarlo:**  
Para consultas específicas sobre facturas, verificación de datos, búsqueda de facturas particulares o revisión del historial completo de facturación. Actualmente accesible desde el Dashboard principal.

---

## 👥 Proveedores

**¿Qué es?**  
Centro de gestión de proveedores, donde se administra la información de todos los proveedores, se normalizan nombres duplicados y se categorizan para mejor organización.

**¿Para qué sirve?**  
- Ver el listado completo de proveedores únicos
- Asignar categorías a proveedores (las categorías se gestionan en la sección "Datos" → Tab "Categorías")
- Editar información de proveedores (NIF/CIF, email de contacto, categoría)
- Filtrar proveedores por letra inicial (A-Z)
- Filtrar proveedores por categoría
- Consultar estadísticas por proveedor (total facturado, número de facturas)
- Identificar y gestionar proveedores duplicados

**Características principales:**
- **Listado normalizado**: Proveedores únicos sin duplicados
- **Filtro alfabético**: Navegación rápida por letra inicial (A-Z)
- **Filtro por categoría**: Filtrar proveedores según su categoría asignada
- **Categorización visual**: Chips de colores que muestran la categoría de cada proveedor
- **Estadísticas por proveedor**: Total facturado y número de facturas asociadas
- **Búsqueda avanzada**: Localización rápida de proveedores específicos por nombre
- **Edición de datos**: Actualización de NIF/CIF, datos de contacto y categoría mediante formulario de edición
- **Iconos por categoría**: Cada categoría tiene un icono visual distintivo

**Cuándo usarlo:**  
Para mantener la base de datos de proveedores actualizada, organizar proveedores por categorías, corregir información incorrecta, asignar categorías a proveedores nuevos o consultar estadísticas de gastos por proveedor.

---

## 📤 Datos

**¿Qué es?**  
Panel de monitoreo y gestión del sistema con dos secciones principales: estadísticas de sincronización y gestión de categorías.

**¿Para qué sirve?**  
- **Tab Estadísticas**: Monitorear el estado de sincronización entre Google Drive y la base de datos
- **Tab Categorías**: Gestionar las categorías disponibles para proveedores y otros usos del sistema

**Características principales:**

**Tab Estadísticas:**
- **Archivos en Drive**: Contador de facturas disponibles en Google Drive
- **Facturas en BD**: Total de facturas almacenadas en la base de datos
- **Estados de procesamiento**: Desglose de facturas procesadas, en cuarentena y con error
- **Indicador de sincronización**: Última fecha de sincronización con Drive
- **Gráfico de calidad**: Porcentaje de facturas procesadas exitosamente
- **Diferencia de sincronización**: Identificación de archivos no procesados
- **Botón Actualizar**: Refrescar estadísticas en tiempo real

**Tab Categorías:**
- **Listado completo**: Todas las categorías disponibles en el sistema
- **Crear categorías**: Agregar nuevas categorías con nombre, descripción y configuración
- **Editar categorías**: Modificar información de categorías existentes
- **Eliminar categorías**: Remover categorías que ya no se utilizan
- **Búsqueda**: Localizar categorías específicas rápidamente
- **Gestión centralizada**: Administrar todas las categorías desde un solo lugar

**Cuándo usarlo:**  
- **Tab Estadísticas**: Para verificar que el sistema está funcionando correctamente, identificar problemas de sincronización, monitorear el progreso de procesamiento de facturas nuevas o diagnosticar problemas técnicos.
- **Tab Categorías**: Para crear nuevas categorías de proveedores, modificar categorías existentes, o eliminar categorías obsoletas. Ideal cuando necesitas organizar mejor los proveedores o agregar nuevas clasificaciones.

---

## 🎯 Flujo de Trabajo Recomendado

### Flujo Diario:
1. **Dashboard** → Revisar estado general y KPIs
2. **Pendientes** → Resolver facturas con problemas
3. **Datos** (Tab Estadísticas) → Verificar sincronización

### Flujo Semanal:
1. **Proveedores** → Actualizar categorías y datos de proveedores
2. **Datos** (Tab Categorías) → Gestionar categorías si es necesario
3. **Reportes** → Generar análisis semanal y revisar rentabilidad

### Flujo Mensual:
1. **Reportes** → Generar reporte mensual completo y análisis de rentabilidad
2. **Dashboard** → Análisis de tendencias y exportar datos
3. **Proveedores** → Revisar y normalizar nuevos proveedores, asignar categorías
4. **Datos** (Tab Categorías) → Revisar y actualizar categorías según necesidades

---

## 💡 Consejos de Uso

- **Mantén las categorías actualizadas**: Gestiona las categorías desde "Datos" → Tab "Categorías" para facilitar el análisis y reportes
- **Revisa pendientes regularmente**: Evita acumulación de facturas sin procesar
- **Usa los filtros**: Ahorra tiempo en búsquedas específicas (alfabético en Proveedores, por categoría, etc.)
- **Exporta reportes regularmente**: Mantén respaldos de tus análisis desde el Dashboard
- **Monitorea la sincronización**: Usa "Datos" → Tab "Estadísticas" para verificar que todas las facturas se procesen
- **Gestiona categorías centralizadamente**: Crea, edita o elimina categorías desde "Datos" → Tab "Categorías" antes de asignarlas a proveedores
- **Utiliza el análisis de rentabilidad**: Revisa regularmente los reportes de rentabilidad para tomar decisiones estratégicas

---

## 🔒 Seguridad y Acceso

Todas las secciones requieren autenticación. Los datos están protegidos y solo usuarios autorizados pueden acceder a la información de facturas y proveedores.

---

---

## 🏷️ Categorías

**¿Qué es?**  
Sección dedicada a la gestión centralizada de categorías utilizadas en el sistema, principalmente para clasificar proveedores y facilitar análisis y reportes.

**¿Para qué sirve?**  
- Crear nuevas categorías para organizar proveedores
- Editar información de categorías existentes (nombre, descripción, configuración)
- Eliminar categorías que ya no se utilizan
- Consultar todas las categorías disponibles en el sistema
- Gestionar de forma centralizada la taxonomía del sistema

**Características principales:**
- **Listado completo**: Todas las categorías disponibles en el sistema
- **Crear categorías**: Formulario para agregar nuevas categorías con todos sus atributos
- **Editar categorías**: Modificar información de categorías existentes
- **Eliminar categorías**: Remover categorías obsoletas o que ya no se necesitan
- **Búsqueda**: Localizar categorías específicas rápidamente
- **Gestión centralizada**: Un solo lugar para administrar todas las categorías del sistema

**Cuándo usarlo:**  
Cuando necesites crear nuevas categorías de proveedores (por ejemplo, "Seguros y Asesorías", "Formación", etc.), modificar categorías existentes, o eliminar categorías que ya no se utilizan. Ideal para mantener la organización del sistema actualizada según las necesidades del negocio.

**Nota:** Las categorías creadas aquí estarán disponibles inmediatamente para asignar a proveedores en la sección "Proveedores".

---

## 🆕 Cambios Recientes

### Nueva Sección: Categorías
- Se agregó una sección completa para gestionar categorías de proveedores
- Accesible desde "Datos" → Tab "Categorías" o directamente desde el menú lateral
- Permite crear, editar y eliminar categorías de forma centralizada

### Mejoras en Reportes
- Se agregó análisis de rentabilidad con KPIs y gráficos comparativos
- Edición inline de ingresos mensuales para cálculos de rentabilidad
- Selector de año para análisis históricos

### Reorganización de Datos
- La sección "Carga de Datos" ahora se llama "Datos"
- Incluye dos tabs: "Estadísticas" (sincronización) y "Categorías" (gestión de categorías)

### Mejoras en Proveedores
- Filtro por categoría además del filtro alfabético
- Visualización mejorada con chips de colores por categoría
- Iconos distintivos para cada categoría

---

*Última actualización: Diciembre 2025*

