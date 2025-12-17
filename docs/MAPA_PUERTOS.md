# Mapa de Puertos - Infraestructura Traefik

**Última actualización**: 2025-12-11  
**Dominio principal**: alexforge.online  
**IP del servidor**: 82.25.101.32

## 🌐 Puertos Públicos

| Puerto | Servicio | Protocolo | Acceso |
|--------|----------|-----------|--------|
| 80 | Traefik (HTTP) | HTTP | Redirige a HTTPS |
| 443 | Traefik (HTTPS) | HTTPS | Entrada principal |
| 8080 | Traefik Dashboard | HTTP | Solo desarrollo (opcional) |

## 🔒 Puertos Internos (Docker Network)

Los siguientes puertos están **solo accesibles dentro de la red Docker** `traefik-public`:

| Servicio | Puerto Interno | Ruta Externa | Descripción |
|----------|----------------|--------------|-------------|
| Investment Frontend | 3000 | `/Investment-portfolio` | Next.js Dashboard |
| Investment Backend | 8000 | `/Investment-portfolio-api` | FastAPI Backend |
| Trading Bot Dashboard | 8501 | `/bot` | Streamlit Dashboard |
| Trading Bot Metrics | 8080 | `/api/trading` | Prometheus Metrics API |
| Command Center Frontend | 80 | `/command-center` | React Dashboard |
| Command Center Backend | 8001 | `/command-center-api` | FastAPI Backend |
| Invoice Extractor Frontend | 80 | `/invoice-dashboard` | React Dashboard |
| Invoice Extractor Backend | 8002 | `/invoice-api` | FastAPI Backend (host mode) |
| Prometheus | 9090 | `/infra` | Monitoring |
| Grafana | 3000 | `/grafana` | Visualization (integración Loki) |
| Loki | 3100 | - | Log Aggregation (solo interno) |
| Promtail | 9080 | - | Log Shipper (solo interno) |
| Redis | 6379 | - | Cache (interno) |
| PostgreSQL | 5432 | - | Database (interno) |

## 📍 URLs de Acceso

### Servicios Principales

| Servicio | URL HTTPS | URL HTTP (fallback) | Descripción |
|----------|-----------|---------------------|-------------|
| Investment Dashboard | `https://alexforge.online/Investment-portfolio` | `http://82.25.101.32/Investment-portfolio` | Frontend principal |
| Investment API Docs | `https://alexforge.online/Investment-portfolio-api/docs` | `http://82.25.101.32/Investment-portfolio-api/docs` | Swagger UI |
| Trading Bot Dashboard | `https://alexforge.online/bot` | `http://82.25.101.32/bot` | Streamlit UI |
| Trading Bot API | `https://alexforge.online/api/trading` | `http://82.25.101.32/api/trading` | Metrics endpoint |
| Command Center | `https://alexforge.online/command-center` | `http://82.25.101.32/command-center` | Dashboard principal |
| Command Center API | `https://alexforge.online/command-center-api` | `http://82.25.101.32/command-center-api` | API Backend |
| Invoice Dashboard | `https://alexforge.online/invoice-dashboard` | `http://82.25.101.32/invoice-dashboard` | Frontend Invoice |
| Invoice API | `https://alexforge.online/invoice-api` | `http://82.25.101.32/invoice-api` | API Backend |
| Prometheus | `https://82.25.101.32/infra` | - | Monitoring UI |
| Grafana | `https://82.25.101.32/grafana` | - | Dashboards (con Loki) |

### Servicios de Infraestructura

| Servicio | URL | Acceso |
|----------|-----|--------|
| Traefik Dashboard | `http://82.25.101.32:8080/dashboard/` | Desarrollo (opcional) |

## 🔐 Seguridad

### Puertos Expuestos

- ✅ **Solo 80 y 443** están expuestos al exterior
- ✅ Todos los servicios internos usan `expose` (no `ports`)
- ✅ SSL/TLS automático con Let's Encrypt para dominio `alexforge.online`
- ✅ Redirección HTTP → HTTPS automática habilitada
- ✅ Dominio principal: `alexforge.online` (certificados Let's Encrypt)
- ✅ IP estática: `82.25.101.32` (usada como fallback)

### Firewall (UFW)

```bash
# Verificar configuración
sudo ufw status

# Puertos abiertos (esperados)
80/tcp   (HTTP)
443/tcp  (HTTPS)
```

## 🚀 Agregar Nuevo Servicio

Para agregar un nuevo servicio, ver: `/home/alex/proyectos/infra/traefik/TRAEFIK_USAGE_GUIDE.md`

### Ejemplo: Nuevo servicio en puerto 3002

```yaml
services:
  new-service:
    expose:
      - "3002"  # Solo interno
    networks:
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.new-service.rule=Host(`alexforge.online`) && PathPrefix(`/new-service`)"
      - "traefik.http.routers.new-service-https.rule=Host(`alexforge.online`) && PathPrefix(`/new-service`)"
      - "traefik.http.routers.new-service-https.entrypoints=https"
      - "traefik.http.routers.new-service-https.tls=true"
      - "traefik.http.routers.new-service.entrypoints=https"
      - "traefik.http.routers.new-service.tls.certresolver=letsencrypt"
      - "traefik.http.services.new-service.loadbalancer.server.port=3002"
```

## 📊 Migración de Nginx

### Antes (Nginx)

| Ruta | Puerto Interno | Puerto Externo |
|------|----------------|----------------|
| `/api/trading/` | 8080 | 80/443 |
| `/dashboard/` | 8501 | 80/443 |
| `/api/investment/` | 8000 | 80/443 |
| `/investment/` | 3000 | 80/443 |
| `/metrics/` | 9090 | 80/443 |
| `/grafana/` | 3000 | 80/443 |

### Después (Traefik)

| Ruta | Puerto Interno | Puerto Externo |
|------|----------------|----------------|
| `/api/trading` | 8080 | 443 |
| `/bot` | 8501 | 443 |
| `/investment-api` | 8000 | 443 |
| `/investment` | 3000 | 443 |
| `/infra` | 9090 | 443 |
| `/grafana` | 3000 | 443 |

**Cambios principales**:
- ✅ Rutas simplificadas (sin trailing slashes)
- ✅ SSL/TLS automático
- ✅ Sin puertos expuestos directamente

## 🔍 Verificación

```bash
# Ver todos los servicios en red
docker network inspect traefik-public

# Ver puertos en uso
sudo ss -tuln | grep -E ":(80|443) "

# Verificar servicios activos
docker-compose ps
```

---

**Nota**: Este mapa refleja el estado post-migración a Traefik. Para el estado anterior (Nginx), ver backups en `/home/alex/backups/migration-*`.

