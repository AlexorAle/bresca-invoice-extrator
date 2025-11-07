# Arquitectura Técnica del Sistema de Extracción de Facturas

## Documento Técnico para Analistas de Negocio

**Versión:** 1.0  
**Fecha:** Octubre 2025  
**Autor:** Equipo de Arquitectura Técnica

---

## 1. Visión General del Sistema

### 1.1 Propósito del Sistema

El sistema de extracción de facturas es una plataforma automatizada diseñada para:

- **Extraer automáticamente** datos estructurados de facturas en formato PDF almacenadas en Google Drive
- **Procesar y normalizar** información financiera (proveedores, importes, fechas, conceptos)
- **Almacenar** datos validados en una base de datos PostgreSQL con trazabilidad completa
- **Visualizar** información procesada mediante un dashboard web interactivo para análisis de negocio

### 1.2 Arquitectura de Alto Nivel

El sistema sigue una arquitectura de **microservicios modulares** con separación clara de responsabilidades:

```
┌─────────────────┐
│  Google Drive   │  ← Fuente de datos (facturas PDF)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         Pipeline de Ingestión                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Descarga │→ │ Extracción│→ │Validación│     │
│  │   PDF    │  │   OCR/IA  │  │  Reglas  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │  ← Almacenamiento persistente
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         API REST (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Facturas │  │  Resumen │  │  Estad.  │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Dashboard Web  │  ← Visualización (React + Vite)
│   (Frontend)    │
└─────────────────┘
```

---

## 2. Componentes Principales del Sistema

### 2.1 Módulo de Integración con Google Drive

**Ubicación:** `src/drive_client.py`

**Responsabilidades:**
- Autenticación mediante Service Account de Google Cloud
- Listado recursivo de archivos PDF en carpetas organizadas por mes
- Descarga de archivos PDF a almacenamiento temporal local
- Sincronización incremental basada en timestamps de modificación

**Tecnologías:**
- Google Drive API v3
- Service Account Authentication (OAuth 2.0)
- Retry logic con exponential backoff para manejo de errores transitorios

**Flujo de Operación:**
1. Autenticación con credenciales de Service Account
2. Búsqueda de carpetas mensuales (configurables: agosto, septiembre, octubre, etc.)
3. Filtrado de archivos PDF por extensión
4. Descarga de archivos a directorio temporal (`temp/`)
5. Retorno de metadatos: nombre, ID, tamaño, fecha de modificación

### 2.2 Módulo de Extracción de Datos (OCR/IA)

**Ubicación:** `src/ocr_extractor.py`

**Arquitectura Híbrida de Extracción:**

El sistema implementa una estrategia de **extracción en cascada** con dos niveles:

#### 2.2.1 Extracción Primaria: OpenAI GPT-4o-mini Vision

**Tecnología:** OpenAI Vision API (modelo `gpt-4o-mini`)

**Proceso:**
1. Conversión de primera página del PDF a imagen PNG (resolución 200 DPI)
2. Redimensionamiento automático si excede 1024x1024 píxeles (límite de API)
3. Codificación a Base64 para transmisión
4. Envío a OpenAI Vision API con prompt estructurado en JSON
5. Extracción de campos:
   - `nombre_proveedor` (emisor de la factura) - **OBLIGATORIO**
   - `nombre_cliente` (receptor de la factura) - Opcional
   - `importe_total` (valor numérico)
   - `fecha_emision` (formato YYYY-MM-DD)
   - `confianza` (alta/media/baja)

**Ventajas:**
- Alta precisión en reconocimiento de texto estructurado
- Comprensión contextual de documentos
- Manejo de múltiples formatos de factura
- Extracción de campos semánticos (no solo texto)

**Limitaciones:**
- Dependencia de conectividad a API externa
- Costos por token procesado
- Rate limiting (3 segundos entre llamadas)

#### 2.2.2 Extracción Secundaria: Tesseract OCR

**Tecnología:** Tesseract OCR (open-source)

