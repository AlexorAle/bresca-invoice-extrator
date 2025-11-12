# Arquitectura del Servidor - Visión General

**Última actualización:** 2025-11-12  
**Servidor:** VPS (82.25.101.32)  
**Ubicación de proyectos:** `~/proyectos`

---

## 1. Visión general del servidor

### Descripción
Servidor VPS que aloja múltiples aplicaciones de negocio relacionadas con:
- Trading automatizado y análisis de inversiones
- Procesamiento y extracción de facturas
- Sincronización y reportes desde Google Drive
- Monitoreo y gestión de infraestructura

### Rutas importantes
- **Proyectos:** `~/proyectos`
- **Infraestructura:** `~/proyectos/infra`
- **Backups:** (Por completar: ubicación de backups)

### Organización
Las aplicaciones se organizan como repositorios independientes dentro de `~/proyectos`, compartiendo infraestructura común (Traefik como reverse proxy, bases de datos compartidas cuando aplica).

---

## 2. Lista de aplicaciones / proyectos

| Aplicación | Ruta interna | URL externa | Estado | Stack principal |
|------------|--------------|-------------|--------|------------------|
| **Trading Bot** | `~/proyectos/bot-trading` | `http://82.25.101.32/bot` (dashboard)<br>`http://82.25.101.32/api/trading` (API) | Activo | Python + Streamlit + FastAPI + Postgres + Redis |
| **Investment Dashboard** | `~/proyectos/investment-dashboard` | `http://82.25.101.32/Investment-portfolio` | Activo | Next.js 15 + FastAPI + Postgres |
| **Invoice Extractor** | `~/proyectos/invoice-extractor` | `http://82.25.101.32/invoice-dashboard` (frontend)<br>`http://82.25.101.32/invoice-api` (backend) | Activo | FastAPI + React + Postgres |
| **Bresca Reportes Drive** | `~/proyectos/bresca-reportes-drive-dash` | Por completar: URL externa | Activo | Python + Streamlit + DuckDB |
| **Command Center** | `~/proyectos/infra/command-center` | `http://82.25.101.32/command-center` | Activo | FastAPI + React |
| **Traefik** | `~/proyectos/infra/traefik` | `http://82.25.101.32:8080` (dashboard) | Activo | Reverse Proxy |

---

## 3. Arquitectura técnica por aplicación

### 3.1 Trading Bot

#### Información general
- **Nombre funcional:** Trading Bot con Dashboard de Monitoreo
- **Ruta interna:** `~/proyectos/bot-trading`
- **URL externa:**
  - Dashboard: `http://82.25.101.32/bot`
  - API: `http://82.25.101.32/api/trading`
- **Estado:** Activo

#### Stack tecnológico
- **Backend:** Python 3.12
  - Librerías clave: `ccxt`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `TA-Lib`, `backtrader`, `optuna`
  - Framework web: FastAPI (implícito en docker-compose)
  - Bot de Telegram: `python-telegram-bot`
  - Dashboard: Streamlit 1.50.0
- **Base de datos:** PostgreSQL 15 (contenedor `postgres`)
- **Cache:** Redis 7 (contenedor `redis`)
- **Monitoreo:** Prometheus + Grafana
- **Exchanges:** CCXT (soporte múltiples exchanges)

#### Componentes y arquitectura
- **Trading Bot Service:** Motor de trading con estrategias, gestión de riesgo, ejecución de órdenes
- **Streamlit Dashboard:** Visualización de métricas, logs, estado del bot
- **Prometheus:** Métricas de rendimiento y trading
- **Grafana:** Dashboards de visualización
- **Redis:** Cache de datos de mercado y estado de sesión
- **PostgreSQL:** Almacenamiento de operaciones, historial, configuraciones

#### Ejecución y despliegue
- **Orquestación:** Docker Compose (`infrastructure/docker-compose.yml`)
- **Red:** `traefik-public` (red externa compartida)
- **Puertos internos:**
  - Trading Bot API: `8080` (expose only, no public)
  - Streamlit Dashboard: `8501` (expose only, no public)
  - Prometheus: `9090` (expose only, no public)
  - Grafana: `3000` (expose only, no public)
- **Reverse Proxy (Traefik):**
  - Dashboard: `Host(82.25.101.32) && PathPrefix(/bot)` → puerto 8501
  - API: `Host(82.25.101.32) && PathPrefix(/api/trading)` → puerto 8080
  - Prometheus: `Host(82.25.101.32) && PathPrefix(/infra)` → puerto 9090
  - Grafana: `Host(82.25.101.32) && PathPrefix(/grafana)` → puerto 3000
