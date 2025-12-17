# Resumen Ejecutivo - Mejoras Visuales

**Fecha:** 2025-11-12

---

## ✅ CAMBIOS SEGUROS (Aplicar)

| # | Cambio | Archivo | Riesgo | Notas |
|---|--------|---------|--------|-------|
| 1 | Fondo blanco (quitar violeta) | `Dashboard.jsx` | ✅ Ninguno | Cambiar en 2 lugares (normal + error) |
| 2 | Fuente Calibri | `index.css` | ✅ Ninguno | Usar con fallbacks (no está en Google Fonts) |
| 3 | Bordes en tarjetas KPI | `KPICard.jsx` | ✅ Ninguno | Agregar `border border-gray-200` |
| 4 | Colores diferenciados KPI | `KPICard.jsx` + `KPIGrid.jsx` | ✅ Ninguno | Requiere modificar props (solo visual) |
| 5 | Bordes en tabla | `FacturasTable.jsx` | ✅ Ninguno | Agregar borde al contenedor |
| 6 | Alineación TOTAL → right | `FacturasTable.jsx` | ✅ Ninguno | Mejora legibilidad de números |
| 7 | Border en header | `Header.jsx` | ✅ Ninguno | Agregar `border-b` |
| 8 | Ajustar títulos | `Header.jsx` | ⚠️ Bajo | Mantener responsividad |

---

## ⚠️ CAMBIOS A REVISAR

| # | Cambio | Riesgo | Razón |
|---|--------|--------|-------|
| 9 | Padding tabla | ⚠️ Ya implementado | Ya tiene breakpoints responsive |
| 10 | Reducir redondeo | ⚠️ Cambia look | Puede cambiar mucho el aspecto |

---

## ❌ NO APLICAR (Riesgo)

| # | Cambio | Riesgo | Razón |
|---|--------|--------|-------|
| 11 | Selector mes → Dropdown | ❌ ALTO | **Cambio funcional, no solo visual** |

---

## 📊 Detalles por Cambio

### ✅ 1. Fondo Blanco
- **Antes:** `bg-gradient-dashboard` (violeta)
- **Después:** `bg-white` o `bg-gray-50`
- **Lugares:** Dashboard principal + estado de error

### ✅ 2. Fuente Calibri
- **Antes:** `'Inter', -apple-system...`
- **Después:** `'Calibri', 'Candara', 'Segoe', 'Segoe UI', 'Inter', ...`
- **Nota:** Calibri no está en Google Fonts, usar fallbacks

### ✅ 3-4. Tarjetas KPI
- **Agregar:** `border border-gray-200`
- **Colores:**
  - Facturas: `bg-green-100 text-green-800`
  - Importe: `bg-emerald-100 text-emerald-800`
  - Impuestos: `bg-orange-100 text-orange-800`
  - Proveedores: `bg-purple-100 text-purple-800`

### ✅ 5-6. Tabla
- **Bordes:** `border border-gray-200` en contenedor
- **Alineación:** `text-right` en columna TOTAL
- **Filas:** `border-gray-200` (ya tiene `border-gray-100`)

### ✅ 7-8. Header
- **Border:** `border-b border-gray-200`
- **Títulos:** Mantener responsive (`text-xl sm:text-2xl`)

---

## 🎯 Recomendación Final

### ✅ APLICAR (8 cambios):
1. ✅ Fondo blanco
2. ✅ Fuente Calibri
3. ✅ Bordes en tarjetas
4. ✅ Colores KPI
5. ✅ Bordes en tabla
6. ✅ Alineación TOTAL
7. ✅ Border header
8. ✅ Ajustar títulos (con cuidado)

### ⚠️ OPCIONAL (2 cambios):
9. ⚠️ Padding tabla (ya está bien)
10. ⚠️ Reducir redondeo (opcional)

### ❌ NO APLICAR (1 cambio):
11. ❌ Selector mes → Dropdown (cambio funcional)

---

## 📝 Notas Importantes

1. **Fuente Calibri:** No está en Google Fonts, usar con fallbacks seguros
2. **Colores KPI:** Requiere modificar `KPICard` para aceptar `bgColor` prop
3. **Responsividad:** Mantener breakpoints en todos los cambios
4. **Selector de mes:** NO cambiar (es funcional, no solo visual)

---

**Total de cambios seguros: 8**  
**Total de cambios opcionales: 2**  
**Total de cambios a evitar: 1**

---

**Fin del resumen**










