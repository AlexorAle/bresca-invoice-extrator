# Integración Invoice Extractor con Traefik

## Resumen Ejecutivo

El dashboard de Invoice Extractor ha sido integrado exitosamente con Traefik para acceso externo. El frontend React y el backend FastAPI están ahora accesibles desde `http://82.25.101.32` a través de las rutas:

- **Frontend**: `http://82.25.101.32/invoice-dashboard/`
- **Backend API**: `http://82.25.101.32/invoice-api/`

## Configuración Realizada

### 1. Dockerfiles Creados

#### Frontend (`frontend/Dockerfile`)
- Multi-stage build con Node.js 20 Alpine
- Build de producción con Vite
- Servido con Nginx Alpine
- Configuración de SPA routing para React

#### Backend (`Dockerfile.backend`)
- Python 3.11 slim
- Instalación de dependencias desde `requirements.txt`
- Ejecución con Uvicorn en puerto 8000

### 2. Servicios en docker-compose.yml

#### Invoice Backend
```yaml
invoice-backend:
  build:
    context: ../../invoice-extractor
    dockerfile: Dockerfile.backend
  container_name: invoice-backend
  expose:
    - "8000"
  environment:
    - DATABASE_URL=${INVOICE_DATABASE_URL:-postgresql://trading:${POSTGRES_PASSWORD}@postgres:5432/trading_db}
  networks:
    - traefik-public
  labels:
    - "traefik.http.routers.invoice-backend.rule=Host(`82.25.101.32`) && PathPrefix(`/invoice-api`)"
    - "traefik.http.middlewares.invoice-api-strip.stripprefix.prefixes=/invoice-api"
```

#### Invoice Frontend
```yaml
invoice-frontend:
  build:
    context: ../../invoice-extractor/frontend
    dockerfile: Dockerfile
    args:
      - VITE_API_BASE_URL=/invoice-api/api
  container_name: invoice-frontend
  expose:
    - "80"
  networks:
    - traefik-public
  labels:
    - "traefik.http.routers.invoice-frontend.rule=Host(`82.25.101.32`) && PathPrefix(`/invoice-dashboard`)"
    - "traefik.http.middlewares.invoice-strip.stripprefix.prefixes=/invoice-dashboard"
```

### 3. Cambios en el Código

#### Backend (`src/api/main.py`)
- CORS actualizado para permitir acceso desde `http://82.25.101.32` y `https://82.25.101.32`

#### Frontend (`frontend/vite.config.js`)
- Base path removido (manejado por Traefik stripPrefix)
- Configuración de build optimizada

#### Frontend (`frontend/src/utils/api.js`)
- API URL configurada mediante variable de entorno `VITE_API_BASE_URL`
- Durante build, se establece como `/invoice-api/api` (ruta relativa)

### 4. Rutas Traefik

| Servicio | Ruta Externa | Ruta Interna | Middleware |
|----------|--------------|---------------|------------|
| Frontend | `/invoice-dashboard` | `/` | `invoice-strip` (stripPrefix) |
| Backend | `/invoice-api` | `/` | `invoice-api-strip` (stripPrefix) |

## Despliegue

### Comandos de Despliegue

```bash
# Desde /home/alex/proyectos/bot-trading/infrastructure
cd /home/alex/proyectos/bot-trading/infrastructure

# Construir servicios
docker-compose build invoice-frontend invoice-backend

# Levantar servicios
docker-compose up -d invoice-frontend invoice-backend

# Ver logs
docker-compose logs -f invoice-frontend invoice-backend

# Verificar estado
docker-compose ps invoice-frontend invoice-backend
```

### Verificación

```bash
# Frontend
curl http://82.25.101.32/invoice-dashboard/
# Esperado: HTML 200 OK

# Backend Health
curl http://82.25.101.32/invoice-api/healthz
# Esperado: {"status":"ok"}

# Backend API
curl http://82.25.101.32/invoice-api/api/system/sync-status
# Esperado: JSON response o error de BD (si no está configurada)
```

## Configuración de Base de Datos

El backend requiere una conexión a PostgreSQL. Por defecto, intenta conectar a:
- Host: `postgres` (nombre del servicio Docker)
- Database: `trading_db`
- User: `trading`
- Password: `${POSTGRES_PASSWORD}`

Para usar una base de datos diferente, establecer la variable de entorno:
```bash
INVOICE_DATABASE_URL=postgresql://user:password@host:5432/database
```

## Troubleshooting

### Frontend no carga
1. Verificar que Traefik está corriendo: `docker ps | grep traefik`
2. Verificar logs del frontend: `docker logs invoice-frontend`
3. Verificar que los assets se están sirviendo: `curl http://82.25.101.32/invoice-dashboard/assets/index*.js`

### Backend no responde
1. Verificar logs: `docker logs invoice-backend`
2. Verificar conexión a BD: `docker exec invoice-backend python -c "from src.db.database import get_database; print(get_database())"`
3. Verificar health check: `curl http://82.25.101.32/invoice-api/healthz`

### Errores CORS
- Verificar que el backend tiene configurado CORS para `http://82.25.101.32`
- Verificar en `src/api/main.py` que `cors_origins` incluye el dominio correcto

### Assets no cargan (404)
- Verificar que Vite build se ejecutó correctamente
- Verificar que los assets están en `/usr/share/nginx/html/assets/` dentro del contenedor
- Verificar configuración de nginx en el Dockerfile

## Estado Actual

✅ **Frontend**: Accesible en `http://82.25.101.32/invoice-dashboard/`
✅ **Backend Health**: Funcional en `http://82.25.101.32/invoice-api/healthz`
⚠️ **Backend API**: Funcional pero requiere configuración de base de datos

## Próximos Pasos

1. **Configurar Base de Datos**: Asegurar que PostgreSQL está configurado y accesible
2. **Variables de Entorno**: Configurar `.env` con las credenciales correctas
3. **SSL/TLS**: Configurar HTTPS cuando se tenga un dominio (Let's Encrypt no soporta IPs)
4. **Monitoreo**: Agregar health checks más detallados
5. **Logs**: Configurar logging estructurado para debugging

---

**Fecha de Integración**: 2025-11-05
**Última Actualización**: 2025-11-05