- **Volúmenes:**
  - `logs/`, `backups/`, `configs/` montados desde el host
  - Datos persistentes: `prometheus_data`, `grafana_data`, `redis_data`, `postgres_data`

#### Repositorio y ramas Git
- **Ruta local:** `~/proyectos/bot-trading`
- **Remoto:** `https://github.com/AlexorAle/bot-trading.git`
- **Rama principal:** `main`
- **Total de ramas:** 6 (5 remotes + 1 local)
- **Ramas relevantes:**
  - `main` (activa)
  - `feature/monitoring-stack` (long-lived feature)
  - `cursor/analizar-y-reportar-archivos-de-prueba-obsoletos-c620` (cursor branch, posiblemente obsoleta)
  - `cursor/review-crypto-bot-monitoring-implementation-00d1` (cursor branch, posiblemente obsoleta)
- **Comentarios sobre branching:**
  - Modelo híbrido: `main` como trunk, features en ramas separadas
  - Presencia de ramas cursor/* sugiere uso de herramientas de IA para desarrollo
  - **Recomendación:** Revisar y mergear/eliminar ramas cursor/* obsoletas

#### Environments y configuración
- **Archivos `.env`:**
  - `~/proyectos/bot-trading/.env` (configuración principal)
  - `~/proyectos/bot-trading/infrastructure/.env` (configuración de infraestructura)
  - `~/proyectos/bot-trading/.env.example` (template)
- **Variables críticas:**
  - `EXCHANGE`, `API_KEY`, `SECRET` (credenciales de exchange)
  - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (notificaciones)
  - `POSTGRES_PASSWORD`, `GRAFANA_PASSWORD`
- **Riesgos potenciales:**
  - Secretos en `.env` (no versionado, pero verificar permisos `chmod 600`)
- **Recomendaciones:**
  - Usar gestor de secretos (HashiCorp Vault, AWS Secrets Manager) para producción
  - Separar config por entorno (dev/staging/prod)

#### Mantenimiento y tareas sugeridas
- Limpieza periódica de logs antiguos en `logs/`
- Revisión y archivo de ramas cursor/* obsoletas
- Rotación de backups en `backups/`
- Actualización de dependencias Python (especialmente `ccxt` para soporte de exchanges)
- Revisión de métricas de Prometheus (retention: 30 días configurado)

---

### 3.2 Investment Dashboard

#### Información general
- **Nombre funcional:** Investment Portfolio Dashboard
- **Ruta interna:** `~/proyectos/investment-dashboard`
- **URL externa:**
  - Frontend: `http://82.25.101.32/Investment-portfolio`
  - Backend API: `http://82.25.101.32/Investment-portfolio-api`
- **Estado:** Activo

#### Stack tecnológico
- **Frontend:**
  - Next.js 15 (App Router)
  - React 19
  - TypeScript
  - TailwindCSS
  - Radix UI (componentes)
  - Recharts (gráficos)
  - Zustand (estado global)
  - TanStack React Query (data fetching)
- **Backend:**
  - FastAPI
  - Python 3.x
  - Uvicorn
- **Proveedores externos:**
  - CoinMarketCap API (cripto)
  - Yahoo Finance (`yfinance`) (acciones/ETF)
  - Twelve Data API (fallback)
  - Web scraping con Playwright + BeautifulSoup (Financial Times para fondos)
- **Base de datos:** PostgreSQL (compartida con trading bot en docker-compose)

#### Componentes y arquitectura
- **Frontend (Next.js):**
  - App Router en `app/`
  - Bootstrap de datos desde Excel: `public/operaciones.xlsx`
  - Componentes de dashboard en `src/components/dashboard/`
  - Estado global con Zustand (`src/store/dashboardStore.ts`)
  - Proxy de API mediante rewrites en `next.config.mjs`
- **Backend (FastAPI):**
  - Endpoints REST bajo `/api/*`
  - WebSocket en `/ws/alerts` (alertas de precios)
  - Cache en memoria con TTL configurable
  - Logging de peticiones y métricas en `backend/app/api_timings.jsonl`
- **Integración:**
  - Rewrites de Next.js: `/api/*` → `http://localhost:8000/api/:path*`
  - `basePath: '/Investment-portfolio'` para servir bajo subpath
  - Enriquecimiento de datos: frontend llama a backend para completar precios de tickers

#### Ejecución y despliegue
- **Orquestación:** Docker Compose (integrado en `bot-trading/infrastructure/docker-compose.yml`)
- **Servicios:**
  - `investment-backend`: FastAPI en puerto `8000` (expose only)
  - `investment-frontend`: Next.js en puerto `3000` (expose only)
- **Reverse Proxy (Traefik):**
  - Frontend: `Host(82.25.101.32) && PathPrefix(/Investment-portfolio)` → puerto 3000
  - Backend: `Host(82.25.101.32) && PathPrefix(/Investment-portfolio-api)` → puerto 8000
  - Middleware: strip prefix para backend, NO strip para frontend (Next.js maneja basePath)
- **Variables de entorno:**
  - Frontend: `NEXT_PUBLIC_API_URL=http://82.25.101.32/Investment-portfolio-api`
  - Backend: `DATABASE_URL`, `REDIS_URL` (compartidos con trading bot)
  - Backend: `COINMARKETCAP_API_KEY` (requerida), `TWELVE_DATA_API_KEY` (opcional)

#### Repositorio y ramas Git
- **Ruta local:** `~/proyectos/investment-dashboard`
- **Remoto:** `https://github.com/AlexorAle/Investment-Dashboard.git`
- **Rama principal:** `master` (rama activa local: `backup/migracion`)
- **Total de ramas:** 10 (9 remotes + 1 local)
- **Ramas relevantes:**
  - `master` (principal remota)
  - `backup/migracion` (rama local activa, posiblemente de migración a VPS)
  - `codex/add-json-fetch-helper-and-update-hooks` (codex branch)
  - `codex/refactor-cryptosection-and-investmentssection` (codex branch)
  - `codex/remove-asyncio-task-connectivity-test` (codex branch)
  - `codex/remove-print-statement-for-api-key` (codex branch)
  - `codex/restructure-app-directory-and-layout` (codex branch)
- **Comentarios sobre branching:**
  - Modelo con `master` como trunk
  - Múltiples ramas `codex/*` (posiblemente obsoletas, revisar)
  - Rama `backup/migracion` sugiere migración reciente
  - **Recomendación:** Consolidar ramas codex/* y determinar si `backup/migracion` debe mergearse a `master`

#### Environments y configuración
- **Archivos `.env`:**
  - `~/proyectos/investment-dashboard/.env.local` (configuración local)
  - `~/proyectos/investment-dashboard/backend/.env` (backend)
- **Variables críticas:**
  - `COINMARKETCAP_API_KEY` (requerida, validada al iniciar)
  - `TWELVE_DATA_API_KEY` (fallback opcional)
  - `DATABASE_URL`, `REDIS_URL`
- **Riesgos potenciales:**
  - API keys en `.env.local` (verificar permisos)
- **Recomendaciones:**
  - Usar gestor de secretos para API keys
  - Documentar límites de rate limiting de APIs externas

#### Mantenimiento y tareas sugeridas
- Actualización periódica de `public/operaciones.xlsx`
- Limpieza de logs en `backend/app/api_timings.jsonl`
- Revisión y merge/eliminación de ramas codex/* obsoletas
- Consolidación de rama `backup/migracion` si la migración está completa
- Monitoreo de rate limits de CoinMarketCap y Twelve Data
- Actualización de dependencias (Next.js, React, FastAPI)

---

### 3.3 Invoice Extractor

#### Información general
- **Nombre funcional:** Invoice Extractor - Sistema de Extracción y Procesamiento de Facturas
- **Ruta interna:** `~/proyectos/invoice-extractor`
- **URL externa:**
  - Frontend: `http://82.25.101.32/invoice-dashboard`
  - Backend API: `http://82.25.101.32/invoice-api`
- **Estado:** Activo

#### Stack tecnológico
- **Backend:**
  - FastAPI 0.104.1
  - Python 3.12
  - Uvicorn
  - SQLAlchemy 2.0.23
  - PostgreSQL (base de datos `negocio_db`)
  - Google Drive API (sincronización)
  - OpenAI API (procesamiento de texto)
  - PDF processing: `pdf2image`, `pytesseract`, `pypdf`
- **Frontend:**
  - React 19.1.1
  - Vite 7.1.7
  - TypeScript
  - TailwindCSS
  - Recharts (gráficos)
  - Lucide React (iconos)
- **Procesamiento:**
  - OCR: Tesseract (vía `pytesseract`)
  - LLM: OpenAI (análisis de facturas)

#### Componentes y arquitectura
- **Backend (FastAPI):**
  - API REST bajo `/api/*`
  - Procesamiento de facturas: descarga desde Google Drive, OCR, extracción con LLM
  - Base de datos: `negocio_db` (PostgreSQL)
  - Almacenamiento: `data/` (facturas procesadas)
  - Logs: `logs/`
- **Frontend (React + Vite):**
  - Dashboard de visualización y gestión
  - Build estático servido por `serve` (servidor HTTP simple, modo SPA)
  - Configuración: `base: '/invoice-dashboard/'` en `vite.config.js` (rutas absolutas)
  - Compatible con Traefik strip prefix para arquitectura multi-proyecto
- **Integración:**
  - Backend usa `network_mode: host` (puerto 8002 expuesto directamente)
  - Traefik file provider configura ruta `/invoice-api` → `http://172.17.0.1:8002`
  - Frontend servido por Traefik en `/invoice-dashboard` con strip prefix
  - Flujo de rutas: Browser → `/invoice-dashboard/assets/...` → Traefik strip → `/assets/...` → Container

#### Ejecución y despliegue
- **Orquestación:** Docker Compose (integrado en `bot-trading/infrastructure/docker-compose.yml`)
- **Servicios:**
  - `invoice-backend`: FastAPI en puerto `8002` (network_mode: host, expuesto directamente)
  - `invoice-frontend`: `serve` sirve build estático en puerto `80` (expose only, modo SPA)
- **Reverse Proxy (Traefik):**
  - Frontend: `Host(82.25.101.32) && PathPrefix(/invoice-dashboard)` → puerto 80
  - Backend: File provider (`config/invoice-api.yml`) → `http://172.17.0.1:8002`
  - Middleware: strip prefix para frontend (elimina `/invoice-dashboard` antes de enviar al container)
  - Configuración: Vite usa `base: '/invoice-dashboard/'` para rutas absolutas compatibles con strip prefix
- **Base de datos:**
  - PostgreSQL local: `postgresql://extractor_user:Dagoba50dago-@localhost:5432/negocio_db`
- **Variables de entorno:**
  - `DATABASE_URL` (PostgreSQL)
  - `DASHBOARD_PORT=8501`, `DASHBOARD_HOST=127.0.0.1` (Streamlit dashboard opcional)
  - OpenAI API key (en `.env`)

#### Repositorio y ramas Git
- **Ruta local:** `~/proyectos/invoice-extractor`
- **Remoto:** `https://github.com/AlexorAle/bresca-invoice-extrator.git`
- **Rama principal:** `main`
- **Total de ramas:** 2 (1 remote + 1 local)
- **Ramas relevantes:**
  - `main` (única rama activa)
- **Comentarios sobre branching:**
  - Modelo trunk-based simple (solo `main`)
  - Saludable y limpio
  - **Recomendación:** Mantener este modelo simple o considerar feature branches para cambios grandes

#### Environments y configuración
- **Archivos `.env`:**
  - `~/proyectos/invoice-extractor/.env` (configuración principal)
  - `~/proyectos/invoice-extractor/frontend/.env` (frontend)
  - `~/proyectos/invoice-extractor/frontend/.env.production` (producción)
  - `~/proyectos/invoice-extractor/.env.example` (template)
- **Variables críticas:**
  - `DATABASE_URL` (PostgreSQL con credenciales)
  - OpenAI API key
  - Google Drive credentials (en `creds/` o `.env`)
- **Riesgos potenciales:**
  - Credenciales de base de datos en texto plano en `.env`
  - API keys expuestas
- **Recomendaciones:**
  - Usar gestor de secretos
  - Rotar credenciales periódicamente
  - Verificar permisos de archivos `.env` (`chmod 600`)

#### Mantenimiento y tareas sugeridas
- Limpieza periódica de facturas procesadas en `data/`
- Rotación de logs en `logs/`
- Backup de base de datos `negocio_db`
- Actualización de dependencias (FastAPI, React, OpenAI SDK)
- Revisión de costos de OpenAI API (monitoreo de uso)
- Verificación de sincronización con Google Drive
- **Frontend:** Rebuild con `docker build --no-cache` después de cambios (ver `docs/FRONTEND_DEPLOYMENT_GUIDE.md`)
- **Configuración crítica:** No cambiar `base: '/invoice-dashboard/'` en `vite.config.js` sin actualizar Traefik

---

### 3.4 Bresca Reportes Drive Dashboard

#### Información general
- **Nombre funcional:** Bresca Reportes - Sincronización y Dashboard de Google Drive
- **Ruta interna:** `~/proyectos/bresca-reportes-drive-dash`
- **URL externa:** Por completar: URL externa (probablemente vía proxy en puerto 8501)
- **Estado:** Activo

#### Stack tecnológico
- **Backend:**
  - Python 3.10+
  - Streamlit 1.50.0
  - Google Drive API v3 (`google-api-python-client`)
  - DuckDB (almacén de datos)
  - Pandas (procesamiento de datos)
  - OpenPyXL (lectura de Excel)
- **Procesamiento:**
  - Sincronización automática desde Google Drive
  - Normalización de Excel con alias en `config.yaml`

#### Componentes y arquitectura
- **Sincronización (`sync_drive.py`):**
  - Polling cada 10 minutos a Google Drive (Folder ID)
  - Descarga solo si cambió (md5Checksum/modifiedTime)
  - Guarda manifest local para idempotencia
  - Normalización de Excel con alias en `config.yaml`
  - Almacén: DuckDB `data/warehouse.duckdb`
  - Idempotencia: DELETE por `source_file` y re-insert antes de cada carga
- **Dashboard (Streamlit):**
  - UI en `app.py`
  - Cache con TTL 300s
  - Botón "Refrescar" manual
  - Visualización de datos desde DuckDB

#### Ejecución y despliegue
- **Ejecución:** Systemd service (`bresca.streamlit.service`)
- **Comando:** `streamlit run app.py --server.address 127.0.0.1 --server.port 8501`
- **Puerto:** `8501` (solo localhost, no expuesto públicamente)
- **Proxy:** Nginx (configuración sugerida en `DEPLOY_NOTES.md`, no confirmado si está activo)
- **Cron:** Sincronización cada 10 minutos (`*/10 * * * *`)
- **Entorno virtual:** `.venv/` en el directorio del proyecto
- **Variables de entorno:**
  - Google Drive credentials (Service Account en `creds/service_account.json`)
  - Configuración en `config.yaml`

#### Repositorio y ramas Git
- **Ruta local:** `~/proyectos/bresca-reportes-drive-dash`
- **Remoto:** (Por completar: verificar con `git remote -v`)
- **Rama principal:** (Por completar: verificar rama activa)
- **Total de ramas:** (Por completar)
- **Comentarios sobre branching:**
  - Repositorio Git presente pero sin ramas remotas visibles en análisis inicial
  - **Recomendación:** Verificar estado del repositorio y configuración remota

#### Environments y configuración
- **Archivos `.env`:**
  - `~/proyectos/bresca-reportes-drive-dash/.env` (vacío en análisis)
  - `~/proyectos/bresca-reportes-drive-dash/.env.example` (template)
- **Configuración:**
  - `config.yaml`: alias y mapeo de hojas de Excel
  - `creds/service_account.json`: credenciales de Google Drive (fuera de git)
- **Riesgos potenciales:**
  - Service Account JSON con permisos amplios
  - Falta de proxy/HTTPS si está expuesto directamente
- **Recomendaciones:**
  - Verificar que puerto 8501 solo escuche en 127.0.0.1
  - Configurar proxy reverso con HTTPS (Nginx + Let's Encrypt)
  - Rotar credenciales de Service Account periódicamente
  - Backup de `data/warehouse.duckdb`

#### Mantenimiento y tareas sugeridas
- Backup diario de `data/warehouse.duckdb` (política: 7 diarios + 4 semanales)
- Rotación de `sync.log` con logrotate
- Monitoreo de fallos de sincronización (alertas si 3 fallos seguidos)
- Limpieza de archivos raw antiguos en `data/raw` si el volumen crece
- Verificación de permisos de Service Account en Google Drive
- Actualización de dependencias Python

---

### 3.5 Command Center

#### Información general
- **Nombre funcional:** Command Center - Panel de Control y Gestión
- **Ruta interna:** `~/proyectos/infra/command-center`
- **URL externa:**
  - Frontend: `http://82.25.101.32/command-center`
  - Backend API: `http://82.25.101.32/command-center-api`
