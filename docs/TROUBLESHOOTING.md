# Troubleshooting Invoice Dashboard

## Problema: "El link no funciona"

### Diagnóstico

El flujo es:
1. **Frontend (React)** → Se carga desde `/invoice-dashboard/`
2. **Frontend** → Hace llamadas API al **Backend** en `/invoice-api/api/...`
3. **Backend (FastAPI)** → Consulta la **Base de Datos** PostgreSQL
4. **Backend** → Devuelve datos JSON al Frontend
5. **Frontend** → Renderiza los datos en el dashboard

### Verificación Rápida

```bash
# 1. Verificar que el frontend carga
curl http://82.25.101.32/invoice-dashboard/
# Debe devolver HTML 200 OK

# 2. Verificar que los assets cargan
curl http://82.25.101.32/invoice-dashboard/assets/index*.js
# Debe devolver JavaScript 200 OK

# 3. Verificar que el backend responde
curl http://82.25.101.32/invoice-api/healthz
# Debe devolver: {"status":"ok"}

# 4. Verificar que la API funciona (puede fallar por BD)
curl http://82.25.101.32/invoice-api/api/system/sync-status
# Si hay BD: JSON con datos
# Si no hay BD: Error de conexión (esperado)
```

### Problemas Comunes

#### 1. Frontend muestra página en blanco

**Síntomas**: El HTML carga pero no se ve nada

**Causas posibles**:
- Los assets JavaScript no cargan (404)
- Errores de JavaScript en la consola del navegador
- La API no responde

**Solución**:
```bash
# Verificar assets
curl -I http://82.25.101.32/invoice-dashboard/assets/index*.js

# Ver logs del frontend
docker logs invoice-frontend

# Ver logs del backend
docker logs invoice-backend
```

#### 2. Error "Failed to fetch" o "Network Error"

**Síntomas**: El frontend carga pero no muestra datos, consola muestra errores de red

**Causas posibles**:
- El backend no está corriendo
- CORS no configurado correctamente
- La URL de la API es incorrecta

**Solución**:
```bash
# Verificar que el backend está corriendo
docker ps | grep invoice-backend

# Verificar health check
curl http://82.25.101.32/invoice-api/healthz

# Verificar CORS en el backend
docker exec invoice-backend cat /app/src/api/main.py | grep -A 5 "cors_origins"
```

#### 3. Error de Base de Datos

**Síntomas**: El frontend carga pero muestra "Error de Conexión" o datos vacíos

**Causas posibles**:
- PostgreSQL no está corriendo
- La conexión a la BD no está configurada
- Las credenciales de BD son incorrectas

**Solución**:
```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep postgres

# Verificar la variable de entorno
docker exec invoice-backend env | grep DATABASE_URL

# Probar conexión manual
docker exec invoice-backend python -c "from src.db.database import get_database; print(get_database())"
```

#### 4. Assets no cargan (404)

**Síntomas**: El HTML carga pero los archivos JS/CSS dan 404

**Causas posibles**:
- Vite base path no configurado correctamente
- Nginx no configurado para servir desde el path correcto

**Solución**:
```bash
# Verificar que Vite tiene base path
cat invoice-extractor/frontend/vite.config.js | grep base

# Verificar configuración de nginx
docker exec invoice-frontend cat /etc/nginx/conf.d/default.conf

# Reconstruir el frontend
cd bot-trading/infrastructure
docker-compose build invoice-frontend
docker-compose up -d --force-recreate invoice-frontend
```

### Configuración de Base de Datos

El backend **SÍ necesita PostgreSQL** para funcionar completamente. El health check funciona sin BD, pero los endpoints de datos requieren BD.

**Para configurar la BD**:

1. Verificar que PostgreSQL está corriendo:
```bash
docker ps | grep postgres
```

2. Configurar la URL de conexión en `docker-compose.yml`:
```yaml
invoice-backend:
  environment:
    - DATABASE_URL=postgresql://trading:${POSTGRES_PASSWORD}@postgres:5432/trading_db
```

O usar una BD externa:
```yaml
invoice-backend:
  environment:
    - DATABASE_URL=postgresql://user:password@host:5432/database
```

3. Verificar que las tablas existen:
```bash
# Verificar schema
docker exec postgres psql -U trading -d trading_db -c "\dt"
```

### Verificación Completa

Para verificar que todo funciona:

```bash
# 1. Contenedores corriendo
docker ps | grep invoice

# 2. Frontend accesible
curl -I http://82.25.101.32/invoice-dashboard/

# 3. Assets cargando
curl -I http://82.25.101.32/invoice-dashboard/assets/index*.js

# 4. Backend saludable
curl http://82.25.101.32/invoice-api/healthz

# 5. API respondiendo (puede fallar sin BD)
curl http://82.25.101.32/invoice-api/api/system/sync-status
```

### Estado Actual

✅ **Frontend**: Cargando correctamente con assets
✅ **Backend**: Saludable y respondiendo
⚠️ **Backend API**: Requiere PostgreSQL para datos completos

---

**Última actualización**: 2025-11-05