**Activación:**
- Fallback automático si OpenAI falla o retorna confianza baja
- Complemento cuando OpenAI no encuentra campos críticos

**Proceso:**
1. Conversión de PDF a imagen (150 DPI)
2. Extracción de texto mediante OCR
3. Parsing con expresiones regulares para campos específicos:
   - Patrones para "Cliente:", "Total:", "Fecha:", etc.
4. Retorno de datos con confianza marcada como "baja"

**Ventajas:**
- Sin dependencia de servicios externos
- Sin costos adicionales
- Procesamiento local

**Limitaciones:**
- Menor precisión que IA
- Dependiente de calidad de imagen
- Requiere patrones regex específicos

#### 2.2.3 Estrategia de Combinación

El sistema implementa **combinación inteligente** de resultados:
- Si OpenAI retorna confianza "alta" o "media" → usar resultado completo
- Si OpenAI retorna confianza "baja" o falta campo crítico → complementar con Tesseract
- Priorizar datos de OpenAI pero llenar campos faltantes con Tesseract

### 2.3 Módulo de Normalización y Validación

**Ubicación:** `src/parser_normalizer.py`

**Responsabilidades:**

#### 2.3.1 Normalización de Datos

**Fechas:**
- Conversión de múltiples formatos (DD/MM/YYYY, YYYY-MM-DD, DD.MM.YYYY) a ISO 8601
- Validación de fechas válidas
- Manejo de fechas faltantes (NULL)

**Importes:**
- Normalización de separadores decimales (coma vs punto)
- Eliminación de símbolos de moneda (€, $)
- Conversión a tipo numérico (DECIMAL en BD)
- Manejo de valores negativos (facturas de abono)

**Proveedores:**
- Limpieza de espacios y caracteres especiales
- Normalización de mayúsculas/minúsculas
- Validación de campo obligatorio

#### 2.3.2 Generación de Hash de Contenido

**Algoritmo:** SHA-256 del contenido binario del PDF

**Propósito:**
- Detección de duplicados exactos
- Verificación de integridad
- Trazabilidad de versiones

**Implementación:**
```python
hash_contenido = SHA256(contenido_binario_pdf)
```

### 2.4 Pipeline de Ingestión

**Ubicación:** `src/pipeline/ingest.py`

**Flujo Completo de Procesamiento:**

```
1. VALIDACIÓN DE ARCHIVO
   ├─ Verificar integridad del PDF
   ├─ Validar tamaño esperado
   └─ Detectar PDFs protegidos con contraseña

2. EXTRACCIÓN DE DATOS
   ├─ Intentar OpenAI Vision API
   ├─ Fallback a Tesseract si es necesario
   └─ Combinar resultados si aplica

3. NORMALIZACIÓN
   ├─ Normalizar fechas, importes, proveedores
   ├─ Generar hash de contenido
   └─ Crear DTO (Data Transfer Object)

4. VALIDACIÓN CRÍTICA
   ├─ Verificar proveedor obligatorio
   ├─ Verificar importe_total no NULL
   └─ Marcar como error si falla

5. DETECCIÓN DE DUPLICADOS
   ├─ Buscar por drive_file_id
   ├─ Buscar por hash_contenido
   ├─ Buscar por proveedor + número_factura
   └─ Decidir acción: INSERT / UPDATE / IGNORE / DUPLICATE / REVIEW

6. VALIDACIÓN DE REGLAS DE NEGOCIO
   ├─ Validar rangos de importes
   ├─ Validar fechas razonables
   └─ Validar estructura fiscal

7. PERSISTENCIA
   ├─ UPSERT en tabla facturas
   ├─ Actualizar tabla proveedores
   └─ Registrar evento en ingest_events

8. AUDITORÍA
   ├─ Registrar timestamp de procesamiento
   ├─ Guardar metadatos (extractor usado, confianza)
   └─ Logging estructurado
```

#### 2.4.1 Sistema de Detección de Duplicados

