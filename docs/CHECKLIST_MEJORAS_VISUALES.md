# Checklist de Mejoras Visuales - Análisis de Seguridad

**Fecha:** 2025-11-12  
**Objetivo:** Analizar cambios visuales sugeridos sin romper funcionalidad

---

## ✅ CAMBIOS SEGUROS (Solo CSS, sin riesgo)

### 1. Fondo General (de violeta a blanco)

**Cambio sugerido:**
- `bg-gradient-dashboard` → `bg-white` o `bg-gray-50`

**Archivos afectados:**
- `Dashboard.jsx` (2 lugares: contenedor principal y estado de error)
- `index.css` (clase `.bg-gradient-dashboard` puede quedar para otros usos)

**Análisis:**
- ✅ **SEGURO** - Solo cambia color de fondo
- ⚠️ **Nota:** Cambiar en ambos lugares (contenedor principal y estado de error)
- ✅ No afecta funcionalidad, solo visual

**Implementación:**
```jsx
// Dashboard.jsx - Línea 51
// Antes: className="min-h-screen bg-gradient-dashboard p-2..."
// Después: className="min-h-screen bg-white p-2..."

// Dashboard.jsx - Línea 30 (estado de error)
// Antes: className="min-h-screen bg-gradient-dashboard flex..."
// Después: className="min-h-screen bg-white flex..."
```

---

### 2. Fuente Calibri

**Cambio sugerido:**
- Cambiar fuente de `Inter` a `Calibri`

**Archivos afectados:**
- `index.css` (línea 40-45)

**Análisis:**
- ⚠️ **REVISAR** - Calibri es fuente de Windows, puede no estar disponible en Linux/Mac
- ✅ **Alternativa segura:** Usar Calibri con fallbacks: `'Calibri', 'Candara', 'Segoe', 'Segoe UI', sans-serif`
- ✅ O usar fuente web similar (pero Calibri no está en Google Fonts)

**Implementación:**
```css
/* index.css */
body {
  font-family: 'Calibri', 'Candara', 'Segoe', 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
```

**Recomendación:** ✅ Aplicar con fallbacks

---

### 3. Bordes en Tarjetas KPI

**Cambio sugerido:**
- Agregar `border border-gray-200` a cada tarjeta KPI
- Reducir `rounded-2xl` a `rounded-md` o `rounded-lg`

**Archivos afectados:**
- `KPICard.jsx` (línea 30)

**Análisis:**
- ✅ **SEGURO** - Solo agrega borde visual
- ✅ No afecta funcionalidad
- ⚠️ **Nota:** Reducir redondeo puede cambiar aspecto, pero es seguro

**Implementación:**
```jsx
// KPICard.jsx
// Antes: className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl shadow-card..."
// Después: className="bg-white border border-gray-200 p-4 sm:p-6 lg:p-8 rounded-lg shadow-card..."
```

---

### 4. Colores Diferenciados en Tarjetas KPI

**Cambio sugerido:**
- Primera (Facturas Procesadas): `bg-green-100 text-green-800`
- Segunda (Importe del Mes): `bg-emerald-100 text-emerald-800`
- Tercera (Impuestos Totales): `bg-orange-100 text-orange-800`
- Cuarta (Proveedores Activos): `bg-purple-100 text-purple-800`

**Archivos afectados:**
- `KPICard.jsx` (fondo de tarjeta)
- `KPIGrid.jsx` (pasar colores diferentes)

**Análisis:**
- ⚠️ **REVISAR** - Actualmente el fondo es blanco y el icono tiene color
- ✅ **SEGURO** si cambiamos solo el fondo de la tarjeta
- ⚠️ **Nota:** Necesitamos pasar un prop adicional o modificar KPIGrid para pasar colores de fondo
- ✅ No rompe funcionalidad, solo visual

