# Arquitectura del Sistema Invoice Extractor - Documentación para Multi-Sucursal

**Fecha de creación:** 2025-12-11  
**Última actualización:** 2026-01-22  
**Propósito:** Documentación técnica completa del sistema actual para diseñar plan de implementación multi-sucursal  
**Versión del Sistema:** 1.1.0 (incluye módulo de Costos de Personal)

---

## 📋 Resumen Ejecutivo

### Sistema Actual
Sistema de extracción y gestión automática de facturas que:
- Sincroniza facturas desde Google Drive (carpetas mensuales)
- Extrae datos mediante OCR (Tesseract) + LLM (OpenAI)
- Almacena en PostgreSQL (`negocio_db`)
- Proporciona dashboard web (React + React-admin)
- API REST (FastAPI) para todas las operaciones
- Gestiona ingresos y costos de personal mensuales
- Genera análisis de rentabilidad integrado

### Requerimiento Nuevo
El cliente abrió una segunda sucursal y necesita:
- **Mismo frontend** para ambas sucursales
- **Selector de sucursal** en el frontend
- **Datos separados** por sucursal (facturas, proveedores, reportes)
- **Misma base de datos** (no crear proyecto separado)
- **Mismo Google Drive** pero con carpetas separadas por sucursal

### Objetivo del Documento
Proporcionar toda la información técnica necesaria para diseñar un plan de implementación que permita:
1. Agregar soporte multi-sucursal sin romper funcionalidad existente
2. Mantener el mismo frontend con selector de sucursal
3. Filtrar todos los datos por sucursal seleccionada
4. Soportar múltiples carpetas de Google Drive (una por sucursal)

---

## 🏗️ Arquitectura General