**Ubicación:** `src/pipeline/duplicate_manager.py`

**Estrategia Multi-Criterio:**

1. **Duplicado por File ID:** Mismo archivo en Drive ya procesado
   - Si hash no cambió → IGNORE (sin cambios)
   - Si hash cambió → UPDATE_REVISION (nueva versión)

2. **Duplicado por Hash:** Mismo contenido, diferente archivo
   - → DUPLICATE (mover a cuarentena)

3. **Duplicado por Número de Factura:** Mismo proveedor + mismo número
   - → REVIEW (requiere revisión manual)

4. **Sin duplicados detectados:**
   - → INSERT (nueva factura)

**Estados de Factura:**
- `procesado`: Extracción exitosa y validada
- `pendiente`: En cola de procesamiento
- `error`: Error crítico (sin proveedor, sin importe)
- `revisar`: Requiere revisión manual (duplicado potencial, validación fallida)
- `duplicado`: Duplicado confirmado

#### 2.4.2 Sistema de Cuarentena

**Propósito:** Aislar archivos problemáticos para revisión manual

**Ubicación:** `data/quarantine/`

**Archivos en Cuarentena:**
- Facturas con errores críticos
- Duplicados detectados
- Archivos que requieren revisión manual

**Metadatos:** Cada archivo en cuarentena incluye archivo `.meta.json` con:
- Información del archivo original
- Error o razón de cuarentena
- Timestamp de cuarentena
- Datos extraídos (si aplica)

### 2.5 Capa de Persistencia (Base de Datos)

**Tecnología:** PostgreSQL 14+

**Ubicación:** `src/db/models.py`, `src/db/repositories.py`

#### 2.5.1 Esquema de Base de Datos

**Tabla: `facturas`**

Campos principales:
- `id`: Identificador único (BigInteger, auto-incremental)
- `drive_file_id`: ID único del archivo en Google Drive (único)
- `drive_file_name`: Nombre original del archivo
- `drive_folder_name`: Carpeta de origen (mes)
- `proveedor_id`: FK a tabla proveedores
- `proveedor_text`: Nombre del proveedor (texto libre)
- `numero_factura`: Número de factura del proveedor
- `fecha_emision`: Fecha de emisión (DATE)
- `fecha_recepcion`: Timestamp de procesamiento
- `importe_total`: Importe total (DECIMAL 18,2) - **Permite NULL para facturas en revisión**
- `base_imponible`: Base imponible (DECIMAL 18,2)
- `impuestos_total`: Total de impuestos (DECIMAL 18,2)
- `iva_porcentaje`: Porcentaje de IVA (DECIMAL 5,2)
- `conceptos_json`: Conceptos en formato JSONB
- `metadatos_json`: Metadatos adicionales (JSONB)
- `extractor`: Extractor usado ('openai', 'tesseract', 'hybrid')
- `confianza`: Nivel de confianza ('alta', 'media', 'baja')
- `hash_contenido`: Hash SHA-256 (único, permite NULL)
- `revision`: Número de revisión (incrementa en actualizaciones)
- `estado`: Estado de procesamiento
- `error_msg`: Mensaje de error si aplica
- `creado_en`, `actualizado_en`: Timestamps de auditoría

**Índices:**
- `idx_facturas_hash_contenido_unique`: Hash único (para detección de duplicados)
- `idx_facturas_proveedor_numero`: Búsqueda por proveedor + número
- `idx_facturas_estado`: Filtrado por estado
- `idx_facturas_drive_modified`: Sincronización incremental

**Tabla: `proveedores`**

- `id`: Identificador único
- `nombre`: Nombre del proveedor (único)
- `nif_cif`: NIF/CIF del proveedor
- `email_contacto`: Email de contacto
- `creado_en`: Timestamp de creación

**Tabla: `ingest_events`**

