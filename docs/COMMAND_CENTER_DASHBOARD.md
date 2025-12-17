# Command Center - Dashboard y Funcionalidades

**Fecha:** 2025-12-03  
**Ubicación:** `~/proyectos/infra/command-center`  
**Estado:** Activo

---

## 📋 Resumen Ejecutivo

Command Center es el panel de control centralizado para gestionar y monitorear todas las aplicaciones del servidor. Incluye dos interfaces: un dashboard React moderno y un dashboard Streamlit alternativo.

---

## 🎯 Componentes

### 1. Frontend React
- **Ubicación:** `frontend/`
- **Stack:** React + Vite + TypeScript + TailwindCSS
- **URL:** `https://alexforge.online/command-center`
- **Funcionalidades:**
  - Dashboard principal con métricas de servicios
  - Monitor de logs unificado con filtros avanzados
  - Integración con Grafana/Loki para visualización de logs
  - Gestión de servicios Docker
  - Visualización de estado de contenedores

### 2. Backend FastAPI
- **Ubicación:** `backend/`
- **Stack:** FastAPI + Python
- **URL:** `https://alexforge.online/command-center-api`
- **Puerto:** 8001
- **Funcionalidades:**
  - API REST para gestión de servicios
  - Lectura de logs desde Docker y archivos
  - Integración con Loki para consulta de logs
  - Gestión de docker-compose del trading bot
  - Endpoints de salud y métricas

### 3. Dashboard Streamlit (Alternativo)
- **Ubicación:** `streamlit_dashboard_modern.py`
- **Stack:** Streamlit
- **Estado:** Disponible (acceso interno)
- **Funcionalidades:**
  - Visualización de métricas del servidor
  - Monitoreo de servicios
  - Dashboard alternativo con diseño moderno

---

## 🔧 Funcionalidades Principales

### Monitor de Logs Unificado

**Endpoint:** `/api/logs/{app_id}`

**Características:**
- Filtrado por aplicación (trading-bot, invoice-extractor, investment-dashboard)
- Filtrado por componente (backend, frontend, db, bot)
- Filtrado por nivel (INFO, WARN, ERROR, DEBUG)
- Búsqueda de texto en logs
- Filtrado por rango de tiempo
- Orden ascendente/descendente
- Modo tail (streaming en tiempo real)
- Integración con Grafana/Loki para consultas avanzadas

**Ejemplo de uso:**
```bash
# Obtener últimos 20 logs del trading bot
curl https://alexforge.online/command-center-api/api/logs/trading-bot?lines=20

# Filtrar solo errores
curl https://alexforge.online/command-center-api/api/logs/trading-bot?level=ERROR

# Buscar texto específico
curl https://alexforge.online/command-center-api/api/logs/trading-bot?q=startup
```

### Gestión de Servicios

- Ver estado de contenedores Docker
- Iniciar/detener servicios
- Ver logs en tiempo real
- Gestionar docker-compose del trading bot

### Integración con Grafana/Loki

- Botón "Abrir Grafana" en monitor de logs
- Genera URLs pre-configuradas con filtros aplicados
- Consultas LogQL automáticas basadas en filtros seleccionados

---

## 🌐 URLs de Acceso

| Componente | URL HTTPS | URL HTTP (fallback) |
|------------|-----------|---------------------|
| Frontend | `https://alexforge.online/command-center` | `http://82.25.101.32/command-center` |
| Backend API | `https://alexforge.online/command-center-api` | `http://82.25.101.32/command-center-api` |
| Health Check | `https://alexforge.online/command-center-api/healthz` | `http://82.25.101.32/command-center-api/healthz` |

---

## 🔐 Configuración Traefik

### Frontend
- **Router HTTP:** `Host(alexforge.online) && PathPrefix(/command-center)`
- **Router HTTPS:** `Host(alexforge.online) && PathPrefix(/command-center)` con TLS
- **Middleware:** Strip prefix `/command-center`
- **Puerto interno:** 80

### Backend
- **Router HTTP:** `Host(alexforge.online) && PathPrefix(/command-center-api)`
- **Router HTTPS:** `Host(alexforge.online) && PathPrefix(/command-center-api)` con TLS
- **Middleware:** Strip prefix `/command-center-api`
- **Puerto interno:** 8001

---

## 📊 Variables de Entorno

```bash
# Backend
TRADING_BOT_PATH=/home/alex/proyectos/bot-trading
LOG_FILE=/home/alex/proyectos/bot-trading/backtrader_engine/logs/paper_trading.log
DOCKER_COMPOSE_PATH=/home/alex/proyectos/bot-trading/infrastructure/docker-compose.traefik.yml
DOCKER_COMPOSE_DIR=/home/alex/proyectos/bot-trading/infrastructure
BASE_DOMAIN=alexforge.online

# Frontend
VITE_API_BASE_URL=/command-center-api/api
VITE_BASE_DOMAIN=alexforge.online
VITE_USE_HTTPS=true
```

---

## 🚀 Despliegue

```bash
cd ~/proyectos/infra/command-center
docker-compose up -d
```

---

## 🔍 Monitoreo

### Health Checks

```bash
# Backend
curl https://alexforge.online/command-center-api/healthz

# Verificar contenedores
docker ps | grep command-center
```

### Logs

```bash
# Logs del backend
docker logs command-center-backend --tail 50

# Logs del frontend
docker logs command-center-frontend --tail 50
```

---

## 📝 Notas Técnicas

- **Red Docker:** `traefik-public` (compartida con otros servicios)
- **Acceso a Docker Socket:** Backend tiene acceso para gestionar contenedores
- **Logs:** Integración con sistema de logs centralizado (Loki/Promtail)
- **Seguridad:** Acceso a Docker socket requiere permisos adecuados

---

**Fin del documento**

