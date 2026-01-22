# 📘 API de Costos de Personal - Documentación para Desarrollador UI/Frontend

**Fecha:** 2026-01-19  
**Backend:** FastAPI (Invoice Extractor)  
**Base URL:** `https://alexforge.online/invoice-api/api/costos-personal`  
**Autenticación:** Requerida (sesión HTTP con cookies)

---

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Modelo de Datos](#modelo-de-datos)
3. [Endpoints Disponibles](#endpoints-disponibles)
4. [Ejemplos de Uso](#ejemplos-de-uso)
5. [Integración con Rentabilidad](#integración-con-rentabilidad)
6. [Casos de Error](#casos-de-error)
7. [Recomendaciones UI/UX](#recomendaciones-uiux)

---

## 🎯 Resumen Ejecutivo

### ¿Qué es?
Sistema de gestión de **costos mensuales de personal** (sueldos netos + seguros sociales) independiente de las facturas.

### ¿Para qué sirve?
- Cargar manualmente los costos de personal mes a mes
- Integrar automáticamente estos costos en el cálculo de rentabilidad
- Separar gastos variables (facturas) de gastos fijos (personal)

### Campos principales:
- **`sueldos_netos`**: Total de sueldos netos pagados al personal (€)
- **`coste_empresa`**: Total de seguros sociales, cotizaciones, etc. (€)
- **`total_personal`** (calculado): Suma de ambos

### Restricciones:
- ✅ Un solo registro por mes/año (upsert automático)
- ✅ Valores >= 0
- ✅ Mes: 1-12, Año: 2000-2100

---

## 📊 Modelo de Datos

### Schema de Request (POST)

```typescript
interface CostoPersonalCreate {
  mes: number;           // 1-12 (obligatorio)
  año: number;           // 2000-2100 (obligatorio)
  sueldos_netos: number; // >= 0 (obligatorio)
  coste_empresa: number; // >= 0 (obligatorio)
  notas?: string;        // Opcional, max 500 chars
}
```

### Schema de Response (GET)

```typescript
interface CostoPersonalResponse {
  id: number;
  mes: number;
  año: number;
  sueldos_netos: number;
  coste_empresa: number;
  total_personal: number;    // Calculado: sueldos_netos + coste_empresa
  notas: string | null;
  creado_en: string;         // ISO 8601
  actualizado_en: string;    // ISO 8601
}
```

### Schema de Totales Anuales

```typescript
interface CostoPersonalTotales {
  total_sueldos_netos: number;
  total_coste_empresa: number;
  total_personal: number;
}
```

---

## 🔌 Endpoints Disponibles

### 1. **GET** `/api/costos-personal/{year}` - Listar costos de un año

**Descripción:** Obtener todos los costos de personal de un año específico.

**URL:** `GET https://alexforge.online/invoice-api/api/costos-personal/2025`

**Query Parameters:**
- `year` (path, obligatorio): Año a consultar (2000-2100)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "mes": 1,
    "año": 2025,
    "sueldos_netos": 2500.00,
    "coste_empresa": 800.00,
    "total_personal": 3300.00,
    "notas": "Enero 2025 - 1 empleado",
    "creado_en": "2025-01-15T10:30:00",
    "actualizado_en": "2025-01-15T10:30:00"
  },
  {
    "id": 2,
    "mes": 2,
    "año": 2025,
    "sueldos_netos": 2500.00,
    "coste_empresa": 800.00,
    "total_personal": 3300.00,
    "notas": "Febrero 2025 - 1 empleado",
    "creado_en": "2025-02-10T14:20:00",
    "actualizado_en": "2025-02-10T14:20:00"
  }
]
```

**Ejemplo Fetch:**
```javascript
const year = 2025;
const response = await fetch(
  `https://alexforge.online/invoice-api/api/costos-personal/${year}`,
  {
    method: 'GET',
    credentials: 'include', // IMPORTANTE: Incluir cookies de sesión
    headers: {
      'Content-Type': 'application/json'
    }
  }
);

const costos = await response.json();
console.log(costos);
```

---

### 2. **GET** `/api/costos-personal/{year}/{month}` - Obtener costo de un mes

**Descripción:** Obtener el costo de personal de un mes/año específico.

**URL:** `GET https://alexforge.online/invoice-api/api/costos-personal/2025/3`

**Query Parameters:**
- `year` (path, obligatorio): Año
- `month` (path, obligatorio): Mes (1-12)

**Response:** `200 OK`
```json
{
  "id": 3,
  "mes": 3,
  "año": 2025,
  "sueldos_netos": 5000.00,
  "coste_empresa": 1600.00,
  "total_personal": 6600.00,
  "notas": "Marzo 2025 - 2 empleados",
  "creado_en": "2025-03-05T09:15:00",
  "actualizado_en": "2025-03-05T09:15:00"
}
```

**Response:** `404 Not Found` (si no existe)
```json
{
  "detail": "No existe costo de personal para 3/2025"
}
```

**Ejemplo Fetch:**
```javascript
const year = 2025;
const month = 3;

try {
  const response = await fetch(
    `https://alexforge.online/invoice-api/api/costos-personal/${year}/${month}`,
    {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    }
  );

  if (response.status === 404) {
    console.log('No hay costo cargado para este mes');
    return null;
  }

  const costo = await response.json();
  return costo;
} catch (error) {
  console.error('Error al obtener costo:', error);
}
```

---

### 3. **POST** `/api/costos-personal` - Crear/Actualizar costo (UPSERT)

**Descripción:** Crear o actualizar costo de personal. Si ya existe un costo para el mes/año, se actualiza. Si no existe, se crea.

**URL:** `POST https://alexforge.online/invoice-api/api/costos-personal`

**Body (JSON):**
```json
{
  "mes": 4,
  "año": 2025,
  "sueldos_netos": 3500.50,
  "coste_empresa": 1200.00,
  "notas": "Abril 2025 - 1 empleado + bonus"
}
```

**Response:** `201 Created` (si es creación) o `200 OK` (si es actualización)
```json
{
  "id": 4,
  "mes": 4,
  "año": 2025,
  "sueldos_netos": 3500.50,
  "coste_empresa": 1200.00,
  "total_personal": 4700.50,
  "notas": "Abril 2025 - 1 empleado + bonus",
  "creado_en": "2025-04-08T11:45:00",
  "actualizado_en": "2025-04-08T11:45:00"
}
```

**Ejemplo Fetch:**
```javascript
const costoData = {
  mes: 4,
  año: 2025,
  sueldos_netos: 3500.50,
  coste_empresa: 1200.00,
  notas: "Abril 2025 - 1 empleado + bonus"
};

const response = await fetch(
  'https://alexforge.online/invoice-api/api/costos-personal',
  {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(costoData)
  }
);

if (response.ok) {
  const costo = await response.json();
  console.log('Costo guardado:', costo);
} else {
  const error = await response.json();
  console.error('Error:', error.detail);
}
```

---

### 4. **DELETE** `/api/costos-personal/{id}` - Eliminar costo

**Descripción:** Eliminar un costo de personal por ID.

**URL:** `DELETE https://alexforge.online/invoice-api/api/costos-personal/4`

**Response:** `204 No Content` (éxito, sin body)

**Response:** `404 Not Found` (si no existe)
```json
{
  "detail": "Costo con ID 4 no encontrado"
}
```

**Ejemplo Fetch:**
```javascript
const costoId = 4;

const response = await fetch(
  `https://alexforge.online/invoice-api/api/costos-personal/${costoId}`,
  {
    method: 'DELETE',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  }
);

if (response.status === 204) {
  console.log('Costo eliminado correctamente');
} else if (response.status === 404) {
  console.log('Costo no encontrado');
}
```

---

### 5. **GET** `/api/costos-personal/{year}/totales` - Totales anuales

**Descripción:** Obtener totales de costos de personal de un año.

**URL:** `GET https://alexforge.online/invoice-api/api/costos-personal/2025/totales`

**Response:** `200 OK`
```json
{
  "total_sueldos_netos": 30000.00,
  "total_coste_empresa": 9600.00,
  "total_personal": 39600.00
}
```

**Ejemplo Fetch:**
```javascript
const year = 2025;

const response = await fetch(
  `https://alexforge.online/invoice-api/api/costos-personal/${year}/totales`,
  {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    }
  }
);