Auditoría completa del proceso:
- `id`: Identificador único
- `drive_file_id`: ID del archivo procesado
- `etapa`: Etapa del proceso ('ingest_start', 'extraction', 'validation', 'ingest_complete', etc.)
- `nivel`: Nivel de log ('INFO', 'WARNING', 'ERROR')
- `detalle`: Mensaje descriptivo
- `hash_contenido`: Hash asociado
- `decision`: Decisión de duplicado (si aplica)
- `ts`: Timestamp del evento

**Tabla: `sync_state`**

Estado de sincronización incremental:
- `key`: Clave de estado (ej: 'last_sync_timestamp')
- `value`: Valor del estado
- `updated_at`: Última actualización

#### 2.5.2 Repositorio de Datos

**Ubicación:** `src/db/repositories.py`

**Clase: `FacturaRepository`**

Métodos principales:
- `file_exists(drive_file_id)`: Verificar si archivo ya procesado
- `find_by_file_id(drive_file_id)`: Buscar por ID de Drive
- `find_by_hash(hash_contenido)`: Buscar por hash
- `find_by_invoice_number(proveedor, numero)`: Buscar por número de factura
- `upsert_factura(factura_dto, increment_revision)`: Insertar o actualizar
- `get_summary_by_month(month, year)`: Resumen estadístico del mes
- `get_facturas_by_day(month, year)`: Agrupación por día
- `get_recent_facturas(month, year, limit)`: Facturas recientes
- `get_categories_breakdown(month, year)`: Desglose por proveedor
- `get_all_facturas_by_month(month, year)`: Listado completo

**Optimizaciones:**
- Uso de índices para consultas frecuentes
- Agregaciones SQL para cálculos de resumen
- Paginación implícita en consultas de listado

### 2.6 API REST (Backend)

**Tecnología:** FastAPI (Python)

**Ubicación:** `src/api/main.py`, `src/api/routes/facturas.py`

#### 2.6.1 Endpoints Principales

**Base URL:** `/api/facturas`

1. **GET `/summary`**
   - Parámetros: `month` (1-12), `year` (2000-2100)
   - Retorna: Resumen estadístico del mes
     - Total de facturas
     - Importe total
     - Promedio por factura
     - Cantidad de proveedores únicos
     - Cambios porcentuales vs mes anterior

2. **GET `/by_day`**
   - Parámetros: `month`, `year`
   - Retorna: Facturas agrupadas por día del mes
     - Fecha
     - Cantidad de facturas
     - Importe total del día

3. **GET `/recent`**
   - Parámetros: `month`, `year`, `limit` (default: 5)
   - Retorna: Facturas más recientes del mes
     - ID, número, proveedor, fecha, importes

4. **GET `/list`**
   - Parámetros: `month`, `year`
   - Retorna: Listado completo de facturas del mes
     - Todos los campos relevantes

5. **GET `/categories`**
   - Parámetros: `month`, `year`
   - Retorna: Desglose por proveedor (categoría)
     - Nombre del proveedor
     - Cantidad de facturas
     - Importe total
     - Porcentaje del total

6. **GET `/failed`**
   - Parámetros: `month`, `year`
   - Retorna: Lista de facturas fallidas (desde cuarentena)
     - Nombre del archivo
     - Timestamp de error

#### 2.6.2 Características Técnicas

**CORS:** Configurado para permitir requests desde frontend
- Orígenes permitidos: localhost (varios puertos), IP de producción

**Manejo de Errores:**
- Exception handler global
- Logging estructurado de errores
- Respuestas HTTP estándar (200, 400, 500)

**Validación:**
- Validación de parámetros con Pydantic
- Validación de rangos (mes 1-12, año 2000-2100)
- Schemas de respuesta tipados

### 2.7 Dashboard Web (Frontend)

**Tecnología:** React 18 + Vite + TailwindCSS

**Ubicación:** `frontend/src/`

#### 2.7.1 Arquitectura del Frontend

**Estructura de Componentes:**