### Diagrama de Arquitectura Actual

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Drive                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Carpeta Base: GOOGLE_DRIVE_FOLDER_ID                │   │
│  │    ├── agosto/    (facturas de agosto)               │   │
│  │    ├── septiembre/ (facturas de septiembre)          │   │
│  │    └── octubre/   (facturas de octubre)              │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DriveClient (Google Drive API)                  │
│  - Service Account OAuth2                                    │
│  - Búsqueda recursiva de PDFs                               │
│  - Descarga de archivos                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Pipeline de Procesamiento                       │
│  ┌─────────────────────────────────────────────┐           │
│  │  1. Descarga PDF → temp/                     │           │
│  │  2. Validación (magic bytes %PDF-)           │           │
│  │  3. OCR Extraction:                          │           │
│  │     - Primario: OpenAI GPT-4o                │           │
│  │     - Fallback: Tesseract OCR                │           │
│  │  4. Normalización (fechas, importes)          │           │
│  │  5. Validación de reglas de negocio          │           │
│  │  6. Detección de duplicados (hash SHA256)    │           │
│  │  7. UPSERT en PostgreSQL                     │           │
│  └─────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL (negocio_db)                          │
│  ┌─────────────────────────────────────────────┐           │
│  │  Tablas:                                     │           │
│  │  - facturas (principal)                      │           │
│  │  - proveedores (legacy)                       │           │
│  │  - proveedores_maestros (normalizados)        │           │
│  │  - categorias                                │           │
│  │  - ingest_events (auditoría)                  │           │
│  │  - sync_state (sincronización)                │           │
│  │  - ingresos_mensuales (rentabilidad)          │           │
│  │  - costos_personal (costos mensuales)         │           │
│  └─────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Puerto 8002)                   │
│  ┌─────────────────────────────────────────────┐           │
│  │  Endpoints REST:                             │           │
│  │  - /api/facturas/*                          │           │
│  │  - /api/proveedores/*                       │           │
│  │  - /api/system/*                            │           │
│  │  - /api/categorias/*                        │           │
│  │  - /api/ingresos/*                          │           │
│  │  - /api/costos-personal/*                   │           │
│  │  - /api/auth/*                             │           │
│  └─────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              React Frontend (React-admin)                    │
│  ┌─────────────────────────────────────────────┐           │
│  │  Secciones:                                  │           │
│  │  - Dashboard (KPIs, gráficos, tabla)         │           │
│  │  - Pendientes (facturas con problemas)       │           │
│  │  - Reportes (análisis, rentabilidad)         │           │
│  │  - Proveedores (gestión + categorías)        │           │
│  │  - Datos (estadísticas + categorías)         │           │
│  │  - Categorías (gestión centralizada)         │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Datos Actual

1. **Sincronización Drive → BD:**
   - Script `src/main.py` ejecuta periódicamente (cron o manual)
   - `DriveClient` busca PDFs en carpetas mensuales (agosto, septiembre, etc.)
   - Para cada PDF nuevo:
     - Descarga a `temp/`
     - Extrae datos con OCR
     - Valida y normaliza
     - Detecta duplicados
     - UPSERT en tabla `facturas`

2. **Frontend → Backend:**
   - Usuario accede a `https://alexforge.online/invoice-dashboard`
   - React-admin hace requests a `/invoice-api/api/*`
   - Backend consulta PostgreSQL y retorna JSON
   - Frontend renderiza datos en tablas, gráficos, etc.

3. **Autenticación:**
   - Sistema de sesiones con cookies
   - Middleware `AuthMiddleware` protege rutas `/api/*`
   - Rutas públicas: `/healthz`, `/docs`, `/api/auth/*`

---

## 🛠️ Stack Tecnológico

### Backend

| Componente | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.12 | Lenguaje principal |
| **FastAPI** | 0.104.1 | Framework web REST |
| **Uvicorn** | Latest | ASGI server |
| **SQLAlchemy** | 2.0.23 | ORM para PostgreSQL |
| **PostgreSQL** | 15+ | Base de datos relacional |
| **Pydantic** | Latest | Validación de datos y schemas |
| **python-dotenv** | Latest | Variables de entorno |

### Frontend

| Componente | Versión | Propósito |
|------------|---------|-----------|
| **React** | 19.1.1 | Framework UI |
| **Vite** | 7.1.7 | Build tool y dev server |
| **React-Admin** | 5.13.1 | Framework de admin panel |
| **Material-UI** | 7.3.5 | Componentes UI |
| **Recharts** | 3.3.0 | Gráficos y visualizaciones |
| **Lucide React** | 0.552.0 | Iconos |
| **TailwindCSS** | 3.4.18 | Estilos utilitarios |
| **date-fns** | 4.1.0 | Manipulación de fechas |

### Procesamiento

| Componente | Versión | Propósito |
|------------|---------|-----------|
| **OpenAI API** | Latest | Extracción de datos de facturas (GPT-4o) |
| **Tesseract OCR** | Latest | Fallback OCR |
| **pdf2image** | Latest | Conversión PDF → Imagen |
| **pypdf** | Latest | Procesamiento PDF |
| **pytesseract** | Latest | Wrapper Python para Tesseract |

### Infraestructura

| Componente | Propósito |
|------------|-----------|
| **Docker** | Contenedores para backend y frontend |
| **Docker Compose** | Orquestación de servicios |
| **Traefik** | Reverse proxy con SSL/TLS automático |
| **PostgreSQL** | Base de datos (local o contenedor) |

---

## 🗄️ Estructura de Base de Datos

### Base de Datos: `negocio_db`

**Conexión:**
```
postgresql://extractor_user:Dagoba50dago-@localhost:5432/negocio_db
```

### Tablas Principales

#### 1. `facturas` (Tabla Principal)

**Propósito:** Almacena todas las facturas procesadas

**Campos Clave:**
```sql
id                  BIGSERIAL PRIMARY KEY
drive_file_id       TEXT NOT NULL UNIQUE        -- ID único en Google Drive
drive_file_name     TEXT NOT NULL               -- Nombre del archivo
drive_folder_name   TEXT NOT NULL               -- Carpeta mensual (agosto, septiembre, etc.)
drive_modified_time TIMESTAMP                   -- Última modificación en Drive

-- Datos de factura
proveedor_id        BIGINT FK(proveedores.id)
proveedor_text      TEXT                        -- Nombre del proveedor (texto)
proveedor_maestro_id INTEGER FK(proveedores_maestros.id)
numero_factura      TEXT
moneda              TEXT DEFAULT 'EUR'          -- ISO 3 chars
fecha_emision       DATE
fecha_recepcion     TIMESTAMP

-- Datos financieros
base_imponible      DECIMAL(18,2)
impuestos_total     DECIMAL(18,2)
iva_porcentaje      DECIMAL(5,2)
importe_total       DECIMAL(18,2)               -- NULL permitido

-- Metadata
conceptos_json      JSONB                       -- Conceptos de la factura
metadatos_json      JSONB                       -- Metadata adicional
pagina_analizada    INTEGER DEFAULT 1
extractor           TEXT NOT NULL               -- 'openai' o 'tesseract'
confianza           TEXT                        -- 'alta', 'media', 'baja'
hash_contenido      TEXT                        -- SHA256 para detección duplicados
revision            INTEGER DEFAULT 1

-- Estado y control
estado              TEXT DEFAULT 'procesado'    -- 'procesado', 'pendiente', 'error', 'revisar', 'duplicado', 'error_permanente'
error_msg           TEXT
reprocess_attempts  INTEGER DEFAULT 0
reprocessed_at      TIMESTAMP
reprocess_reason    TEXT
deleted_from_drive  BOOLEAN DEFAULT FALSE

-- Timestamps
creado_en           TIMESTAMP DEFAULT now()
actualizado_en      TIMESTAMP DEFAULT now()
```

**Índices:**
- `idx_facturas_hash_contenido_unique` (hash_contenido) - Único para duplicados
- `idx_facturas_proveedor_numero` (proveedor_text, numero_factura)
- `idx_facturas_estado` (estado)
- `idx_facturas_drive_modified` (drive_modified_time)
- `idx_facturas_deleted` (deleted_from_drive) - Parcial

**Constraints:**
- `check_moneda_length`: moneda debe ser 3 caracteres
- `check_base_imponible_positive`: base_imponible >= 0
- `check_impuestos_positive`: impuestos_total >= 0
- `check_confianza_values`: confianza IN ('alta', 'media', 'baja')
- `check_estado_values`: estado IN ('procesado', 'pendiente', 'error', 'revisar', 'duplicado', 'error_permanente')

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **NO existe campo `sucursal_id` o similar**
- **NO hay separación por sucursal actualmente**
- **Todas las facturas están en la misma tabla sin distinción**

---

#### 2. `proveedores` (Legacy)

**Propósito:** Tabla legacy de proveedores (mantener para compatibilidad)

```sql
id              SERIAL PRIMARY KEY
nombre          TEXT NOT NULL UNIQUE
categoria       TEXT                        -- Categoría asignada
nif_cif         TEXT
email_contacto  TEXT
creado_en       TIMESTAMP DEFAULT now()

-- Relación
facturas        relationship("Factura", back_populates="proveedor")
```

**⚠️ IMPORTANTE:**
- Esta tabla es legacy, pero aún se usa
- `proveedores_maestros` es la tabla principal actual

---

#### 3. `proveedores_maestros` (Principal)

**Propósito:** Proveedores normalizados y unificados

```sql
id                      SERIAL PRIMARY KEY
nombre_canonico         TEXT NOT NULL UNIQUE        -- Nombre normalizado
nif_cif                 TEXT UNIQUE                 -- NIF/CIF único
nombres_alternativos    JSONB DEFAULT '[]'          -- Variaciones del nombre
total_facturas          INTEGER DEFAULT 0           -- Contador
total_importe           DECIMAL(18,2) DEFAULT 0.00  -- Suma total
categoria               TEXT                         -- Categoría asignada
activo                  BOOLEAN DEFAULT TRUE
fecha_creacion          TIMESTAMP DEFAULT now()
fecha_actualizacion     TIMESTAMP DEFAULT now()

-- Relación
facturas                relationship("Factura", foreign_keys="Factura.proveedor_maestro_id")
```

**Índices:**
- `idx_proveedores_maestros_nif` (nif_cif) - Parcial WHERE nif_cif IS NOT NULL
- `idx_proveedores_maestros_nombre` (nombre_canonico)

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **NO existe campo `sucursal_id`**
- **Los proveedores son compartidos entre sucursales actualmente**
- **Necesitará decisión: ¿proveedores compartidos o separados por sucursal?**

---

#### 4. `categorias`

**Propósito:** Categorías para proveedores y otros usos

```sql
id              SERIAL PRIMARY KEY
nombre          TEXT NOT NULL UNIQUE
descripcion     TEXT
color           TEXT DEFAULT '#3b82f6'        -- Color hexadecimal
activo          BOOLEAN DEFAULT TRUE
creado_en       TIMESTAMP DEFAULT now()
actualizado_en  TIMESTAMP DEFAULT now()
```

**Índices:**
- `idx_categorias_nombre` (nombre)
- `idx_categorias_activo` (activo) - Parcial WHERE activo = TRUE

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **Las categorías son compartidas actualmente**
- **Decisión necesaria: ¿categorías globales o por sucursal?**

---

#### 5. `ingest_events` (Auditoría)

**Propósito:** Log de eventos de procesamiento

```sql
id              BIGSERIAL PRIMARY KEY
drive_file_id   TEXT NOT NULL                 -- ID del archivo procesado
etapa           TEXT NOT NULL                 -- 'ingest_start', 'download', 'extract', 'validation', 'ingest_complete', 'ingest_error'
nivel           TEXT NOT NULL                 -- 'INFO', 'WARNING', 'ERROR'
detalle         TEXT                          -- Mensaje detallado
hash_contenido  TEXT                          -- Hash de la factura
decision        TEXT                          -- 'INSERT', 'DUPLICATE', 'REVIEW', etc.
ts              TIMESTAMP DEFAULT now()
```

**⚠️ IMPORTANTE:**
- **NO tiene índice por sucursal**
- **Útil para debugging y auditoría**

---

#### 6. `sync_state` (Sincronización)

**Propósito:** Estado de sincronización incremental con Drive

```sql
key         TEXT PRIMARY KEY                  -- Ej: 'drive_last_sync_time'
value       TEXT NOT NULL                     -- Valor serializado
updated_at  TIMESTAMP DEFAULT now()
```

**Uso actual:**
- `drive_last_sync_time`: Timestamp de última sincronización
- Permite sincronización incremental (solo archivos modificados)

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **Actualmente hay un solo estado global**
- **Necesitará estado por sucursal: `drive_last_sync_time_sucursal_1`, etc.**

---

#### 7. `ingresos_mensuales` (Rentabilidad)

**Propósito:** Ingresos mensuales para análisis de rentabilidad

```sql
id              SERIAL PRIMARY KEY
mes             INTEGER NOT NULL              -- 1-12
año             INTEGER NOT NULL              -- 2000-2100
monto_ingresos  DECIMAL(18,2) NOT NULL DEFAULT 5000.00
creado_en       TIMESTAMP DEFAULT now()
actualizado_en  TIMESTAMP DEFAULT now()

-- Constraint único
UNIQUE(mes, año)
```

**Índices:**
- `idx_ingresos_mensuales_año` (año)
- `idx_ingresos_mensuales_mes_año` (mes, año)

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **NO tiene campo sucursal**
- **Los ingresos son globales actualmente**
- **Necesitará ingresos por sucursal**

---

#### 8. `costos_personal` (Costos de Personal)

**Propósito:** Costos de personal mensuales para análisis de rentabilidad

```sql
id              SERIAL PRIMARY KEY
mes             INTEGER NOT NULL              -- 1-12
año             INTEGER NOT NULL              -- 2000-2100
sueldos_netos   DECIMAL(18,2) NOT NULL DEFAULT 0.00
coste_empresa   DECIMAL(18,2) NOT NULL DEFAULT 0.00  -- Seguros sociales, etc.
total_personal  DECIMAL(18,2) GENERATED ALWAYS AS (sueldos_netos + coste_empresa) STORED
notas           TEXT
creado_en       TIMESTAMP DEFAULT now()
actualizado_en  TIMESTAMP DEFAULT now()

-- Constraint único
UNIQUE(mes, año)
```

**Índices:**
- `idx_costos_personal_año` (año)
- `idx_costos_personal_mes_año` (mes, año)

**Constraints:**
- `check_costo_personal_mes_range`: mes >= 1 AND mes <= 12
- `check_costo_personal_año_range`: año >= 2000 AND año <= 2100
- `uq_costos_personal_mes_año`: UNIQUE(mes, año)

**Campo calculado:**
- `total_personal`: Suma automática de `sueldos_netos` + `coste_empresa` (STORED)

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **NO tiene campo sucursal**
- **Los costos de personal son globales actualmente**
- **Necesitará costos de personal por sucursal**

**⚠️ INTEGRACIÓN:**
- Se integra con el endpoint `/api/ingresos/rentabilidad/{year}` para cálculo de gastos totales
- Los costos de personal se suman a los gastos de facturas para obtener rentabilidad neta

---

### Relaciones Entre Tablas

```
facturas
  ├── proveedor_id → proveedores.id (legacy, opcional)
  ├── proveedor_maestro_id → proveedores_maestros.id (principal, opcional)
  └── (sin relación directa con categorias)

proveedores
  └── (sin relación con categorias, solo texto en campo categoria)

proveedores_maestros
  └── categoria (TEXT) → categorias.nombre (relación implícita, no FK)

categorias
  └── (independiente, referenciada por texto en proveedores)
```

**⚠️ OBSERVACIÓN:**
- La relación entre `proveedores_maestros` y `categorias` es **implícita por texto**, no hay Foreign Key
- Esto permite flexibilidad pero puede causar inconsistencias

---

## 🔌 APIs y Endpoints

### Base URL
```
Producción: https://alexforge.online/invoice-api/api
Desarrollo: http://localhost:8002/api
```

### Estructura de Rutas

#### 1. `/api/facturas/*` (FacturasRouter)

**Endpoints principales:**

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| GET | `/facturas/summary` | Resumen de facturas del mes | `month`, `year` |
| GET | `/facturas/by_day` | Facturas agrupadas por día | `month`, `year` |
| GET | `/facturas/recent` | Facturas recientes | `month`, `year`, `limit` |
| GET | `/facturas/list` | Lista completa de facturas | `month`, `year`, `page`, `per_page` |
| GET | `/facturas/{id}` | Detalle de una factura | `id` |
| GET | `/facturas/failed` | Facturas con errores | `month`, `year` |
| GET | `/facturas/categories` | Desglose por categorías | `month`, `year` |
| POST | `/facturas/manual` | Crear factura manualmente | Body: `ManualFacturaCreate` |
| GET | `/facturas/export/excel` | Exportar a Excel | `month`, `year` |

**⚠️ IMPORTANTE:**
- **Todos los endpoints filtran por `month` y `year`**
- **NO hay filtro por sucursal actualmente**
- **Todos retornan datos de TODAS las sucursales mezcladas**

---

#### 2. `/api/proveedores/*` (ProveedoresRouter)

**Endpoints principales:**

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| GET | `/proveedores` | Lista de proveedores | `letra`, `search`, `categoria`, `skip`, `limit` |
| GET | `/proveedores/{id}` | Detalle de proveedor | `id` |
| PUT | `/proveedores/{id}` | Actualizar proveedor | `id`, Body: `ProveedorUpdate` |
| GET | `/proveedores/stats/categorias` | Estadísticas por categoría | - |

**⚠️ IMPORTANTE:**
- **Filtra por letra inicial, búsqueda y categoría**
- **NO filtra por sucursal**
- **Retorna TODOS los proveedores de todas las sucursales**

---

#### 3. `/api/system/*` (SystemRouter)

**Endpoints principales:**

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| GET | `/system/sync-status` | Estado de sincronización con Drive | - |
| GET | `/system/data-load-stats` | Estadísticas de carga de datos | - |

**⚠️ IMPORTANTE:**
- **Estadísticas globales, no por sucursal**
- **Sync status es global**

---

#### 4. `/api/categorias/*` (CategoriasRouter)

**Endpoints principales:**

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| GET | `/categorias` | Lista de categorías | - |
| GET | `/categorias/{id}` | Detalle de categoría | `id` |
| POST | `/categorias` | Crear categoría | Body: `CategoriaCreate` |
| PUT | `/categorias/{id}` | Actualizar categoría | `id`, Body: `CategoriaUpdate` |
| DELETE | `/categorias/{id}` | Eliminar categoría | `id` |

**⚠️ IMPORTANTE:**
- **Categorías globales, compartidas**

---

#### 5. `/api/ingresos/*` (IngresosRouter)

**Endpoints principales:**

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| GET | `/ingresos/mensuales` | Ingresos mensuales | `year` |
| GET | `/ingresos/mensuales/{id}` | Detalle de ingreso mensual | `id` |
| POST | `/ingresos/mensuales` | Crear ingreso mensual | Body: `IngresoMensualCreate` |
| PUT | `/ingresos/mensuales/{id}` | Actualizar ingreso mensual | `id`, Body: `IngresoMensualUpdate` |
| GET | `/ingresos/rentabilidad/{year}` | Análisis de rentabilidad anual | `year` |

**Endpoint de Rentabilidad:**
- Calcula rentabilidad mensual: `Ingresos - Gastos (facturas) - Costos de Personal`
- Integra datos de:
  - `ingresos_mensuales` (ingresos por mes)
  - `facturas` (gastos por mes, sumando `importe_total`)
  - `costos_personal` (costos de personal por mes)
- Retorna array de 12 meses con: ingresos, gastos, costos_personal, beneficio neto, margen (%)

**⚠️ IMPORTANTE:**
- **Ingresos globales, no por sucursal**
- **Análisis de rentabilidad incluye costos de personal desde Enero 2026**

---

#### 6. `/api/costos-personal/*` (CostosPersonalRouter)

**Endpoints principales:**

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| GET | `/costos-personal/{year}` | Costos de personal por año | `year` (path param) |
| POST | `/costos-personal` | Crear/actualizar costo mensual | Body: `CostoPersonalCreate` |
| PUT | `/costos-personal/{costo_id}` | Actualizar costo existente | `costo_id`, Body: `CostoPersonalUpdate` |
| DELETE | `/costos-personal/{costo_id}` | Eliminar costo de personal | `costo_id` |

**Schemas Pydantic:**

```python
class CostoPersonalBase(BaseModel):
    mes: int
    año: int
    sueldos_netos: float
    coste_empresa: float
    notas: Optional[str] = None

class CostoPersonalCreate(CostoPersonalBase):
    pass

class CostoPersonalUpdate(BaseModel):
    sueldos_netos: Optional[float] = None
    coste_empresa: Optional[float] = None
    notas: Optional[str] = None

class CostoPersonalResponse(CostoPersonalBase):
    id: int
    total_personal: float
    creado_en: datetime
    actualizado_en: datetime
```

**Repository:**
- `CostoPersonalRepository` en `src/db/repositories.py`
- Métodos: `get_by_year()`, `get_by_month_year()`, `upsert()`, `delete()`
- UPSERT con `ON CONFLICT DO UPDATE` para idempotencia (evita duplicados por mes/año)

**⚠️ IMPORTANTE:**
- **Costos globales, no por sucursal**
- **El endpoint POST usa UPSERT: si ya existe el registro para el mes/año, lo actualiza**
- **Integración con `/api/ingresos/rentabilidad/{year}` para análisis de rentabilidad**

---

#### 7. `/api/auth/*` (AuthRouter)

**Endpoints principales:**

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| GET | `/auth/check` | Verificar autenticación | - |
| GET | `/auth/me` | Obtener usuario actual | - |
| POST | `/auth/google` | Login con Google OAuth | Body: `GoogleAuthRequest` |
| POST | `/auth/logout` | Cerrar sesión | - |

**⚠️ IMPORTANTE:**
- **Autenticación actual no incluye información de sucursal**
- **Sesión almacena solo `user` (email, nombre)**

---

### Formato de Respuestas

**Ejemplo: GET /api/facturas/summary**
```json
{
  "total_facturas": 150,
  "total_importe": 45000.50,
  "base_imponible": 37190.08,
  "impuestos_total": 7810.42,
  "promedio_importe": 300.00
}
```

**Ejemplo: GET /api/facturas/list**
```json
{
  "data": [
    {
      "id": 1,
      "numero_factura": "FAC-2025-001",
      "proveedor_nombre": "SUPERMERCADOS MAS",
      "fecha_emision": "2025-08-15",
      "importe_total": 1250.50,
      "estado": "procesado",
      "confianza": "alta"
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 25
}
```

---

## 🔄 Flujo de Procesamiento de Facturas

### Pipeline Completo

```
1. INICIO (src/main.py)
   ↓
2. Inicializar componentes:
   - Database (PostgreSQL pool)
   - DriveClient (Service Account OAuth2)
   - InvoiceExtractor (OpenAI + Tesseract)
   ↓
3. Obtener meses a procesar (CLI: --months o .env: MONTHS_TO_SCAN)
   ↓
4. Para cada mes:
   a. Buscar carpeta en Drive (ej: "agosto")
      - Usa GOOGLE_DRIVE_FOLDER_ID como carpeta base
      - Busca subcarpeta por nombre del mes
   b. Listar PDFs en la carpeta (recursivo)
      - Query: mimeType='application/pdf' AND trashed=false
      - Obtiene: id, name, modifiedTime, size, parents
   c. Agregar metadata (folder_name, modifiedTime)
   ↓
5. Filtrar duplicados (si no --force):
   - Consultar drive_file_ids en BD
   - Eliminar ya procesados de la lista
   ↓
6. Para cada archivo nuevo:
   a. Descargar a temp/
      - Sanitizar nombre de archivo
      - Validar descarga exitosa
   
   b. Validar integridad
      - Magic bytes %PDF-
      - Tamaño > 0
      - Tamaño coincide (opcional)
   
   c. Log evento: ingest_start
   
   d. Extracción OCR
      i. Convertir PDF → Image → Base64
      ii. Llamar OpenAI API (GPT-4o)
          - Prompt estructurado
          - Format: JSON
          - Timeout: 60s
          - Retries: 3x con backoff
      iii. Si falla o confianza baja:
           - Fallback a Tesseract
           - Regex patterns
           - Merge resultados
   
   e. Normalización
      - Fechas → ISO format (YYYY-MM-DD)
      - Importes → float (detecta formato EUR/USD)
      - Moneda → uppercase 3 chars
   
   f. Detección de duplicados
      - Calcular hash SHA256: proveedor + número + fecha + importe
      - Consultar hash_contenido en BD
      - Decisión: INSERT, DUPLICATE, REVIEW, IGNORE, UPDATE_REVISION
   
   g. Crear DTO
      - Combinar OCR data + Drive metadata
      - Añadir timestamps
      - Determinar extractor usado
   
   h. Validación
      i. Business rules:
         - Campos obligatorios
         - Importe > 0 (o NULL si estado='revisar')
         - Coherencia fiscal
         - Fecha no futura
      ii. Si falla:
          - Marcar estado = 'revisar'
          - Guardar en pending/
   
   i. UPSERT en BD
      - INSERT ON CONFLICT (drive_file_id) DO UPDATE
      - Retornar factura_id
   
   j. Log evento: ingest_complete
      - Incluir elapsed_ms
      - Incluir factura_id
   
   k. Cleanup
      - Eliminar archivo de temp/
   ↓
7. Generar estadísticas
   - Total procesados
   - Exitosos / Fallidos
   - Validación fallida
   - Duración total
   ↓
8. Guardar stats en JSON
   - logs/last_run_stats.json
   ↓
9. Crear backup (si exitosos > 0)
   - pg_dump con timestamp
   ↓
10. FIN
```

### Variables de Entorno Críticas

```env
# Google Drive
GOOGLE_SERVICE_ACCOUNT_FILE=keys/service_account.json
GOOGLE_DRIVE_FOLDER_ID=1e-JVdEzB8FUQns85WH2qkkXE-CDM6NF9  # Carpeta base

# Base de datos
DATABASE_URL=postgresql://extractor_user:Dagoba50dago-@localhost:5432/negocio_db

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Procesamiento
MONTHS_TO_SCAN=agosto,septiembre,octubre
TEMP_PATH=temp
QUARANTINE_PATH=data/quarantine
```

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **`GOOGLE_DRIVE_FOLDER_ID` es único actualmente**
- **Necesitará múltiples folder IDs (uno por sucursal)**
- **O estructura de carpetas: `GOOGLE_DRIVE_FOLDER_ID/sucursal_1/`, `GOOGLE_DRIVE_FOLDER_ID/sucursal_2/`**

---

## 🎨 Frontend - Estructura y Componentes

### Arquitectura Frontend

```
frontend/
├── src/
│   ├── admin/                    # React-admin (framework principal)
│   │   ├── App.jsx               # Configuración principal de React-admin
│   │   ├── Layout.jsx            # Layout personalizado con Sidebar
│   │   ├── dataProvider.js       # Adaptador FastAPI → React-admin
│   │   ├── authProvider.js       # Autenticación
│   │   ├── theme.js              # Tema personalizado
│   │   └── resources/            # Recursos (secciones)
│   │       ├── facturas/         # (Oculto temporalmente)
│   │       ├── proveedores/      # Gestión de proveedores
│   │       ├── reportes/          # Dashboard, Pendientes, Reportes
│   │       ├── carga-datos/      # Estadísticas + Categorías (tabs)
│   │       └── categorias/       # Gestión de categorías
│   ├── components/               # Componentes reutilizables
│   │   ├── Dashboard.jsx         # Dashboard principal
│   │   ├── FacturasTable.jsx    # Tabla de facturas
│   │   ├── KPIGrid.jsx           # Grid de KPIs
│   │   ├── Header.jsx            # Header con selector mes/año
│   │   └── Sidebar.jsx           # Sidebar de navegación
│   ├── hooks/
│   │   └── useInvoiceData.js     # Hook para datos de facturas
│   └── utils/
│       ├── api.js                # Funciones de API
│       └── constants.js          # Constantes
└── vite.config.js                # Config: base: '/invoice-dashboard/'
```

### DataProvider (Adaptador API)

**Archivo:** `frontend/src/admin/dataProvider.js`

**Funcionalidad:**
- Convierte requests de React-admin a llamadas FastAPI
- Adapta respuestas FastAPI al formato esperado por React-admin
- Maneja paginación, filtros, sorting

**Recursos actuales:**
- `proveedores` → `/api/proveedores`
- `facturas` → `/api/facturas/list` (con month/year)
- `pendientes` → `/api/facturas/failed`
- `reportes` → `/api/facturas/*` (múltiples endpoints)
- `categorias` → `/api/categorias`
- `datos` → `/api/system/data-load-stats`

**⚠️ IMPORTANTE:**
- **NO hay contexto de sucursal en el dataProvider**
- **Todas las requests son globales**

---

### Secciones del Frontend

#### 1. Dashboard (`ReporteDashboard`)
- **Componente:** `frontend/src/admin/resources/reportes/ReporteDashboard.jsx`
- **Datos:** Hook `useInvoiceData(month, year)`
- **Muestra:**
  - KPIs (total facturas, importe total, base imponible, impuestos)
  - Gráfico por categorías
  - Tabla de facturas recientes
- **Filtros:** Mes y año (selector en Header)

#### 2. Pendientes (`ReportePendientes`)
- **Componente:** `frontend/src/admin/resources/reportes/ReportePendientes.jsx`
- **Datos:** `/api/facturas/failed?month=X&year=Y`
- **Muestra:** Facturas con estado 'error', 'revisar', 'pendiente'

#### 3. Reportes (`Reportes`)
- **Componente:** `frontend/src/admin/resources/reportes/Reportes.jsx`
- **Incluye:** Análisis de rentabilidad (`AnalisisRentabilidad.jsx`)
- **Datos:** Múltiples endpoints de `/api/facturas/*` y `/api/ingresos/*`

#### 4. Proveedores (`ProveedorList`)
- **Componente:** `frontend/src/admin/resources/proveedores/ProveedorList.jsx`
- **Datos:** `/api/proveedores?letra=X&categoria=Y&search=Z`
- **Funcionalidades:**
  - Filtro alfabético A-Z
  - Filtro por categoría
  - Búsqueda por nombre
  - Edición de proveedor (categoría, NIF, email)

#### 5. Datos (`CargaDatosPanel`)
- **Componente:** `frontend/src/admin/resources/carga-datos/CargaDatosPanel.jsx`
- **Tabs:**
  - **Estadísticas:** `/api/system/data-load-stats`
  - **Categorías:** Lista embebida de `CategoriasList`

#### 6. Categorías (`CategoriasList`)
- **Componente:** `frontend/src/admin/resources/categorias/CategoriasList.jsx`
- **Datos:** `/api/categorias`
- **Funcionalidades:** CRUD completo (crear, editar, eliminar)

---

## 🔐 Autenticación y Sesiones

### Sistema Actual

**Middleware:** `AuthMiddleware` en `src/api/main.py`

**Rutas públicas:**
- `/`
- `/healthz`
- `/docs`
- `/redoc`
- `/openapi.json`
- `/api/auth/*`

**Rutas protegidas:**
- Todas las demás rutas `/api/*` requieren sesión activa

**Sesiones:**
- `SessionMiddleware` con cookies
- Clave secreta: `SESSION_SECRET_KEY` (variable de entorno)
- Duración: 24 horas
- Almacenamiento: `request.session['user']`

**Estructura de usuario en sesión:**
```python
{
    'email': 'usuario@example.com',
    'name': 'Nombre Usuario',
    'picture': 'https://...'  # Opcional, si viene de Google OAuth
}
```

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **NO hay información de sucursal en la sesión**
- **NO hay permisos por sucursal**
- **Cualquier usuario autenticado ve TODAS las facturas**

---

## 📁 Integración con Google Drive

### Estructura Actual

**Carpeta Base:** Configurada en `GOOGLE_DRIVE_FOLDER_ID`

**Estructura de carpetas:**
```
GOOGLE_DRIVE_FOLDER_ID/
├── agosto/
│   ├── factura_001.pdf
│   ├── factura_002.pdf
│   └── ...
├── septiembre/
│   ├── factura_001.pdf
│   └── ...
└── octubre/
    └── ...
```

**Proceso de búsqueda:**
1. `DriveClient.get_folder_id_by_name('agosto', parent_id=GOOGLE_DRIVE_FOLDER_ID)`
2. `DriveClient.list_pdf_files(folder_id)` - Lista recursivamente todos los PDFs
3. Para cada PDF: descarga y procesa

**Campos almacenados:**
- `drive_file_id`: ID único del archivo en Drive
- `drive_file_name`: Nombre del archivo
- `drive_folder_name`: Nombre de la carpeta (mes)
- `drive_modified_time`: Timestamp de última modificación

**⚠️ IMPORTANTE PARA MULTI-SUCURSAL:**
- **Actualmente hay una sola carpeta base**
- **Opciones de diseño:**
  1. **Opción A:** Múltiples carpetas base (una por sucursal)
     ```
     GOOGLE_DRIVE_FOLDER_ID_SUCURSAL_1/
     GOOGLE_DRIVE_FOLDER_ID_SUCURSAL_2/
     ```
  2. **Opción B:** Subcarpetas por sucursal
     ```
     GOOGLE_DRIVE_FOLDER_ID/
     ├── sucursal_1/
     │   ├── agosto/
     │   └── septiembre/
     └── sucursal_2/
         ├── agosto/
         └── septiembre/
     ```
  3. **Opción C:** Prefijo en nombre de carpeta
     ```
     GOOGLE_DRIVE_FOLDER_ID/
     ├── sucursal_1_agosto/
     ├── sucursal_1_septiembre/
     ├── sucursal_2_agosto/
     └── sucursal_2_septiembre/
     ```

---

## 🔍 Análisis de Impacto para Multi-Sucursal

### Cambios Necesarios Identificados

#### 1. Base de Datos

**Tablas que necesitan `sucursal_id`:**
- ✅ `facturas` - **CRÍTICO** (todas las queries filtran por facturas)
- ✅ `proveedores` - **IMPORTANTE** (pueden ser compartidos o separados)
- ✅ `proveedores_maestros` - **IMPORTANTE** (misma decisión que proveedores)
- ✅ `ingest_events` - **ÚTIL** (auditoría por sucursal)
- ✅ `sync_state` - **CRÍTICO** (estado de sync por sucursal)
- ✅ `ingresos_mensuales` - **IMPORTANTE** (ingresos por sucursal)
- ✅ `costos_personal` - **IMPORTANTE** (costos de personal por sucursal)

**Tablas que pueden ser compartidas:**
- `categorias` - **DECISIÓN:** ¿Categorías globales o por sucursal?

**Índices nuevos necesarios:**
- `idx_facturas_sucursal` (sucursal_id)
- `idx_facturas_sucursal_estado` (sucursal_id, estado)
- `idx_facturas_sucursal_fecha` (sucursal_id, fecha_emision)
- `idx_proveedores_sucursal` (si se separan por sucursal)

---

#### 2. Backend (FastAPI)

**Cambios en Repositories:**
- `FacturaRepository`: Agregar filtro `sucursal_id` en TODAS las queries
- `ProveedorRepository`: Decidir si filtra por sucursal o es compartido
- `SyncStateRepository`: Keys por sucursal (`drive_last_sync_time_sucursal_1`)

**Cambios en Endpoints:**
- Todos los endpoints de `/api/facturas/*` necesitan `sucursal_id` (query param o header)
- Endpoints de `/api/proveedores/*` necesitan decidir si filtran por sucursal
- Endpoints de `/api/system/*` necesitan `sucursal_id` para estadísticas
- Endpoints de `/api/ingresos/*` necesitan `sucursal_id`
- Endpoints de `/api/costos-personal/*` necesitan `sucursal_id`

**Middleware nuevo:**
- `SucursalMiddleware`: Extraer `sucursal_id` de sesión o header
- Validar que el usuario tenga acceso a la sucursal

**Dependencias nuevas:**
- `get_sucursal_id()`: Dependency que retorna sucursal_id del request
- `validate_sucursal_access()`: Validar permisos

---

#### 3. Frontend (React)

**Cambios en DataProvider:**
- Agregar `sucursal_id` a todas las requests
- Context de React para almacenar sucursal seleccionada
- Persistir selección en localStorage o sesión

**Componentes nuevos:**
- `SucursalSelector`: Dropdown/selector de sucursal
- Ubicación: Header o Sidebar (visible en todas las páginas)

**Cambios en componentes existentes:**
- Todos los hooks (`useInvoiceData`) necesitan pasar `sucursal_id`
- Todos los dataProviders necesitan incluir `sucursal_id` en queries

**Context/State Management:**
- Crear `SucursalContext` para compartir sucursal seleccionada
- O usar React-admin `useStore` para persistir

---

#### 4. Procesamiento (Pipeline)

**Cambios en `src/main.py`:**
- Agregar parámetro `--sucursal` o `--sucursal-id`
- O detectar automáticamente desde carpeta de Drive

**Cambios en `DriveClient`:**
- Soporte para múltiples `GOOGLE_DRIVE_FOLDER_ID` (uno por sucursal)
- O búsqueda en subcarpetas por sucursal

**Cambios en `FacturaRepository.upsert_factura()`:**
- Incluir `sucursal_id` en el DTO
- Validar que no haya duplicados entre sucursales (o permitirlos)

---

#### 5. Autenticación

**Cambios en sesión:**
- Agregar `sucursal_id` a `request.session['user']`
- O almacenar `sucursal_id` por separado en sesión

**Permisos (futuro):**
- Tabla `usuarios_sucursales` para control de acceso
- Middleware que valida acceso a sucursal

---

## 🎯 Decisiones de Diseño Necesarias

### 1. Modelo de Datos

**Pregunta 1: ¿Proveedores compartidos o separados?**
- **Opción A:** Proveedores compartidos (mismo proveedor para ambas sucursales)
  - Pros: Normalización, menos duplicados
  - Contras: Estadísticas mezcladas
- **Opción B:** Proveedores separados por sucursal
  - Pros: Datos completamente independientes
  - Contras: Duplicación de datos, más complejidad

**Recomendación:** **Opción A** (compartidos) con estadísticas filtradas por sucursal

---

**Pregunta 2: ¿Categorías compartidas o separadas?**
- **Opción A:** Categorías globales (compartidas)
  - Pros: Consistencia, menos mantenimiento
- **Opción B:** Categorías por sucursal
  - Pros: Flexibilidad por sucursal
  - Contras: Más complejidad

**Recomendación:** **Opción A** (compartidas) inicialmente, permitir extensión futura

---

**Pregunta 3: ¿Detección de duplicados entre sucursales?**
- **Opción A:** Duplicados globales (mismo hash = duplicado en cualquier sucursal)
- **Opción B:** Duplicados solo dentro de sucursal (mismo hash en misma sucursal)

**Recomendación:** **Opción B** (por sucursal) - facturas pueden ser iguales en diferentes sucursales

---

### 2. Estructura de Google Drive

**Pregunta: ¿Cómo organizar carpetas por sucursal?**

**Opción A: Múltiples carpetas base**
```
GOOGLE_DRIVE_FOLDER_ID_SUCURSAL_1=xxx
GOOGLE_DRIVE_FOLDER_ID_SUCURSAL_2=yyy
```
- Pros: Separación clara, fácil de entender
- Contras: Múltiples variables de entorno

**Opción B: Subcarpetas por sucursal**
```
GOOGLE_DRIVE_FOLDER_ID/
├── sucursal_1/
│   ├── agosto/
│   └── septiembre/
└── sucursal_2/
    ├── agosto/
    └── septiembre/
```
- Pros: Una sola variable de entorno, estructura clara
- Contras: Cambio en lógica de búsqueda

**Opción C: Prefijo en nombre de carpeta**
```
GOOGLE_DRIVE_FOLDER_ID/
├── sucursal_1_agosto/
├── sucursal_1_septiembre/
├── sucursal_2_agosto/
└── sucursal_2_septiembre/
```
- Pros: Flexible, fácil de migrar
- Contras: Parsing de nombres, menos intuitivo

**Recomendación:** **Opción B** (subcarpetas) - más limpio y escalable

---

### 3. Identificación de Sucursal

**Pregunta: ¿Cómo identificar la sucursal de una factura?**

**Opción A: Campo `sucursal_id` en tabla `facturas`**
- Pros: Simple, directo, fácil de filtrar
- Contras: Requiere migración de datos existentes

**Opción B: Inferir desde `drive_folder_name`**
- Ejemplo: `drive_folder_name = "sucursal_1/agosto"` → parsear sucursal
- Pros: No requiere migración
- Contras: Lógica frágil, depende de estructura de carpetas

**Recomendación:** **Opción A** (campo explícito) - más robusto y mantenible

---

### 4. Selector de Sucursal en Frontend

**Pregunta: ¿Dónde y cómo mostrar el selector?**

**Opción A: Header (siempre visible)**
- Pros: Accesible en todas las páginas
- Contras: Ocupa espacio

**Opción B: Sidebar (menú lateral)**
- Pros: Integrado con navegación
- Contras: Puede estar colapsado

**Opción C: Modal al iniciar sesión**
- Pros: Forzar selección explícita
- Contras: Interrumpe flujo

**Recomendación:** **Opción A** (Header) - más visible y accesible

---

## 📊 Consideraciones de Migración

### Datos Existentes

**Problema:** Actualmente hay facturas en la BD sin `sucursal_id`

**Opciones de migración:**

1. **Asignar todas las facturas existentes a "Sucursal 1" (default)**
   ```sql
   ALTER TABLE facturas ADD COLUMN sucursal_id INTEGER DEFAULT 1;
   ```

2. **Crear tabla de sucursales primero**
   ```sql
   CREATE TABLE sucursales (
     id SERIAL PRIMARY KEY,
     nombre TEXT NOT NULL UNIQUE,
     codigo TEXT NOT NULL UNIQUE,
     activa BOOLEAN DEFAULT TRUE,
     creado_en TIMESTAMP DEFAULT now()
   );
   
   INSERT INTO sucursales (nombre, codigo) VALUES 
     ('Sucursal Principal', 'SUCURSAL_1'),
     ('Sucursal Nueva', 'SUCURSAL_2');
   ```

3. **Migrar datos existentes**
   ```sql
   UPDATE facturas SET sucursal_id = 1 WHERE sucursal_id IS NULL;
   ```

---

### Compatibilidad Hacia Atrás

**Estrategia:**
- Mantener endpoints sin `sucursal_id` como "legacy" (retornan datos de sucursal por defecto)
- Agregar endpoints nuevos con `sucursal_id` explícito
- Deprecar endpoints legacy después de migración completa

---

## 🔒 Seguridad y Permisos

### Consideraciones Actuales

**Estado actual:**
- Autenticación básica (sí/no)
- Sin control de acceso por sucursal
- Cualquier usuario autenticado ve todo

### Necesidades Futuras

**Tabla sugerida: `usuarios_sucursales`**
```sql
CREATE TABLE usuarios_sucursales (
  id SERIAL PRIMARY KEY,
  usuario_email TEXT NOT NULL,
  sucursal_id INTEGER NOT NULL REFERENCES sucursales(id),
  rol TEXT DEFAULT 'viewer',  -- 'viewer', 'editor', 'admin'
  creado_en TIMESTAMP DEFAULT now(),
  UNIQUE(usuario_email, sucursal_id)
);
```

**Middleware sugerido:**
- Validar que `request.session['user']['email']` tenga acceso a `sucursal_id` solicitado
- Retornar 403 si no tiene acceso

---

## 📝 Checklist de Implementación Sugerido

### Fase 1: Base de Datos
- [ ] Crear tabla `sucursales`
- [ ] Agregar columna `sucursal_id` a `facturas`
- [ ] Agregar columna `sucursal_id` a `proveedores` (si se separan)
- [ ] Agregar columna `sucursal_id` a `ingest_events`
- [ ] Agregar columna `sucursal_id` a `ingresos_mensuales`
- [ ] Agregar columna `sucursal_id` a `costos_personal`
- [ ] Modificar `sync_state` para keys por sucursal
- [ ] Crear índices necesarios
- [ ] Migrar datos existentes (asignar a Sucursal 1)

### Fase 2: Backend
- [ ] Crear modelo `Sucursal` en SQLAlchemy
- [ ] Agregar `sucursal_id` a modelos existentes
- [ ] Modificar `FacturaRepository` para filtrar por `sucursal_id`
- [ ] Modificar `ProveedorRepository` (decidir si filtra o no)
- [ ] Modificar `SyncStateRepository` para keys por sucursal
- [ ] Agregar `sucursal_id` a todos los endpoints de `/api/facturas/*`
- [ ] Agregar `sucursal_id` a endpoints de `/api/system/*`
- [ ] Agregar `sucursal_id` a endpoints de `/api/ingresos/*`
- [ ] Agregar `sucursal_id` a endpoints de `/api/costos-personal/*`
- [ ] Modificar `CostoPersonalRepository` para filtrar por `sucursal_id`
- [ ] Crear dependency `get_sucursal_id()`
- [ ] Crear middleware `SucursalMiddleware` (opcional)
- [ ] Actualizar schemas Pydantic

### Fase 3: Procesamiento
- [ ] Modificar `src/main.py` para aceptar `--sucursal-id`
- [ ] Modificar `DriveClient` para buscar en subcarpetas por sucursal
- [ ] Modificar pipeline para incluir `sucursal_id` en DTO
- [ ] Actualizar detección de duplicados (por sucursal)

### Fase 4: Frontend
- [ ] Crear componente `SucursalSelector`
- [ ] Crear `SucursalContext` o usar `useStore`
- [ ] Agregar selector al Header
- [ ] Modificar `dataProvider` para incluir `sucursal_id` en requests
- [ ] Modificar `useInvoiceData` hook para incluir `sucursal_id`
- [ ] Actualizar todos los componentes que usan datos
- [ ] Persistir selección en localStorage

### Fase 5: Testing y Validación
- [ ] Probar procesamiento de facturas por sucursal
- [ ] Validar que datos se filtran correctamente
- [ ] Verificar que no hay "filtrado" entre sucursales
- [ ] Probar migración de datos existentes
- [ ] Validar performance con índices nuevos

---

## 🚀 Consideraciones de Performance

### Índices Críticos

**Para queries por sucursal:**
```sql
-- Facturas por sucursal y fecha
CREATE INDEX idx_facturas_sucursal_fecha 
ON facturas(sucursal_id, fecha_emision);

-- Facturas por sucursal y estado
CREATE INDEX idx_facturas_sucursal_estado 
ON facturas(sucursal_id, estado);

-- Proveedores por sucursal (si se separan)
CREATE INDEX idx_proveedores_sucursal 
ON proveedores(sucursal_id);
```

### Queries Optimizadas

**Ejemplo de query optimizada:**
```sql
-- Antes (sin sucursal)
SELECT * FROM facturas 
WHERE fecha_emision >= '2025-08-01' 
  AND fecha_emision <= '2025-08-31';

-- Después (con sucursal)
SELECT * FROM facturas 
WHERE sucursal_id = 1
  AND fecha_emision >= '2025-08-01' 
  AND fecha_emision <= '2025-08-31';
-- Usa índice: idx_facturas_sucursal_fecha
```

---

## 📚 Referencias y Archivos Clave

### Archivos de Código Importantes

**Backend:**
- `src/api/main.py` - Aplicación FastAPI principal
- `src/api/routes/facturas.py` - Endpoints de facturas
- `src/api/routes/proveedores.py` - Endpoints de proveedores
- `src/api/routes/system.py` - Endpoints de sistema
- `src/api/routes/ingresos.py` - Endpoints de ingresos y rentabilidad
- `src/api/routes/costos_personal.py` - Endpoints de costos de personal
- `src/db/models.py` - Modelos SQLAlchemy
- `src/db/repositories.py` - Repositorios de datos (incluye CostoPersonalRepository)
- `src/db/database.py` - Configuración de conexión
- `src/drive_client.py` - Cliente de Google Drive
- `src/main.py` - Script de procesamiento

**Frontend:**
- `frontend/src/admin/App.jsx` - Configuración React-admin
- `frontend/src/admin/dataProvider.js` - Adaptador API
- `frontend/src/admin/resources/*/` - Componentes de secciones
- `frontend/src/components/` - Componentes reutilizables
- `frontend/vite.config.js` - Configuración Vite

**Configuración:**
- `.env` - Variables de entorno
- `docker-compose.frontend.yml` - Orquestación Docker
- `Dockerfile.backend` - Build del backend

**Migraciones:**
- `migrations/20260119_add_costos_personal.sql` - Creación tabla costos_personal

---

## 📊 Cambios Recientes Implementados (Enero 2026)

### Nueva Funcionalidad: Costos de Personal

**Fecha de implementación:** Enero 19, 2026

**Descripción:**
Se implementó un sistema completo para registrar y gestionar los costos de personal mensuales, que incluye:
- Sueldos netos del personal
- Costes de empresa (seguros sociales, etc.)
- Cálculo automático del total de personal
- Integración con análisis de rentabilidad

**Componentes implementados:**

1. **Base de Datos:**
   - Nueva tabla `costos_personal` con campos:
     - `mes`, `año` (clave compuesta única)
     - `sueldos_netos` (DECIMAL 18,2)
     - `coste_empresa` (DECIMAL 18,2)
     - `total_personal` (campo calculado STORED)
     - `notas` (opcional)
   - Migración: `migrations/20260119_add_costos_personal.sql`
   - Constraints: validación rango mes (1-12), año (2000-2100)
   - Índices: `idx_costos_personal_año`, `idx_costos_personal_mes_año`

2. **Backend (FastAPI):**
   - Modelo SQLAlchemy: `CostoPersonal` en `src/db/models.py`
   - Repositorio: `CostoPersonalRepository` en `src/db/repositories.py`
     - Métodos: `get_by_year()`, `get_by_month_year()`, `upsert()`, `delete()`
     - UPSERT con idempotencia (ON CONFLICT DO UPDATE)
   - Router: `src/api/routes/costos_personal.py`
     - GET `/{year}` - Obtener costos del año
     - POST `/` - Crear/actualizar (UPSERT)
     - PUT `/{costo_id}` - Actualizar existente
     - DELETE `/{costo_id}` - Eliminar registro
   - Schemas Pydantic: `CostoPersonalCreate`, `CostoPersonalUpdate`, `CostoPersonalResponse`

3. **Integración con Rentabilidad:**
   - Modificado endpoint `/api/ingresos/rentabilidad/{year}`
   - Ahora incluye costos de personal en el cálculo de gastos totales
   - Fórmula: `Beneficio Neto = Ingresos - Gastos (facturas) - Costos Personal`
   - Retorna array mensual con breakdown completo

4. **Documentación:**
   - `REPORTE_IMPLEMENTACION_COSTOS_PERSONAL.md` - Reporte técnico completo
   - `API_COSTOS_PERSONAL_FRONTEND.md` - Guía para desarrollo frontend

**Estado actual:**
- ✅ Backend completamente funcional y testeado
- ✅ Migración de base de datos aplicada
- ✅ APIs documentadas con OpenAPI
- ✅ Integración con análisis de rentabilidad
- ⏳ Frontend pendiente de desarrollo

**Consideraciones para Multi-Sucursal:**
- La tabla `costos_personal` **NO tiene campo `sucursal_id` actualmente**
- Los costos de personal son **globales**
- En implementación multi-sucursal se deberá:
  - Agregar columna `sucursal_id` a la tabla
  - Modificar constraint único a `(mes, año, sucursal_id)`
  - Filtrar por sucursal en todos los endpoints
  - Actualizar análisis de rentabilidad para filtrar por sucursal

---

## 🎯 Resumen para Plan de Implementación

### Información Crítica

1. **Base de datos actual:** PostgreSQL `negocio_db`, sin soporte multi-sucursal
2. **Tabla principal:** `facturas` - necesita `sucursal_id`
3. **Tablas de análisis:** `ingresos_mensuales`, `costos_personal` - necesitan `sucursal_id`
4. **APIs actuales:** Filtran por `month` y `year`, NO por sucursal
5. **Frontend:** React-admin, sin selector de sucursal
6. **Google Drive:** Una carpeta base, necesita estructura por sucursal
7. **Procesamiento:** Script `src/main.py` procesa todas las facturas sin distinción
8. **Análisis de rentabilidad:** Integrado con costos de personal (Enero 2026)

### Decisiones Requeridas

1. ✅ **Proveedores:** Compartidos o separados por sucursal
2. ✅ **Categorías:** Compartidas o separadas
3. ✅ **Estructura Drive:** Múltiples carpetas base o subcarpetas
4. ✅ **Duplicados:** Globales o por sucursal
5. ✅ **Migración datos:** Asignar existentes a Sucursal 1

### Arquitectura Propuesta (Sugerencia)

```
Base de Datos:
  - Tabla `sucursales` (id, nombre, codigo, activa)
  - Campo `sucursal_id` en facturas, ingest_events, ingresos_mensuales, costos_personal
  - Proveedores COMPARTIDOS (sin sucursal_id)
  - Categorías COMPARTIDAS (sin sucursal_id)

Google Drive:
  - Estructura: GOOGLE_DRIVE_FOLDER_ID/sucursal_1/agosto/, sucursal_2/agosto/
  - O múltiples GOOGLE_DRIVE_FOLDER_ID (uno por sucursal)

Backend:
  - Todos los endpoints requieren `sucursal_id` (query param o header)
  - Repositories filtran por sucursal_id automáticamente
  - Dependency `get_sucursal_id()` inyecta sucursal en queries

Frontend:
  - Selector de sucursal en Header (siempre visible)
  - Context/Store para sucursal seleccionada
  - dataProvider incluye sucursal_id en todas las requests
  - Persistencia en localStorage
```

---

**Fin del documento**

*Este documento proporciona toda la información técnica necesaria para diseñar un plan de implementación multi-sucursal. Incluye arquitectura actual, estructura de datos, APIs, flujos de procesamiento y consideraciones de diseño.*