const totales = await response.json();
console.log(`Total personal ${year}:`, totales.total_personal);
```

---

## 💰 Integración con Rentabilidad

### ⚠️ IMPORTANTE: El endpoint de rentabilidad YA INCLUYE los costos de personal automáticamente

**Endpoint:** `GET /api/ingresos/rentabilidad/{year}`

**Cambios en la respuesta:**

```typescript
interface IngresoMensualItem {
  mes: number;
  año: number;
  ingresos: number;
  gastos: number;              // Gastos de facturas (proveedores)
  gastos_personal: number;     // ⭐ NUEVO: Costos de personal del mes
  gastos_totales: number;      // ⭐ NUEVO: gastos + gastos_personal
  rentabilidad: number;        // Calculado: ingresos - gastos_totales
  margen: number;
  ingreso_cargado: boolean;
  estado: string;
}
```

**Ejemplo de respuesta:**
```json
{
  "meses": [
    {
      "mes": 1,
      "año": 2025,
      "ingresos": 15000.00,
      "gastos": 8000.00,
      "gastos_personal": 3300.00,
      "gastos_totales": 11300.00,
      "rentabilidad": 3700.00,
      "margen": 24.7,
      "ingreso_cargado": true,
      "estado": "positivo"
    }
  ],
  "totales": {
    "ingresos": 180000.00,
    "gastos": 151300.00,
    "rentabilidad": 28700.00,
    "margen": 15.9
  }
}
```

**⚠️ No necesitas hacer nada especial:** El backend ya suma automáticamente `gastos_personal` a `gastos` para calcular `gastos_totales` y `rentabilidad`.

---

## ❌ Casos de Error

### Error 400: Validación fallida
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "mes"],
      "msg": "Input should be less than or equal to 12"
    }
  ]
}
```