```
Dashboard (Componente Principal)
├── Header
│   ├── Selector de Mes/Año
│   └── Título y Navegación
├── KPIGrid
│   └── KPICard (x4)
│       ├── Facturas del Mes
│       ├── Importe Total
│       ├── Promedio por Factura
│       └── Proveedores Únicos
├── CategoriesPanel
│   └── Tabla de Desglose por Proveedor
├── AnalysisGrid
│   ├── QualityPanel (Métricas de Calidad)
│   └── FailedInvoicesPanel (Facturas Fallidas)
└── FacturasTable
    └── Tabla Completa de Facturas
```

#### 2.7.2 Flujo de Datos en el Frontend

**Hook Personalizado: `useInvoiceData`**

```javascript
useInvoiceData(month, year)
  ↓
Promise.all([
  fetchInvoiceSummary(month, year),
  fetchInvoicesByDay(month, year),
  fetchRecentInvoices(month, year, 5),
  fetchCategoriesBreakdown(month, year),
  fetchFailedInvoices(month, year),
  fetchAllFacturas(month, year)
])
  ↓
Transformación de Datos
  ├── KPIs (transformToKPIs)
  ├── Métricas de Calidad (extractQualityMetrics)
  └── Datos de Gráficos
  ↓
setData({ summary, kpis, chartData, ... })
  ↓
Renderizado de Componentes
```

**Características:**
- **Fetch Paralelo:** Todas las peticiones se ejecutan simultáneamente
- **Estado de Carga:** Loading spinner durante fetch
- **Manejo de Errores:** Pantalla de error con opción de reintentar
- **Re-fetch Automático:** Actualización al cambiar mes/año

#### 2.7.3 Componentes de Visualización

**KPIGrid:**
- 4 tarjetas de métricas principales
- Formato de moneda (EUR) con separadores
- Indicadores de cambio porcentual (vs mes anterior)
- Iconos y colores diferenciados por métrica

**CategoriesPanel:**
- Tabla responsive con desglose por proveedor
- Ordenamiento por importe total (descendente)
- Porcentaje del total por proveedor
- Formato de moneda

**AnalysisGrid:**
- **QualityPanel:** Distribución de confianza (alta/media/baja)
- **FailedInvoicesPanel:** Lista de facturas en cuarentena

**FacturasTable:**
- Tabla completa con todas las facturas del mes
- Columnas: Número, Proveedor, Fecha, Importes, Estado, Confianza
- Formato responsive (scroll horizontal en móvil)
- Ordenamiento por fecha (más recientes primero)

#### 2.7.4 Diseño Responsive

**Breakpoints:**
- Mobile: < 640px (1 columna)
- Tablet: 640px - 1024px (2 columnas)
- Desktop: > 1024px (4 columnas para KPIs)

**Tecnologías de Estilo:**
- TailwindCSS para estilos utilitarios
- Gradientes y sombras para diseño moderno
- Animaciones de carga (skeleton loaders)

---

## 3. Flujo Completo de Procesamiento