- **Estado:** Activo

#### Stack tecnológico
- **Backend:**
  - FastAPI
  - Python 3.x
  - Docker SDK (acceso a Docker socket)
- **Frontend:**
  - React + Vite
  - TypeScript
  - TailwindCSS

#### Componentes y arquitectura
- **Backend (FastAPI):**
  - API REST bajo `/api/*`
  - Acceso a Docker socket para gestión de contenedores
  - Lectura de logs del trading bot
  - Gestión de docker-compose del trading bot
- **Frontend (React):**
  - Dashboard de control
  - Visualización de logs
  - Gestión de servicios

#### Ejecución y despliegue
- **Orquestación:** Docker Compose (`docker-compose.yml`)
- **Servicios:**
  - `command-center-backend`: FastAPI en puerto `8001` (expose only)
  - `command-center-frontend`: Nginx sirve build estático en puerto `80` (expose only)
- **Reverse Proxy (Traefik):**
  - Frontend: `Host(82.25.101.32) && PathPrefix(/command-center)` → puerto 80
  - Backend: `Host(82.25.101.32) && PathPrefix(/command-center-api)` → puerto 8001
  - Middleware: strip prefix para ambos
- **Volúmenes:**
  - Docker socket: `/var/run/docker.sock` (acceso a Docker)
  - Trading bot path: montado como read-only
  - Infrastructure: acceso read-only a docker-compose files
