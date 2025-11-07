# Resumen Ejecutivo: Implementación Dashboard React

## 📋 Validación de Base de Datos

### ✅ Campos Verificados

| Campo en Prompt | Campo Real en BD | Estado |
|----------------|------------------|--------|
| `proveedor_nombre` | `proveedor_text` | ⚠️ **Ajustar** |
| `importe_base` | `base_imponible` | ⚠️ **Ajustar** |
| `importe_iva` | `impuestos_total` | ⚠️ **Ajustar** |
| `numero_factura` | `numero_factura` | ✅ Correcto |
| `fecha_emision` | `fecha_emision` | ✅ Correcto |
| `importe_total` | `importe_total` | ✅ Correcto |

### Estructura de Tablas

**Tabla `facturas`:**
- `id` (BigInteger, PK)
- `proveedor_id` (FK a `proveedores.id`)
- `proveedor_text` (Text) - Nombre del proveedor
- `numero_factura` (Text)
- `fecha_emision` (Date)
- `base_imponible` (DECIMAL) - Base imponible
- `impuestos_total` (DECIMAL) - Total de impuestos (IVA)
- `importe_total` (DECIMAL)
- `confianza` (Text: 'alta', 'media', 'baja')
- `estado` (Text: 'procesado', 'pendiente', 'error', 'revisar', 'duplicado')
- `extractor` (Text: 'openai', 'tesseract')
- `tiempo_promedio_ocr` - No existe directamente, se calcula

**Tabla `proveedores`:**
- `id` (Integer, PK)
- `nombre` (Text, unique)
- `nif_cif` (Text)

---

## 🎯 Plan de Implementación

### Fase 1: Backend API (FastAPI)

#### 1.1 Crear estructura de API

**Archivos a crear:**
```
src/
├── api/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app principal
│   ├── dependencies.py            # Dependencias (DB, auth)
│   └── routes/
│       ├── __init__.py
│       ├── facturas.py            # Endpoints de facturas
│       └── system.py              # Endpoints de sistema
```

#### 1.2 Implementar endpoints

**Nota**: Se eliminaron referencias a `tiempo_promedio_ocr` y estado de servicios según decisiones técnicas.

**Endpoint: `GET /api/facturas/summary?month=11&year=2025`**
- **Funcionalidad**: Resumen de facturas del mes
- **Campos a retornar**:
  - `total_facturas`: Total de facturas del mes
  - `facturas_exitosas`: Facturas con estado='procesado'
  - `facturas_fallidas`: Facturas con estado IN ('error', 'revisar')
  - `importe_total`: SUM(importe_total) del mes
  - `promedio_factura`: AVG(importe_total) del mes
  - `proveedores_activos`: COUNT(DISTINCT proveedor_text) del mes
  - `confianza_extraccion`: AVG(confianza) convertido a porcentaje (alta=100%, media=50%, baja=25%)

**Endpoint: `GET /api/facturas/by_day?month=11&year=2025`**
- **Funcionalidad**: Facturas agrupadas por día
- **Campos a retornar**:
  - `dia`: Día del mes (1-31)
  - `cantidad`: COUNT(*) por día
  - `importe_total`: SUM(importe_total) por día
  - `importe_iva`: SUM(impuestos_total) por día (mapear de `impuestos_total`)

**Endpoint: `GET /api/facturas/recent?month=11&year=2025&limit=5`**
- **Funcionalidad**: Facturas recientes del mes
- **Campos a retornar**:
  - `id`: Factura.id
  - `numero_factura`: Factura.numero_factura
  - `proveedor_nombre`: Factura.proveedor_text (mapear nombre)
  - `fecha_emision`: Factura.fecha_emision (ISO format)
  - `importe_base`: Factura.base_imponible (mapear nombre)
  - `importe_iva`: Factura.impuestos_total (mapear nombre)
  - `importe_total`: Factura.importe_total

**Endpoint: `GET /api/facturas/categories?month=11&year=2025`**
- **Funcionalidad**: Desglose por categorías
- **Nota**: No hay campo `categoria` en BD. Opciones:
  - Agrupar por `proveedor_text` (recomendado)
  - Agrupar por `confianza`
  - Agrupar por `extractor`
- **Campos a retornar**:
  - `categoria`: Nombre de la categoría (ej: proveedor_text)
  - `cantidad`: COUNT(*) por categoría
  - `importe_total`: SUM(importe_total) por categoría

**Endpoint: `GET /api/system/sync-status`** (Opcional - solo si se necesita mostrar última sincronización)
- **Funcionalidad**: Estado de sincronización con Drive
- **Campos a retornar**:
  - `last_sync`: Timestamp ISO de última sincronización desde `SyncState` (key: 'drive_last_sync_time')
  - `updated_at`: Fecha de última actualización del estado