### 3.1 Flujo de Ingestión de Facturas

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INICIO: Ejecución del Pipeline                           │
│    - Configuración desde .env                               │
│    - Conexión a Google Drive                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. LISTADO DE ARCHIVOS                                      │
│    - Búsqueda de carpetas mensuales                         │
│    - Filtrado de archivos PDF                               │
│    - Verificación de sincronización incremental             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. DESCARGA DE ARCHIVOS                                     │
│    - Descarga a directorio temporal                         │
│    - Validación de integridad                               │
│    - Verificación de tamaño                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. EXTRACCIÓN DE DATOS (Por cada archivo)                  │
│    ├─ Conversión PDF → Imagen                               │
│    ├─ Envío a OpenAI Vision API                            │
│    ├─ Si falla → Tesseract OCR                             │
│    └─ Combinación de resultados                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. NORMALIZACIÓN                                            │
│    ├─ Normalizar fechas → YYYY-MM-DD                       │
│    ├─ Normalizar importes → DECIMAL                        │
│    ├─ Limpiar nombres de proveedores                        │
│    └─ Generar hash SHA-256                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. VALIDACIÓN CRÍTICA                                       │
│    ├─ ¿Proveedor existe? → Si no → ERROR                   │
│    ├─ ¿Importe existe? → Si no → ERROR                      │
│    └─ Si error → Mover a cuarentena                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. DETECCIÓN DE DUPLICADOS                                  │
│    ├─ Buscar por drive_file_id                              │
│    ├─ Buscar por hash_contenido                             │
│    ├─ Buscar por proveedor + número                         │
│    └─ Decidir: INSERT / UPDATE / IGNORE / DUPLICATE / REVIEW│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. VALIDACIÓN DE REGLAS DE NEGOCIO                          │
│    ├─ Validar rangos de importes                            │
│    ├─ Validar fechas razonables                             │
│    └─ Si falla → Marcar para revisión                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. PERSISTENCIA EN BASE DE DATOS                            │
│    ├─ UPSERT en tabla facturas                              │
│    ├─ Actualizar/crear en tabla proveedores                 │
│    └─ Registrar evento en ingest_events                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. LIMPIEZA                                                │
│     ├─ Eliminar archivos temporales                        │
│     └─ Registrar estadísticas finales                       │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Flujo de Visualización en Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USUARIO SELECCIONA MES/AÑO                                │
│    - Cambio en selector de Header                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. HOOK useInvoiceData SE ACTIVA                             │
│    - Estado: loading = true                                 │
│    - Limpia datos anteriores                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. FETCH PARALELO A API REST                                 │
│    - GET /api/facturas/summary                               │
│    - GET /api/facturas/by_day                                │
│    - GET /api/facturas/recent                                │
│    - GET /api/facturas/categories                            │
│    - GET /api/facturas/failed                                │
│    - GET /api/facturas/list                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. API REST CONSULTA BASE DE DATOS                           │
│    - FacturaRepository ejecuta queries SQL                   │
│    - Agregaciones y cálculos en BD                           │
│    - Retorno de datos JSON                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. TRANSFORMACIÓN DE DATOS EN FRONTEND                      │
│    - Cálculo de KPIs                                         │
│    - Extracción de métricas de calidad                       │
│    - Formateo de monedas y fechas                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. RENDERIZADO DE COMPONENTES                                │
│    - KPIGrid: 4 tarjetas de métricas                        │
│    - CategoriesPanel: Tabla de proveedores                  │
│    - AnalysisGrid: Calidad y errores                         │
│    - FacturasTable: Lista completa                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Tecnologías y Dependencias

### 4.1 Backend (Python)

**Framework Web:**
- FastAPI 0.104+: Framework REST API moderno y rápido
- Uvicorn: Servidor ASGI de alto rendimiento

**Base de Datos:**
- SQLAlchemy 2.0+: ORM para PostgreSQL
- psycopg2: Driver de PostgreSQL
- Alembic: Migraciones de base de datos (opcional)

**Procesamiento de Documentos:**
- pdf2image: Conversión PDF → Imagen
- Pillow (PIL): Procesamiento de imágenes
- pypdf: Validación de PDFs

**IA y OCR:**
- openai: Cliente para OpenAI Vision API
- pytesseract: Wrapper para Tesseract OCR
- tenacity: Retry logic con exponential backoff

**Integración Cloud:**
- google-api-python-client: Cliente de Google Drive API
- google-auth: Autenticación OAuth 2.0

**Utilidades:**
- python-dotenv: Gestión de variables de entorno
- pydantic: Validación de datos y schemas

### 4.2 Frontend (JavaScript/React)

**Framework:**
- React 18: Biblioteca de UI
- Vite: Build tool y dev server

**Estilos:**
- TailwindCSS: Framework de CSS utilitario
- PostCSS: Procesamiento de CSS

**HTTP Client:**
- Fetch API nativo (sin librerías adicionales)

