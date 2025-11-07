# Detalles Técnicos del Dashboard de Facturación

**Versión**: 1.0.0  
**Fecha**: 2025-11-05  
**Proyecto**: Invoice Extractor

---

## 📐 Arquitectura del Sistema

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Dashboard   │──│  Components  │──│    Hooks    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                          │                                │
│                    ┌─────▼─────┐                          │
│                    │   API.js  │                          │
│                    └─────┬─────┘                          │
└──────────────────────────┼────────────────────────────────┘
                           │ HTTP/REST
                           │
┌──────────────────────────▼────────────────────────────────┐
│              Backend (FastAPI)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Routes     │──│  Dependencies │──│   Schemas     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘          │
│                          │                                │
│                    ┌─────▼─────┐                          │
│                    │Repository │                          │
│                    └─────┬─────┘                          │
└──────────────────────────┼────────────────────────────────┘
                           │
                           │ SQLAlchemy ORM
                           │
┌──────────────────────────▼────────────────────────────────┐
│              PostgreSQL Database                          │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │  facturas   │  │  proveedores │                       │
│  └──────────────┘  └──────────────┘                       │
└────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend: FastAPI

### Estructura de Archivos

```
src/api/
├── __init__.py
├── main.py                    # Aplicación FastAPI principal
├── dependencies.py            # Dependencias inyectadas
├── routes/
│   ├── __init__.py
│   ├── facturas.py           # Endpoints de facturas
│   └── system.py             # Endpoints de sistema
└── schemas/
    ├── __init__.py
    └── facturas.py           # Schemas Pydantic
```

### Endpoints Detallados

#### 1. GET /api/facturas/summary

**Query Parameters:**
- `month` (int, required): 1-12
- `year` (int, required): 2000-2100

**Response Schema:**
```python
{
  "total_facturas": int,
  "facturas_exitosas": int,
  "facturas_fallidas": int,
  "importe_total": float,
  "promedio_factura": float,
  "proveedores_activos": int,
  "confianza_extraccion": float  # 0-100%
}
```

**Lógica de Negocio:**
- Filtra facturas por `fecha_emision` en el rango del mes
- Cuenta exitosas: `estado == 'procesado'`
- Cuenta fallidas: `estado IN ('error', 'revisar')`
- Calcula confianza: alta=100%, media=50%, baja=25%

**SQL Ejecutado:**
```sql
SELECT 
  COUNT(*) as total_facturas,
  COUNT(*) FILTER (WHERE estado = 'procesado') as facturas_exitosas,
  COUNT(*) FILTER (WHERE estado IN ('error', 'revisar')) as facturas_fallidas,
  SUM(importe_total) as importe_total,
  AVG(importe_total) as promedio_factura,
  COUNT(DISTINCT proveedor_text) as proveedores_activos
FROM facturas
WHERE fecha_emision >= '2025-11-01' 
  AND fecha_emision <= '2025-11-30';
```

#### 2. GET /api/facturas/by_day

**Query Parameters:**
- `month` (int, required): 1-12
- `year` (int, required): 2000-2100

**Response Schema:**
```python
{
  "data": [
    {
      "dia": int,           # 1-31
      "cantidad": int,
      "importe_total": float,
      "importe_iva": float
    }
  ]
}
```

**Lógica:**
- Agrupa por día del mes usando `EXTRACT(day FROM fecha_emision)`
- Retorna todos los días del mes (incluso sin facturas: cantidad=0)
- Ordena por día ascendente

#### 3. GET /api/facturas/recent

**Query Parameters:**
- `month` (int, required): 1-12
- `year` (int, required): 2000-2100
- `limit` (int, optional): 1-100 (default: 5)

**Response Schema:**
```python
{
  "data": [
    {
      "id": int,
      "numero_factura": str | null,
      "proveedor_nombre": str | null,
      "fecha_emision": date | null,
      "importe_base": float | null,
      "importe_iva": float | null,
      "importe_total": float | null
    }
  ]
}
```