- **Variables de entorno:**
  - `TRADING_BOT_PATH`, `LOG_FILE`, `DOCKER_COMPOSE_PATH`, `DOCKER_COMPOSE_DIR`

#### Repositorio y ramas Git
- **Ruta local:** `~/proyectos/infra/command-center`
- **Remoto:** (Por completar: verificar si tiene repositorio Git)
- **Rama principal:** (Por completar)
- **Comentarios sobre branching:**
  - No se detectó repositorio Git en análisis inicial
  - **Recomendación:** Inicializar repositorio Git si no existe, o verificar si está en otro lugar

#### Environments y configuración
- **Archivos `.env`:**
  - `~/proyectos/infra/command-center/.env`
- **Variables críticas:**
  - Rutas a trading bot y archivos de configuración
- **Riesgos potenciales:**
  - Acceso a Docker socket (privilegios elevados)
- **Recomendaciones:**
  - Limitar acceso al backend (autenticación/autorización)
  - Auditar acciones realizadas vía API
  - Considerar usar Docker API con permisos restringidos

#### Mantenimiento y tareas sugeridas
- Revisión de logs de acceso al Docker socket
- Actualización de dependencias
- Verificación de seguridad (autenticación en API)
- Backup de configuraciones

---

### 3.6 Traefik (Reverse Proxy)