### 4.3 Infraestructura

**Base de Datos:**
- PostgreSQL 14+: Base de datos relacional

**Servicios Externos:**
- Google Drive API: Almacenamiento de facturas
- OpenAI API: Extracción de datos con IA

**Herramientas de Desarrollo:**
- Docker (opcional): Containerización
- Traefik (opcional): Reverse proxy

---

## 5. Seguridad y Auditoría

### 5.1 Seguridad

**Autenticación:**
- Service Account de Google Cloud con permisos mínimos (solo lectura)
- Credenciales almacenadas en archivo JSON con permisos 600 (solo owner)

**Validación de Entrada:**
- Validación de tipos y rangos en API REST
- Sanitización de datos antes de inserción en BD
- Prevención de SQL injection mediante ORM (SQLAlchemy)

**Variables Sensibles:**
- Almacenamiento en archivo `.env` (no versionado)
- No hardcodeo de credenciales en código

**Permisos de Archivos:**
- Validación de permisos de archivos de credenciales
- Directorios temporales con permisos restrictivos

### 5.2 Auditoría

**Logging Estructurado:**
- Formato JSON para fácil parsing
- Niveles: DEBUG, INFO, WARNING, ERROR
- Rotación automática de logs (10MB por archivo)

**Tabla de Eventos:**
- Registro completo en `ingest_events`
- Trazabilidad de cada archivo procesado
- Timestamps de cada etapa del proceso

**Metadatos:**
- Hash de contenido para verificación de integridad
- Timestamps de creación y actualización
- Número de revisión para tracking de versiones

---

## 6. Escalabilidad y Rendimiento

### 6.1 Optimizaciones Implementadas

**Base de Datos:**
- Índices en columnas frecuentemente consultadas
- Agregaciones SQL en lugar de procesamiento en memoria
- Constraints para validación a nivel de BD

**Procesamiento:**
- Delay entre llamadas a API (3 segundos) para evitar rate limiting
- Procesamiento secuencial de archivos (evita sobrecarga)
- Limpieza automática de archivos temporales

**Frontend:**
- Fetch paralelo de endpoints (Promise.all)
- Componentes lazy loading (si aplica)
- Optimización de re-renders con React hooks

### 6.2 Limitaciones Actuales

**Procesamiento:**
- Procesamiento secuencial (no paralelo) de facturas
- Dependencia de rate limits de OpenAI API
- Tiempo de procesamiento: ~3-5 segundos por factura

**Almacenamiento:**
- Archivos temporales en disco local
- Sin sistema de cola de mensajes para procesamiento asíncrono

**Escalabilidad:**
- Arquitectura monolítica (no distribuida)
- Sin balanceador de carga
- Sin cache de resultados

### 6.3 Oportunidades de Mejora

**Corto Plazo:**
- Implementar procesamiento paralelo con workers
- Cache de resultados de API en Redis
- Sistema de cola (Celery + RabbitMQ) para procesamiento asíncrono

**Mediano Plazo:**
- Microservicios separados (extracción, API, dashboard)
- Load balancer para API REST
- CDN para assets del frontend

**Largo Plazo:**
- Kubernetes para orquestación
- Base de datos replicada (read replicas)
- Sistema de eventos (Kafka) para desacoplamiento

---

## 7. Monitoreo y Mantenimiento

### 7.1 Logging

**Ubicación:** `logs/extractor.log`

**Formato:** JSON estructurado
```json
{
  "timestamp": "2025-10-30T12:00:00Z",
  "level": "INFO",
  "module": "pipeline.ingest",
  "message": "Factura procesada exitosamente",
  "drive_file_id": "abc123",
  "elapsed_ms": 3500
}
```

**Rotación:** 10MB por archivo, mantener últimos 10 archivos

### 7.2 Métricas Clave

**Procesamiento:**
- Tasa de éxito/fallo de extracción
- Tiempo promedio de procesamiento por factura
- Distribución de confianza (alta/media/baja)