**Causas comunes:**
- `mes` fuera de rango (1-12)
- `año` fuera de rango (2000-2100)
- `sueldos_netos` o `coste_empresa` negativos
- `notas` con más de 500 caracteres

### Error 401: No autenticado
```json
{
  "detail": "No autenticado. Por favor, inicia sesión."
}
```

**Solución:** Asegúrate de incluir `credentials: 'include'` en tus fetch calls.

### Error 404: Recurso no encontrado
```json
{
  "detail": "No existe costo de personal para 3/2025"
}
```

**Solución:** El mes/año no tiene costo cargado. Es normal, permite al UI mostrar "Sin datos" o formulario vacío.

### Error 500: Error del servidor
```json
{
  "detail": "Error al guardar costo: ..."
}
```

**Solución:** Error interno del backend. Revisar logs del contenedor.

---

## 🎨 Recomendaciones UI/UX

### Pantalla Principal: "Costos de Personal"

#### Layout sugerido:
```
┌─────────────────────────────────────────────────────────┐
│  Costos de Personal - 2025               [Año: 2025 ▼] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  MES   SUELDOS NETOS   COSTE EMPRESA   TOTAL   ACCIONES│
│  ───   ────────────    ──────────────   ─────   ─────── │
│  Ene   2,500.00 €      800.00 €         3,300  [✏️][🗑️] │
│  Feb   2,500.00 €      800.00 €         3,300  [✏️][🗑️] │
│  Mar   -               -                 -      [➕]     │
│  Abr   -               -                 -      [➕]     │
│  ...                                                     │
│                                                          │
│  TOTALES ANUALES:                                        │
│  • Sueldos Netos: 30,000.00 €                           │
│  • Coste Empresa: 9,600.00 €                            │
│  • Total Personal: 39,600.00 €                          │
└─────────────────────────────────────────────────────────┘
```