**Implementación:**
```jsx
// KPICard.jsx - Agregar prop bgColor
<div className={`${bgColor} border border-gray-200 p-4...`}>

// KPIGrid.jsx - Pasar colores diferentes
const kpis = [
  { ..., bgColor: 'bg-green-100', textColor: 'text-green-800' },
  { ..., bgColor: 'bg-emerald-100', textColor: 'text-emerald-800' },
  // etc.
];
```

**Recomendación:** ✅ Aplicar, pero requiere modificar props (solo visual)

---

### 5. Reducir Gaps en KPIGrid

**Cambio sugerido:**
- `gap-3 sm:gap-4 ipad:gap-4 lg:gap-6` → `gap-4` (uniforme)

**Archivos afectados:**
- `KPIGrid.jsx` (línea 7 y 58)

**Análisis:**
- ✅ **SEGURO** - Solo cambia espaciado
- ⚠️ **Nota:** Ya tenemos `ipad:gap-4`, el cambio sería hacerlo uniforme
- ✅ No afecta funcionalidad

**Recomendación:** ✅ Aplicar (ya está parcialmente implementado)

---

### 6. Bordes en Tabla

**Cambio sugerido:**
- Agregar `border border-gray-200` al contenedor de tabla
- Agregar `border-b border-gray-200` en celdas (ya existe parcialmente)

**Archivos afectados:**
- `FacturasTable.jsx` (línea 137 y celdas)

**Análisis:**
- ✅ **SEGURO** - Solo agrega bordes visuales
- ✅ Ya tiene `border-b border-gray-100` en filas, cambiar a `border-gray-200` es seguro
- ✅ No afecta funcionalidad

**Implementación:**
```jsx
// FacturasTable.jsx - Contenedor
// Antes: <div className="bg-white rounded-2xl shadow-header p-4...">
// Después: <div className="bg-white border border-gray-200 rounded-2xl shadow-header p-4...">

// FacturasTable.jsx - Filas
// Antes: className="border-b border-gray-100..."
// Después: className="border-b border-gray-200..."
```

---

### 7. Alineación en Tabla

**Cambio sugerido:**
- `text-center` en TOTAL → `text-right`
- Mantener `text-left` en PROVEEDOR
- Mantener `text-center` en FECHA y ESTADO

**Archivos afectados:**
- `FacturasTable.jsx` (celdas de TOTAL)

**Análisis:**
- ✅ **SEGURO** - Solo cambia alineación de texto
- ✅ Mejora legibilidad de números
- ✅ No afecta funcionalidad

**Implementación:**
```jsx
// FacturasTable.jsx - Header TOTAL
// Antes: <th className="text-center...">TOTAL</th>
// Después: <th className="text-right...">TOTAL</th>

// FacturasTable.jsx - Celda TOTAL
// Antes: <td className="... text-center...">€1,234.56</td>
// Después: <td className="... text-right...">€1,234.56</td>
```

---

### 8. Padding en Tabla

**Cambio sugerido:**
- Aumentar padding: `px-4 py-2` → `px-6 py-3`

**Archivos afectados:**
- `FacturasTable.jsx` (celdas)

**Análisis:**
- ⚠️ **REVISAR** - Ya tenemos `px-4 md:px-6 ipad:px-8`
- ✅ **SEGURO** - Solo aumenta espaciado
- ⚠️ **Nota:** Ya está parcialmente implementado, podría ser redundante
- ✅ No afecta funcionalidad

**Recomendación:** ⚠️ Ya está implementado con breakpoints, no necesario

---

### 9. Border en Header

**Cambio sugerido:**
- Agregar `border-b border-gray-200` al header

**Archivos afectados:**
- `Header.jsx` (línea 11)

**Análisis:**
- ✅ **SEGURO** - Solo agrega borde visual
- ✅ No afecta funcionalidad

**Implementación:**
```jsx
// Header.jsx
// Antes: <div className="bg-white rounded-[20px] shadow-header...">
// Después: <div className="bg-white border-b border-gray-200 rounded-[20px] shadow-header...">
```