**Calidad:**
- Porcentaje de facturas con proveedor encontrado
- Porcentaje de facturas con importe encontrado
- Tasa de duplicados detectados

**Rendimiento:**
- Tiempo de respuesta de API REST
- Tiempo de carga del dashboard
- Uso de recursos (CPU, memoria)

### 7.3 Alertas Recomendadas

- Tasa de fallo > 10%
- Tiempo de procesamiento > 10 segundos por factura
- Errores de conexión a OpenAI API
- Errores de conexión a PostgreSQL
- Espacio en disco < 20%

---

## 8. Conclusiones Técnicas

### 8.1 Fortalezas del Sistema

1. **Arquitectura Modular:** Separación clara de responsabilidades facilita mantenimiento
2. **Extracción Híbrida:** Combinación de IA y OCR garantiza alta tasa de éxito
3. **Detección de Duplicados:** Sistema robusto previene datos duplicados
4. **Auditoría Completa:** Trazabilidad total del proceso
5. **Dashboard Interactivo:** Visualización clara para análisis de negocio

### 8.2 Áreas de Mejora

1. **Procesamiento Paralelo:** Implementar workers para aumentar throughput
2. **Cache:** Reducir carga en BD y APIs externas
3. **Manejo de Errores:** Sistema de reintentos más sofisticado
4. **Testing:** Cobertura de tests unitarios e integración
5. **Documentación:** Documentación de API más detallada

### 8.3 Recomendaciones para Analistas de Negocio

**Para Traducción a Lenguaje Ejecutivo:**

1. **Valor de Negocio:**
   - Automatización completa del proceso manual de extracción
   - Reducción de tiempo de procesamiento de horas a minutos
   - Alta precisión mediante IA (OpenAI GPT-4o-mini)

2. **ROI:**
   - Eliminación de trabajo manual repetitivo
   - Reducción de errores humanos
   - Trazabilidad completa para auditorías

3. **Riesgos:**
   - Dependencia de servicios externos (OpenAI, Google Drive)
   - Costos de API por factura procesada
   - Requiere revisión manual de facturas con baja confianza

4. **Escalabilidad:**
   - Sistema preparado para crecimiento
   - Arquitectura permite mejoras incrementales
   - Base de datos optimizada para consultas rápidas

---

## Anexos

### A.1 Glosario de Términos Técnicos

- **OCR (Optical Character Recognition):** Reconocimiento óptico de caracteres
- **IA (Inteligencia Artificial):** Modelos de machine learning para comprensión de documentos
- **API REST:** Interfaz de programación basada en HTTP
- **DTO (Data Transfer Object):** Objeto de transferencia de datos
- **Hash:** Función criptográfica que genera identificador único de contenido
- **UPSERT:** Operación que inserta o actualiza según existencia
- **JSONB:** Tipo de dato JSON binario en PostgreSQL
- **Service Account:** Cuenta de servicio para autenticación automatizada
- **Rate Limiting:** Limitación de velocidad de requests a API

### A.2 Diagramas de Secuencia

**Procesamiento de una Factura:**

```
Usuario → Pipeline → DriveClient → Descarga PDF
                              ↓
                         OCR Extractor
                              ├─ OpenAI API
                              └─ Tesseract (fallback)
                              ↓
                         Parser Normalizer
                              ↓
                         Duplicate Manager
                              ↓
                         FacturaRepository → PostgreSQL
                              ↓
                         IngestEvent → Auditoría
```

**Visualización en Dashboard:**

```
Usuario → Dashboard → useInvoiceData
                          ↓
                    Fetch Paralelo
                          ├─ /summary
                          ├─ /by_day
                          ├─ /recent
                          ├─ /categories
                          ├─ /failed
                          └─ /list
                          ↓
                    FacturaRepository
                          ↓
                    PostgreSQL
                          ↓
                    Transformación
                          ↓
                    Renderizado UI
```

---

**Fin del Documento**