**Ordenamiento:**
- Primero por `fecha_emision` DESC
- Luego por `creado_en` DESC

#### 4. GET /api/facturas/categories

**Query Parameters:**
- `month` (int, required): 1-12
- `year` (int, required): 2000-2100

**Response Schema:**
```python
{
  "data": [
    {
      "categoria": str,      # proveedor_text
      "cantidad": int,
      "importe_total": float
    }
  ]
}
```

**Lógica:**
- Agrupa por `proveedor_text`
- Ordena por `importe_total` DESC
- Excluye facturas sin proveedor_text

#### 5. GET /api/system/sync-status

**Response Schema:**
```python
{
  "last_sync": str | null,      # ISO timestamp
  "updated_at": str | null      # ISO timestamp
}
```

**Fuente de Datos:**
- Tabla `sync_state` con key `'drive_last_sync_time'`

---

## 🎨 Frontend: React

### Estructura de Componentes

```
components/
├── Dashboard.jsx              # Orquestador principal
├── Header.jsx                 # Header + selector de mes
├── KPIGrid.jsx                # Grid de 4 KPIs
├── KPICard.jsx                # Card individual de KPI
├── ChartSection.jsx           # Gráficos con Recharts
├── AnalysisGrid.jsx           # Grid de análisis
├── QualityPanel.jsx           # Panel de calidad
├── CategoriesPanel.jsx         # Tabla de categorías
├── LoadingSpinner.jsx         # Spinner de carga
└── ErrorBoundary.jsx         # Manejo de errores
```

### Flujo de Datos

```
Dashboard
  └─> useInvoiceData(month, year)
      └─> fetchInvoiceSummary()
      └─> fetchInvoicesByDay()
      └─> fetchRecentInvoices()
      └─> fetchCategoriesBreakdown()
      └─> Promise.all([...])  // Fetch paralelo
          └─> Transforma datos
              └─> setData({ summary, kpis, chartData, ... })
                  └─> Renderiza componentes
                      ├─> KPIGrid(data.kpis)
                      ├─> ChartSection(data.chartData)
                      └─> AnalysisGrid(data.quality, data.categories)
```

### Hook Personalizado: useInvoiceData

**Propósito:**
- Centralizar lógica de fetching
- Manejar estados: loading, error, data
- Re-fetch automático al cambiar month/year

**Implementación:**
```javascript
export function useInvoiceData(month, year) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch paralelo de todos los endpoints
    Promise.all([...])
      .then(([summary, byDay, recent, categories]) => {
        setData({
          summary,
          kpis: transformToKPIs(summary),
          chartData: byDay,
          recent,
          quality: extractQualityMetrics(summary),
          categories
        });
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [month, year]);

  return { data, loading, error };
}
```

### Componente: KPICard

**Props:**
```typescript
interface KPICardProps {
  icon: string;           // Emoji o ícono
  value: number | string; // Valor a mostrar
  label: string;          // Etiqueta descriptiva
  change?: number;        // Cambio porcentual (opcional)
  background: string;     // Color de fondo del ícono
  type?: 'number' | 'currency' | 'percentage';
}
```

**Características:**
- Barra superior con gradiente
- Ícono con fondo personalizado
- Badge de cambio con ícono de tendencia
- Hover effect con transform y shadow
- Memoizado con `React.memo`

### Componente: ChartSection

**Librería:** Recharts

**Tres Vistas:**
1. **Importes**: AreaChart con gradiente morado
2. **Cantidad**: BarChart con barras moradas
3. **IVA**: AreaChart con gradiente púrpura oscuro

**Tooltip Personalizado:**
- Muestra día, valor formateado
- Estilo: fondo blanco, borde, sombra

