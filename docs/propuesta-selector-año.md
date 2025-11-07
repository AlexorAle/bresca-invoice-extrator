# Propuesta: Selector de Año en el Dashboard

## Estado Actual

El Header actual tiene:
- **Título**: "🧾 Dashboard de Facturación"
- **Descripción**: "Vista mensual - Actualizado en tiempo real"
- **Selector de mes**: Botones horizontales (Ene, Feb, Mar, Abr, May, Jun, Jul, Ago, Sep, Oct, Nov, Dic)
- **Año**: Fijo en 2025 (hardcodeado)

## Propuesta: Agregar Selector de Año

### Diseño Visual

```
┌─────────────────────────────────────────────────────────────────┐
│  🧾 Dashboard de Facturación                                    │
│  Vista mensual - Actualizado en tiempo real                    │
│                                                                 │
│                    [2025 ▼]  [Ene] [Feb] [Mar] [Abr] [May] ... │
└─────────────────────────────────────────────────────────────────┘
```

### Opciones de Diseño

#### Opción 1: Dropdown a la izquierda del selector de mes
```
[Título]                    [Año: 2025 ▼] [Ene] [Feb] [Mar] ...
```

**Ventajas:**
- Mantiene el diseño horizontal
- Fácil de usar
- No ocupa mucho espacio

#### Opción 2: Dropdown integrado en la misma barra
```
[Título]                    [2025 ▼] [Ene] [Feb] [Mar] ...
```

**Ventajas:**
- Más compacto
- Visualmente integrado

#### Opción 3: Selector de año arriba, meses abajo
```
[Título]                    [Año: 2025 ▼]
                            [Ene] [Feb] [Mar] [Abr] [May] ...
```

**Ventajas:**
- Jerarquía visual clara
- Más espacio para los meses

### Rango de Años

- **Desde**: 2020 (año base)
- **Hasta**: Año actual (2025) + 1 año futuro (para facturas futuras)
- **Lista**: [2020, 2021, 2022, 2023, 2024, 2025, 2026]

### Implementación Técnica

1. **Header.jsx**: Agregar prop `onYearChange` y selector de año
2. **Dashboard.jsx**: Cambiar `selectedYear` de constante a estado con `useState`
3. **useInvoiceData.js**: Ya recibe `year` como parámetro, no necesita cambios
4. **Backend**: Ya soporta filtrado por año, no necesita cambios

### Estilo del Selector

- **Dropdown**: Estilo similar a los botones de mes
- **Fondo**: `bg-gray-50` (igual que el selector de mes)
- **Borde**: Redondeado `rounded-lg`
- **Hover**: Efecto hover similar a los botones de mes
- **Activo**: Mismo estilo que el mes activo (`bg-gradient-active`)

### Ejemplo de Código

```jsx
<select
  value={selectedYear}
  onChange={(e) => onYearChange(parseInt(e.target.value))}
  className="px-4 py-2 rounded-lg bg-white border border-gray-200 text-sm font-medium text-gray-700 hover:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
>
  {Array.from({ length: 7 }, (_, i) => 2020 + i).map(year => (
    <option key={year} value={year}>{year}</option>
  ))}
</select>
```

## Recomendación

**Opción 1** (Dropdown a la izquierda) es la más clara y fácil de usar, manteniendo la consistencia visual con el selector de mes.