#### Información general
- **Nombre funcional:** Traefik - Reverse Proxy y Load Balancer
- **Ruta interna:** `~/proyectos/infra/traefik`
- **URL externa:**
  - Dashboard: `http://82.25.101.32:8080` (o vía `/api`/`/dashboard` en HTTPS)
  - HTTP: `http://82.25.101.32:80`
  - HTTPS: `https://82.25.101.32:443`
- **Estado:** Activo

#### Stack tecnológico
- **Software:** Traefik v2.10
- **Certificados:** Let's Encrypt (ACME TLS Challenge)
- **Providers:** Docker + File

#### Componentes y arquitectura
- **Entry Points:**
  - HTTP: puerto 80 (sin redirect automático a HTTPS, algunas rutas usan HTTP directamente)
  - HTTPS: puerto 443 (con TLS)
  - Dashboard: puerto 8080 (opcional, puede removerse en producción)
- **Providers:**
  - Docker: auto-discovery de servicios con labels `traefik.enable=true`
  - File: configuración estática en `config/` (usado para `invoice-api`)
- **Certificados:**
  - Let's Encrypt con TLS Challenge
  - Storage: `acme.json`
  - Email: `hola@existofestivalessentials.com`

#### Ejecución y despliegue
- **Orquestación:** Docker Compose (`docker-compose.traefik.yml`)
- **Puertos expuestos:**
  - `80:80` (HTTP)
  - `443:443` (HTTPS)
  - `8080:8080` (Dashboard, opcional)