---

### 10. Título y Subtítulo

**Cambio sugerido:**
- Título: `text-2xl font-bold text-gray-900`
- Subtítulo: `text-sm text-gray-500`

**Archivos afectados:**
- `Header.jsx` (líneas 14-18)

**Análisis:**
- ⚠️ **REVISAR** - Actualmente tiene `text-xl sm:text-2xl md:text-3xl` (responsivo)
- ✅ **SEGURO** si mantenemos responsividad
- ⚠️ **Nota:** Cambiar a fijo `text-2xl` puede romper responsive en mobile
- ✅ Mejor mantener responsive: `text-xl sm:text-2xl md:text-2xl`

**Recomendación:** ⚠️ Aplicar pero mantener responsividad

---

## ❌ CAMBIOS CON RIESGO (Revisar antes de aplicar)

### 11. Selector de Mes (Dropdown)

**Cambio sugerido:**
- Reemplazar barra horizontal de meses por dropdown

**Archivos afectados:**
- `Header.jsx` (cambio funcional, no solo visual)

**Análisis:**
- ❌ **RIESGO ALTO** - Cambio funcional, no solo visual
- ❌ Cambia UX completamente
- ❌ Requiere lógica adicional (componente dropdown o select)
- ⚠️ **Nota:** El usuario mencionó "sin romper funcionalidad", esto es un cambio funcional

**Recomendación:** ❌ **NO APLICAR** - Es cambio funcional, no solo visual

**Alternativa segura:**
- ✅ Mantener barra horizontal pero mejorar scroll (ya implementado)
- ✅ O hacer tabs compactos con mejor scroll (ya implementado)

---

### 12. Reducir Redondeo Excesivo

**Cambio sugerido:**
- `rounded-2xl` → `rounded-md` o `rounded-lg`

**Archivos afectados:**
- Múltiples componentes

**Análisis:**
- ✅ **SEGURO** - Solo cambia apariencia
- ⚠️ **Nota:** Puede cambiar mucho el look & feel
- ✅ No afecta funcionalidad

**Recomendación:** ✅ Aplicar gradualmente (solo donde se menciona)

---

## 📋 Resumen de Decisiones

### ✅ APLICAR (Seguro, solo visual):
1. ✅ Fondo general: `bg-gradient-dashboard` → `bg-white`
2. ✅ Fuente Calibri (con fallbacks)
3. ✅ Bordes en tarjetas KPI
4. ✅ Colores diferenciados en tarjetas KPI (con modificación de props)
5. ✅ Bordes en tabla
6. ✅ Alineación `text-right` en columna TOTAL
7. ✅ Border en header
8. ✅ Título/subtítulo (manteniendo responsividad)

### ⚠️ REVISAR (Aplicar con cuidado):
9. ⚠️ Padding en tabla (ya está implementado con breakpoints)
10. ⚠️ Reducir redondeo (cambiar look & feel)

### ❌ NO APLICAR (Riesgo):
11. ❌ Selector de mes a dropdown (cambio funcional, no solo visual)

---

## 🎯 Plan de Implementación Seguro

### Fase 1: Cambios Simples (Solo CSS)
1. Fondo blanco
2. Fuente Calibri
3. Bordes en tabla y header
4. Alineación en tabla

### Fase 2: Cambios en Componentes (Props)
5. Colores diferenciados en KPI (modificar KPICard y KPIGrid)
6. Bordes en tarjetas KPI

### Fase 3: Ajustes Finales
7. Reducir redondeo (opcional)
8. Ajustar títulos (manteniendo responsive)

---

## ⚠️ Advertencias

1. **Fuente Calibri:** No está disponible en Google Fonts, usar con fallbacks
2. **Colores KPI:** Requiere modificar props, pero es solo visual
3. **Selector de mes:** NO cambiar a dropdown (es cambio funcional)
4. **Responsividad:** Mantener breakpoints en títulos y padding

---

**Fin del checklist**