#### Modal de Crear/Editar:
```
┌────────────────────────────────────┐
│  Cargar Costos - Enero 2025        │
├────────────────────────────────────┤
│                                     │
│  Mes:             [Enero     ▼]    │
│  Año:             [2025      ▼]    │
│                                     │
│  Sueldos Netos:   [________] €     │
│  Coste Empresa:   [________] €     │
│  (Seguros Sociales)                │
│                                     │
│  Total Personal:  3,300.00 € ✓     │
│                                     │
│  Notas (opcional):                 │
│  [_____________________________]   │
│                                     │
│            [Cancelar] [Guardar]    │
└────────────────────────────────────┘
```

### Flujo de Usuario:

1. **Ver lista anual:** GET `/api/costos-personal/2025`
2. **Crear nuevo:** Click en [➕] → Modal → POST `/api/costos-personal`
3. **Editar existente:** Click en [✏️] → Modal con datos precargados → POST `/api/costos-personal` (upsert)
4. **Eliminar:** Click en [🗑️] → Confirmación → DELETE `/api/costos-personal/{id}`

### Features recomendadas:

#### 1. **Autocompletado inteligente**
- Copiar datos del mes anterior automáticamente
- Mostrar promedio de meses anteriores

#### 2. **Validaciones en tiempo real**
- Calcular automáticamente `total_personal` mientras el usuario escribe
- Mostrar advertencias si el total es inusualmente alto/bajo

#### 3. **Integración con Rentabilidad**
- Botón "Ver impacto en rentabilidad" que navega a `/rentabilidad?year=2025&mes=3`
- Mostrar badge en la tabla de rentabilidad indicando "✓ Personal cargado" o "⚠️ Sin costos de personal"

#### 4. **Exportación**
- Botón "Exportar Excel" que descargue todos los costos del año
- Incluir columna calculada de "% sobre ingresos"

#### 5. **Bulk Loading**
- Opción "Cargar todos los meses" para copiar un valor fijo a todos los meses vacíos
- Útil si el costo es constante

---

## 📝 Checklist de Implementación

### Backend (✅ Completado)
- [x] Tabla `costos_personal` creada
- [x] Repository `CostoPersonalRepository` implementado
- [x] Routes `/api/costos-personal/*` creadas
- [x] Integración con `/api/ingresos/rentabilidad/{year}`
- [x] Migración SQL lista

### Frontend (🚧 Por hacer)
- [ ] Pantalla "Costos de Personal" en React-Admin
- [ ] Componente tabla mensual con años selector
- [ ] Modal de crear/editar con validaciones
- [ ] Integración con página de Rentabilidad
- [ ] Tests E2E (Playwright)

---

## 🔐 Autenticación

**⚠️ MUY IMPORTANTE:** Todos los endpoints requieren autenticación.

**Solución:** Incluir `credentials: 'include'` en **todos** tus fetch calls:

```javascript
const response = await fetch(url, {
  method: 'GET', // o POST, DELETE, etc.
  credentials: 'include', // ← OBLIGATORIO
  headers: {
    'Content-Type': 'application/json'
  }
});
```

---

## 📞 Contacto y Soporte

**Arquitecto Backend:** Invoice Extractor Senior Team  
**Base URL Producción:** `https://alexforge.online/invoice-api`  
**Documentación OpenAPI:** `https://alexforge.online/invoice-api/docs`

**Próximos pasos:**
1. Aplicar migración SQL en producción (reiniciar backend)
2. Implementar UI en React-Admin
3. Integrar con página de Rentabilidad existente

---

**¡Éxito en la implementación! 🚀**