- **Volúmenes:**
  - Docker socket: `/var/run/docker.sock:ro`
  - Configuración: `traefik.yml`, `config/`
  - Certificados: `acme.json`
- **Red:** `traefik-public` (red externa compartida con servicios)

#### Configuración de rutas
Todas las aplicaciones se enrutan a través de Traefik con las siguientes reglas:

| Aplicación | Ruta | Entry Point | Strip Prefix |
|------------|------|-------------|--------------|
| Trading Bot Dashboard | `/bot` | HTTPS | Sí |
| Trading Bot API | `/api/trading` | HTTPS | No |
| Investment Portfolio Frontend | `/Investment-portfolio` | HTTP | No |
| Investment Portfolio API | `/Investment-portfolio-api` | HTTP | Sí |
| Invoice Extractor Frontend | `/invoice-dashboard` | HTTP | Sí |
| Invoice Extractor API | `/invoice-api` | HTTP | Sí |
| Command Center Frontend | `/command-center` | HTTP | No |
| Command Center API | `/command-center-api` | HTTP | Sí |
| Prometheus | `/infra` | HTTPS | Sí |
| Grafana | `/grafana` | HTTPS | No |

#### Mantenimiento y tareas sugeridas
- Rotación de logs de acceso (`/var/log/traefik/access.log`)
- Renovación automática de certificados Let's Encrypt (verificar que funcione)
- Revisión de configuración de seguridad (dashboard accesible públicamente)
- Considerar deshabilitar dashboard en producción o proteger con auth
- Monitoreo de uso de recursos y rate limiting