**Configuración:**
- ResponsiveContainer: 100% width, 300px height
- CartesianGrid: strokeDasharray="3 3"
- XAxis/YAxis: colores personalizados (#94a3b8)

### Componente: QualityPanel

**Métricas Mostradas:**
1. Facturas exitosas: Badge verde con checkmark
2. Facturas fallidas: Badge amarillo con warning
3. Confianza extracción: Texto verde con porcentaje

**Estructura:**
- Título con emoji
- 3 filas con label, detail y valor
- Separador entre filas (border-bottom)

### Componente: CategoriesPanel

**Tabla HTML:**
- 3 columnas: Concepto, Cantidad, Importe
- Fila por cada proveedor
- Ordenado por importe_total DESC

**Estilos:**
- Header: border-bottom-2, font-semibold
- Filas: border-bottom-1, padding vertical
- Importe: color morado, font-bold

---

## 🎨 Diseño y Estilos

### Paleta de Colores

```css
/* Gradientes */
--gradient-main: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-active: linear-gradient(135deg, #667eea, #764ba2);

/* Textos */
--text-primary: #1e293b
--text-secondary: #64748b
--text-muted: #94a3b8

/* Backgrounds */
--bg-card: #ffffff
--bg-light: #f8fafc
--bg-lighter: #f1f5f9

/* Estados */
--success: #10b981
--success-bg: #d1fae5
--warning: #f59e0b
--warning-bg: #fef3c7
```

### Sombras Personalizadas

```css
--shadow-card: 0 10px 30px rgba(0,0,0,0.08)
--shadow-card-hover: 0 20px 40px rgba(0,0,0,0.12)
--shadow-header: 0 20px 60px rgba(0,0,0,0.1)
--shadow-button-active: 0 4px 12px rgba(102, 126, 234, 0.4)
```

### Border Radius

```css
--radius-sm: 8px
--radius-md: 12px
--radius-lg: 16px
--radius-xl: 20px
```

### Tipografía

- **Fuente**: Inter (Google Fonts)
- **Tamaños**:
  - h1: 2rem (32px), font-weight: 700
  - h2: 1.5rem (24px), font-weight: 600
  - h3: 1.25rem (20px), font-weight: 600
  - body: 1rem (16px), font-weight: 400
  - small: 0.85rem (13.6px)

---

## 📱 Responsive Design

### Breakpoints

```javascript
// Móvil: < 768px
// Tablet: 768px - 1024px
// Desktop: > 1024px
```

### Ajustes por Componente

**Header:**
- Móvil: `flex-col` (stack vertical)
- Desktop: `flex-row` (horizontal)

**KPIGrid:**
- Móvil: `grid-cols-1`
- Tablet: `sm:grid-cols-2`
- Desktop: `lg:grid-cols-4`

**AnalysisGrid:**
- Móvil: `grid-cols-1`
- Desktop: `lg:grid-cols-2`

**Month Selector:**
- Móvil: `overflow-x-auto` (scroll horizontal)
- Desktop: `overflow-x-visible`

---

## 🔄 Flujo de Datos Completo

### 1. Usuario selecciona mes

```
Usuario click en botón "Nov"
  └─> onMonthChange(11)
      └─> setSelectedMonth(11)
          └─> useInvoiceData(11, 2025) detecta cambio
              └─> useEffect ejecuta fetchData()
```

### 2. Fetch de datos

```
fetchData()
  └─> Promise.all([
        fetchInvoiceSummary(11, 2025),
        fetchInvoicesByDay(11, 2025),
        fetchRecentInvoices(11, 2025),
        fetchCategoriesBreakdown(11, 2025)
      ])
      └─> Cada fetch hace HTTP GET al backend
          └─> Backend ejecuta queries SQL
              └─> Retorna JSON
                  └─> Frontend transforma datos
                      └─> setData({ ... })
```

### 3. Renderizado

```
data actualizado
  └─> Dashboard re-renderiza
      ├─> KPIGrid recibe data.kpis
      ├─> ChartSection recibe data.chartData
      └─> AnalysisGrid recibe data.quality, data.categories
          └─> Componentes renderizan UI actualizada
```

---

## 🗄️ Base de Datos

### Consultas Principales

#### Resumen por Mes
```sql
SELECT 
  COUNT(*) as total_facturas,
  COUNT(*) FILTER (WHERE estado = 'procesado') as facturas_exitosas,
  COUNT(*) FILTER (WHERE estado IN ('error', 'revisar')) as facturas_fallidas,
  SUM(importe_total) as importe_total,
  AVG(importe_total) as promedio_factura,
  COUNT(DISTINCT proveedor_text) as proveedores_activos
FROM facturas
WHERE fecha_emision >= :start_date 
  AND fecha_emision <= :end_date;
```

#### Agrupación por Día
```sql
SELECT 
  EXTRACT(day FROM fecha_emision) as dia,
  COUNT(*) as cantidad,
  SUM(importe_total) as importe_total,
  SUM(impuestos_total) as importe_iva
FROM facturas
WHERE fecha_emision >= :start_date 
  AND fecha_emision <= :end_date
GROUP BY EXTRACT(day FROM fecha_emision)
ORDER BY dia;
```

#### Categorías (Proveedores)
```sql
SELECT 
  proveedor_text as categoria,
  COUNT(*) as cantidad,
  SUM(importe_total) as importe_total
FROM facturas
WHERE fecha_emision >= :start_date 
  AND fecha_emision <= :end_date
  AND proveedor_text IS NOT NULL
GROUP BY proveedor_text
ORDER BY SUM(importe_total) DESC;
```

---

## 🚀 Performance

### Optimizaciones Implementadas

1. **Memoización de Componentes:**
   - `KPICard` con `React.memo`
   - Evita re-renders innecesarios

2. **Fetch Paralelo:**
   - `Promise.all()` para todos los endpoints
   - Reduce tiempo total de carga

3. **useMemo para Datos Calculados:**
   - `chartData` memoizado en ChartSection
   - Solo recalcula si `data` cambia

4. **Lazy Loading (Futuro):**
   - Componentes pesados se pueden lazy load
   - No implementado aún

### Métricas Esperadas

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **API Response Time**: < 200ms
- **Bundle Size**: ~500KB (gzipped)

---

## 🧪 Testing (Pendiente)

### Tests Recomendados

**Backend:**
```python
# tests/test_facturas_endpoints.py
def test_get_summary_success()
def test_get_summary_invalid_month()
def test_get_by_day_empty_month()
```

**Frontend:**
```javascript
// __tests__/KPICard.test.jsx
test('renderiza correctamente los datos')
test('formatea moneda correctamente')
test('muestra badge de cambio')
```

---

## 📦 Dependencias

### Backend

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9
```

### Frontend

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "recharts": "^2.10.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    "vite": "^5.0.0"
  }
}
```

---

## 🔐 Seguridad

### Implementado

- ✅ CORS configurado con orígenes específicos
- ✅ Validación de inputs con Pydantic
- ✅ Manejo de errores sin exponer stack traces
- ✅ SQL injection prevention (ORM con queries parametrizadas)

### Recomendaciones Futuras

- [ ] Autenticación JWT
- [ ] Rate limiting
- [ ] HTTPS en producción
- [ ] Validación de permisos por usuario

---

## 📝 Variables de Entorno

### Backend (.env)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/invoice_db
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 🐛 Troubleshooting

### Problemas Comunes

**1. Error de conexión a API**
- Verificar que backend esté corriendo en puerto 8000
- Revisar CORS origins en backend
- Verificar `VITE_API_BASE_URL` en frontend

**2. Datos no se cargan**
- Verificar que haya facturas en el mes seleccionado
- Revisar logs del backend
- Verificar conexión a base de datos

**3. Gráficos no se renderizan**
- Verificar que Recharts esté instalado
- Revisar console para errores de datos
- Verificar que `chartData` tenga formato correcto

---

## 📚 Referencias

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Recharts Docs**: https://recharts.org/
- **Tailwind CSS**: https://tailwindcss.com/
- **React Hooks**: https://react.dev/reference/react

---

**Última actualización**: 2025-11-05  
**Versión del documento**: 1.0.0