#### 1.3 Crear repositorios adicionales

**Métodos a agregar en `FacturaRepository`:**
- `get_summary_by_month(month: int, year: int) -> dict`
- `get_facturas_by_day(month: int, year: int) -> List[dict]`
- `get_recent_facturas(month: int, year: int, limit: int) -> List[dict]`
- `get_categories_breakdown(month: int, year: int) -> List[dict]`

#### 1.4 Esquemas Pydantic

**Archivo: `src/api/schemas/facturas.py`**
- `FacturaSummaryResponse`
- `FacturaByDayResponse`
- `FacturaRecentResponse`
- `CategoryBreakdownResponse`
- `SystemStatusResponse`

---

### Fase 2: Frontend React

#### 2.1 Setup del proyecto

**Comandos:**
```bash
cd /home/alex/proyectos/invoice-extractor
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install tailwindcss postcss autoprefixer
npm install recharts lucide-react
npx tailwindcss init -p
```

#### 2.2 Estructura de carpetas

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx
│   │   ├── Header.jsx
│   │   ├── KPIGrid.jsx
│   │   ├── KPICard.jsx
│   │   ├── ChartSection.jsx
│   │   ├── AnalysisGrid.jsx
│   │   ├── QualityPanel.jsx
│   │   ├── CategoriesPanel.jsx
│   │   ├── StatusBar.jsx              # Opcional (solo si se necesita mostrar última sincronización)
│   │   ├── LoadingSpinner.jsx
│   │   └── ErrorBoundary.jsx
│   ├── hooks/
│   │   └── useInvoiceData.js
│   ├── utils/
│   │   ├── formatters.js
│   │   ├── constants.js
│   │   └── api.js
│   ├── App.jsx
│   └── index.css
├── package.json
├── tailwind.config.js
└── vite.config.js
```

#### 2.3 Componentes a implementar

**Orden de implementación:**

1. **Utils y helpers** (base)
   - `formatters.js`: formatCurrency, formatNumber, formatPercentage, formatDate
   - `constants.js`: MONTH_NAMES, MONTH_NAMES_SHORT
   - `api.js`: Cliente API con fetch wrappers

2. **Hooks**
   - `useInvoiceData.js`: Hook personalizado para fetch de datos

3. **Componentes base**
   - `ErrorBoundary.jsx`: Manejo de errores
   - `LoadingSpinner.jsx`: Spinner de carga
   - `KPICard.jsx`: Card individual de KPI

4. **Componentes principales**
   - `Header.jsx`: Header con selector de mes
   - `KPIGrid.jsx`: Grid de 4 KPIs
   - `ChartSection.jsx`: Gráficos con Recharts
   - `QualityPanel.jsx`: Panel de calidad (sin tiempo OCR)
   - `CategoriesPanel.jsx`: Panel de categorías (agrupado por proveedor_text)
   - `AnalysisGrid.jsx`: Grid con ambos paneles

5. **Componente principal**
   - `Dashboard.jsx`: Orquestador principal

#### 2.4 Mapeo de campos API → Frontend

**Ajustes necesarios en el frontend:**

```javascript
// En useInvoiceData.js o api.js
function transformApiResponse(apiData) {
  return {
    summary: {
      total_facturas: apiData.total_facturas,
      facturas_exitosas: apiData.facturas_exitosas,
      facturas_fallidas: apiData.facturas_fallidas,
      importe_total: apiData.importe_total,
      promedio_factura: apiData.promedio_factura,
      proveedores_activos: apiData.proveedores_activos,
      confianza_extraccion: apiData.confianza_extraccion
    },
    byDay: apiData.byDay.map(item => ({
      dia: item.dia,
      cantidad: item.cantidad,
      importe_total: item.importe_total,
      importe_iva: item.importe_iva, // Viene como importe_iva del endpoint
      // Para el gráfico, usar estos campos
    })),
    recent: apiData.recent.map(item => ({
      id: item.id,
      numero_factura: item.numero_factura,
      proveedor_nombre: item.proveedor_nombre, // Viene mapeado desde proveedor_text
      fecha_emision: item.fecha_emision,
      importe_base: item.importe_base, // Viene mapeado desde base_imponible
      importe_iva: item.importe_iva, // Viene mapeado desde impuestos_total
      importe_total: item.importe_total
    })),
    categories: apiData.categories
  };
}
```

---

### Fase 3: Configuración y Testing

#### 3.1 Variables de entorno

**.env (Backend):**
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/invoice_db
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**.env (Frontend):**
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

#### 3.2 Testing

**Backend:**
- Tests unitarios de repositorios
- Tests de integración de endpoints
- Coverage ≥80%

**Frontend:**
- Tests de componentes con React Testing Library
- Tests de hooks
- Tests E2E con Playwright (opcional)

---

## ✅ Decisiones Técnicas Resueltas

### 1. Categorías de facturas
**Decisión**: Agrupar por `proveedor_text` (más útil para análisis)

### 2. Tiempo promedio OCR
**Decisión**: ❌ **NO incluir** en el dashboard

### 3. Estado de servicios
**Decisión**: ❌ **NO incluir** en el dashboard

### 4. Sincronización con Drive
**Decisión**: ✅ Usar `SyncState` table con key `'drive_last_sync_time'`
- Campo `value`: Timestamp ISO de última sincronización
- Campo `updated_at`: Se actualiza automáticamente
- **Suficiente** para mostrar última sincronización

---

## 📝 Checklist de Implementación

### Backend (FastAPI)
- [ ] Crear estructura `src/api/`
- [ ] Implementar `main.py` con FastAPI app
- [ ] Crear `dependencies.py` (DB session, CORS)
- [ ] Implementar `routes/facturas.py` con 4 endpoints (summary, by_day, recent, categories)
- [ ] Implementar `routes/system.py` con sync-status (opcional)
- [ ] Agregar métodos al `FacturaRepository`
- [ ] Crear schemas Pydantic
- [ ] Configurar CORS para frontend
- [ ] Agregar manejo de errores
- [ ] Tests unitarios de repositorios
- [ ] Tests de integración de endpoints
- [ ] Documentación OpenAPI/Swagger

### Frontend (React)
- [ ] Setup proyecto Vite + React
- [ ] Configurar Tailwind CSS
- [ ] Instalar dependencias (recharts, lucide-react)
- [ ] Crear estructura de carpetas
- [ ] Implementar `utils/formatters.js`
- [ ] Implementar `utils/constants.js`
- [ ] Implementar `utils/api.js`
- [ ] Implementar `hooks/useInvoiceData.js`
- [ ] Implementar `components/ErrorBoundary.jsx`
- [ ] Implementar `components/LoadingSpinner.jsx`
- [ ] Implementar `components/KPICard.jsx`
- [ ] Implementar `components/Header.jsx`
- [ ] Implementar `components/KPIGrid.jsx`
- [ ] Implementar `components/ChartSection.jsx`
- [ ] Implementar `components/QualityPanel.jsx` (sin tiempo OCR)
- [ ] Implementar `components/CategoriesPanel.jsx` (agrupado por proveedor_text)
- [ ] Implementar `components/AnalysisGrid.jsx`
- [ ] Implementar `components/Dashboard.jsx`
- [ ] Configurar `App.jsx` con ErrorBoundary
- [ ] Agregar estilos globales (index.css)
- [ ] Testing de componentes
- [ ] Validación responsive (móvil, tablet, desktop)
- [ ] Optimización de performance (memo, useMemo, useCallback)

### Integración
- [ ] Configurar variables de entorno
- [ ] Probar conexión Backend ↔ Frontend
- [ ] Validar mapeo de campos
- [ ] Probar cambio de mes
- [ ] Validar estados de carga y error
- [ ] Probar responsive design
- [ ] Validar accesibilidad (ARIA labels)

---

## 🚀 Orden de Ejecución Recomendado

1. **Día 1: Backend API**
   - Crear estructura FastAPI
   - Implementar endpoints básicos
   - Agregar métodos al repositorio
   - Testing básico

2. **Día 2: Frontend Base**
   - Setup proyecto React
   - Implementar utils y hooks
   - Crear componentes base (Loading, ErrorBoundary, KPICard)

3. **Día 3: Frontend Componentes**
   - Header y KPIGrid
   - ChartSection con Recharts
   - AnalysisGrid (Quality + Categories)

4. **Día 4: Frontend Finalización**
   - Dashboard principal
   - Integración completa

5. **Día 5: Testing y Polish**
   - Tests unitarios
   - Tests de integración
   - Ajustes responsive
   - Optimizaciones de performance

---

## 📊 Métricas de Éxito

- ✅ Todos los endpoints retornan datos correctos
- ✅ Frontend consume API sin errores
- ✅ Cambio de mes funciona correctamente
- ✅ Gráficos se renderizan con datos reales
- ✅ Responsive funciona en móvil, tablet y desktop
- ✅ Cobertura de tests ≥80%
- ✅ Performance: First Contentful Paint < 1.5s
- ✅ Accesibilidad: WCAG AA compliance

---

## 🔗 Referencias

- **Modelos DB**: `src/db/models.py`
- **Repositorios**: `src/db/repositories.py`
- **Dashboard actual**: `src/dashboard/app.py` (Streamlit)

---

**Fecha de creación**: 2025-01-XX
**Última actualización**: 2025-01-XX