---

## 4. Infraestructura y red global

### Reverse Proxy (Traefik)
- **Ubicación:** `~/proyectos/infra/traefik`
- **Función:** Reverse proxy único para todas las aplicaciones
- **Red compartida:** `traefik-public` (Docker network externa)
- **Enrutamiento:**
  - Basado en `Host` y `PathPrefix`
  - Algunas rutas usan HTTP, otras HTTPS (según configuración de Let's Encrypt)
  - Let's Encrypt no soporta IPs directamente, por lo que algunas rutas usan HTTP

### Mapa de puertos

| Puerto | Servicio | Acceso | Notas |
|--------|----------|--------|-------|
| 80 | Traefik HTTP | Público | Entry point HTTP |
| 443 | Traefik HTTPS | Público | Entry point HTTPS |
| 8080 | Traefik Dashboard | Público | Considerar proteger o deshabilitar |
| 8000 | Investment Backend | Interno (Docker) | Expuesto vía Traefik |
| 8001 | Command Center Backend | Interno (Docker) | Expuesto vía Traefik |
| 8002 | Invoice Backend | Host | `network_mode: host`, expuesto directamente |
| 8501 | Streamlit Dashboards | Localhost | Trading Bot, Bresca Reportes (systemd) |
| 3000 | Investment Frontend | Interno (Docker) | Expuesto vía Traefik |
| 3000 | Grafana | Interno (Docker) | Expuesto vía Traefik |
| 9090 | Prometheus | Interno (Docker) | Expuesto vía Traefik |
| 5432 | PostgreSQL | Interno (Docker) | No expuesto públicamente |
| 6379 | Redis | Interno (Docker) | No expuesto públicamente |

### Relaciones entre aplicaciones

- **Trading Bot ↔ Investment Dashboard:**
  - Comparten PostgreSQL y Redis (contenedores en `bot-trading/infrastructure/docker-compose.yml`)
  - Investment Dashboard puede leer datos de trading si comparten schema

- **Invoice Extractor:**
  - Base de datos independiente (`negocio_db`)
  - Backend usa `network_mode: host` (diferente del resto)

- **Command Center:**
  - Accede a Docker socket para gestionar servicios
  - Lee logs del Trading Bot
  - Gestiona docker-compose del Trading Bot

- **Bresca Reportes:**
  - Completamente independiente (DuckDB local, systemd service)
  - No comparte infraestructura con otras apps

---

## 5. Repositorios y mantenimiento global

### Resumen de repositorios

| Proyecto | Repositorio Git | Rama Principal | Total Ramas | Estado |
|----------|----------------|----------------|-------------|--------|
| bot-trading | `https://github.com/AlexorAle/bot-trading.git` | `main` | 6 | Activo |
| investment-dashboard | `https://github.com/AlexorAle/Investment-Dashboard.git` | `master` | 10 | Activo |
| invoice-extractor | `https://github.com/AlexorAle/bresca-invoice-extrator.git` | `main` | 2 | Activo |
| bresca-reportes-drive-dash | (Por completar) | (Por completar) | (Por completar) | Activo |
| command-center | (Sin repo detectado) | - | - | Activo |

### Análisis de branching

- **Modelos identificados:**
  - **Trunk-based simple:** `invoice-extractor` (solo `main`)
  - **Feature branches:** `bot-trading`, `investment-dashboard` (trunk + features)
  - **Ramas cursor/codex:** Presencia de ramas generadas por herramientas de IA

- **Problemas detectados:**
  - Múltiples ramas `cursor/*` y `codex/*` sin mergear (posiblemente obsoletas)
  - `investment-dashboard` tiene rama local `backup/migracion` que debería consolidarse
  - Inconsistencia en nombres de rama principal (`main` vs `master`)

- **Recomendaciones:**
  1. **Estandarizar nombre de rama principal:** Elegir `main` o `master` y migrar todos los repos
  2. **Limpieza de ramas:**
     - Revisar y mergear/eliminar ramas `cursor/*` y `codex/*` obsoletas
     - Consolidar `backup/migracion` en `investment-dashboard`
  3. **Estrategia de branching:**
     - Mantener trunk-based para proyectos pequeños (`invoice-extractor`)
     - Usar feature branches para cambios grandes
     - Documentar convenciones de naming
  4. **Tags y releases:**
     - Considerar usar tags de Git para versiones/releases
     - Documentar proceso de release

---

## 6. CI/CD y despliegue

### Estado actual
- **CI/CD:** No se detectaron pipelines de CI/CD automatizados (GitHub Actions, GitLab CI, etc.)
- **Despliegue:** Manual mediante Docker Compose
- **Proceso típico:**
  1. Pull de cambios desde repositorio
  2. Rebuild de imágenes Docker (`docker-compose build`)
  3. Restart de servicios (`docker-compose up -d`)

### Recomendaciones
- **Implementar CI/CD:**
  - GitHub Actions para tests automáticos
  - Pipeline de despliegue automatizado (con aprobación manual para producción)
  - Notificaciones de despliegue (Telegram, email)
- **Versionado:**
  - Tags de Git para releases
  - Versionado semántico
- **Rollback:**
  - Estrategia de rollback documentada
  - Backup de imágenes Docker antes de actualizar

---

## 7. Mantenimiento periódico recomendado

### Tareas diarias
- [ ] Verificar logs de errores en todas las aplicaciones
- [ ] Monitoreo de uso de recursos (CPU, memoria, disco)
- [ ] Verificación de sincronización de Bresca Reportes (cron)

### Tareas semanales
- [ ] Revisión de logs y rotación si es necesario
- [ ] Verificación de backups (PostgreSQL, DuckDB)
- [ ] Revisión de métricas de Prometheus/Grafana
- [ ] Actualización de dependencias menores (patch)

### Tareas mensuales
- [ ] Limpieza de logs antiguos
- [ ] Revisión y archivo de ramas Git obsoletas
- [ ] Actualización de dependencias (minor)
- [ ] Revisión de seguridad (permisos, secretos)
- [ ] Verificación de certificados SSL/TLS
- [ ] Análisis de uso de APIs externas (costos, rate limits)

### Tareas trimestrales
- [ ] Actualización mayor de dependencias (con testing exhaustivo)
- [ ] Revisión de arquitectura y optimizaciones
- [ ] Auditoría de seguridad completa
- [ ] Revisión de estrategias de backup y disaster recovery
- [ ] Documentación de cambios arquitectónicos

### Tareas específicas por aplicación

#### Trading Bot
- Rotación de logs en `logs/`
- Backup de `backups/`
- Revisión de métricas de trading
- Actualización de `ccxt` para soporte de exchanges

#### Investment Dashboard
- Actualización de `public/operaciones.xlsx`
- Limpieza de `backend/app/api_timings.jsonl`
- Monitoreo de rate limits de APIs externas

#### Invoice Extractor
- Limpieza de facturas procesadas en `data/`
- Backup de base de datos `negocio_db`
- Revisión de costos de OpenAI API

#### Bresca Reportes
- Backup de `data/warehouse.duckdb` (diario)
- Rotación de `sync.log`
- Verificación de permisos de Google Drive Service Account

#### Command Center
- Revisión de logs de acceso
- Auditoría de acciones realizadas vía API

#### Traefik
- Rotación de logs de acceso
- Verificación de renovación de certificados Let's Encrypt
- Revisión de configuración de seguridad

---

## 8. Notas y observaciones

### Puntos de atención
1. **Seguridad:**
   - Algunas rutas usan HTTP en lugar de HTTPS (limitación de Let's Encrypt con IPs)
   - Traefik dashboard accesible públicamente (considerar proteger o deshabilitar)
   - Credenciales en archivos `.env` (considerar gestor de secretos)

2. **Infraestructura:**
   - `invoice-backend` usa `network_mode: host` (diferente del resto)
   - Mezcla de servicios en Docker y systemd (Bresca Reportes)

3. **Mantenimiento:**
   - Múltiples ramas Git obsoletas sin limpiar
   - Falta de CI/CD automatizado
   - Proceso de backup no completamente documentado

4. **Escalabilidad:**
   - Algunas aplicaciones comparten base de datos (posible cuello de botella)
   - Falta de estrategia de alta disponibilidad

### Mejoras sugeridas
1. **Unificar infraestructura:**
   - Migrar Bresca Reportes a Docker Compose
   - Considerar migrar `invoice-backend` a red Docker estándar

2. **Seguridad:**
   - Implementar autenticación en APIs públicas
   - Proteger Traefik dashboard
   - Migrar a gestor de secretos (HashiCorp Vault, AWS Secrets Manager)

3. **Observabilidad:**
   - Centralizar logs (ELK, Loki)
   - Alertas automatizadas (Prometheus + Alertmanager)
   - Dashboards unificados en Grafana

4. **CI/CD:**
   - Implementar pipelines automatizados
   - Tests automatizados antes de despliegue
   - Estrategia de blue-green o canary deployments

---

**Fin del documento**


