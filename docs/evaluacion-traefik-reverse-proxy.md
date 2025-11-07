# Evaluación: Usar Traefik como Reverse Proxy para Invoice Extractor

**Fecha:** 6 de noviembre de 2025  
**Contexto:** Usuario migró de Nginx a Traefik y quiere evaluar su uso para el sistema de facturas

---

## 🔍 Investigación de Configuración Actual

### Estado Actual

- ✅ **Traefik está instalado** (usuario confirmó migración)
- ✅ **Frontend accesible** en `http://82.25.101.32/invoice-dashboard/`
- ✅ **API corriendo** en `localhost:8001`
- ⚠️ **API no accesible desde fuera** (necesita reverse proxy)

---

## 🎯 Ventajas de Traefik vs Nginx

### Traefik

✅ **Ventajas:**
- **Auto-discovery**: Detecta servicios automáticamente (Docker, Kubernetes)
- **Labels dinámicos**: Configuración mediante labels en contenedores
- **Let's Encrypt automático**: Renovación automática de certificados SSL
- **Dashboard integrado**: Interfaz web para monitoreo
- **Hot reload**: Cambios sin reiniciar
- **Múltiples backends**: Fácil balanceo de carga
- **Ya está instalado**: No necesitas instalar Nginx

❌ **Desventajas:**
- Curva de aprendizaje más pronunciada
- Configuración diferente a Nginx tradicional
- Requiere entender labels y routers

### Nginx

✅ **Ventajas:**
- Más conocido y documentado
- Configuración tradicional (archivos de texto)
- Más ligero para casos simples

❌ **Desventajas:**
- Configuración manual
- Renovación SSL manual (o con certbot)
- Necesitas instalarlo si no está

---

## 🏗️ Arquitectura con Traefik

### Opción 1: Traefik con Docker (Recomendado)

Si el API está en Docker:

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    image: invoice-extractor-api:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`82.25.101.32`) && PathPrefix(`/api`)"
      - "traefik.http.routers.api.entrypoints=web"
      - "traefik.http.services.api.loadbalancer.server.port=8001"
      - "traefik.http.routers.api.middlewares=api-stripprefix"
      - "traefik.http.middlewares.api-stripprefix.stripprefix.prefixes=/api"
    
  frontend:
    image: nginx:alpine
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`82.25.101.32`) && PathPrefix(`/invoice-dashboard`)"
      - "traefik.http.routers.frontend.entrypoints=web"
      - "traefik.http.services.frontend.loadbalancer.server.port=80"
```

### Opción 2: Traefik con File Provider (Sin Docker)

Si el API NO está en Docker:

```yaml
# traefik.yml o configuración dinámica
http:
  routers:
    api:
      rule: "Host(`82.25.101.32`) && PathPrefix(`/api`)"
      service: api-service
      entryPoints:
        - web
      middlewares:
        - api-stripprefix
    
    frontend:
      rule: "Host(`82.25.101.32`) && PathPrefix(`/invoice-dashboard`)"
      service: frontend-service
      entryPoints:
        - web

  services:
    api-service:
      loadBalancer:
        servers:
          - url: "http://localhost:8001"
    
    frontend-service:
      loadBalancer:
        servers:
          - url: "http://localhost:8080"  # O donde esté el frontend

  middlewares:
    api-stripprefix:
      stripPrefix:
        prefixes:
          - "/api"
```

### Opción 3: Traefik con Systemd Service (API como proceso)

Si el API corre como proceso (no Docker):

```yaml
# Configuración en Traefik para servicios externos
http:
  routers:
    invoice-api:
      rule: "Host(`82.25.101.32`) && PathPrefix(`/api`)"
      service: invoice-api-service
      entryPoints:
        - web
      middlewares:
        - strip-api-prefix

  services:
    invoice-api-service:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8001"

  middlewares:
    strip-api-prefix:
      stripPrefix:
        prefixes:
          - "/api"
```

---

## 📋 Configuración Recomendada

### Para tu caso (API como proceso, Frontend estático)

**Estructura sugerida:**

```
Traefik (Puerto 80/443)
├── /invoice-dashboard → Frontend estático (servido por Nginx o Traefik)
└── /api → Reverse proxy → localhost:8001 (FastAPI)
```

**Configuración Traefik:**

```yaml
# traefik.yml o configuración dinámica
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  file:
    filename: /etc/traefik/dynamic/invoice-extractor.yml
    watch: true

# /etc/traefik/dynamic/invoice-extractor.yml
http:
  routers:
    # Frontend estático
    invoice-frontend:
      rule: "Host(`82.25.101.32`) && PathPrefix(`/invoice-dashboard`)"
      service: invoice-frontend-service
      entryPoints:
        - web
    
    # API
    invoice-api:
      rule: "Host(`82.25.101.32`) && PathPrefix(`/api`)"
      service: invoice-api-service
      entryPoints:
        - web
      middlewares:
        - strip-api-prefix

  services:
    invoice-frontend-service:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8080"  # Nginx sirviendo frontend estático
    
    invoice-api-service:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8001"  # FastAPI

  middlewares:
    strip-api-prefix:
      stripPrefix:
        prefixes:
          - "/api"
```

---

## 🔄 Comparación: Traefik vs Nginx

| Característica | Traefik | Nginx |
|----------------|---------|-------|
| Configuración | Labels/YAML | Archivos de texto |
| Auto-discovery | ✅ Sí | ❌ No |
| SSL automático | ✅ Sí (Let's Encrypt) | ⚠️ Con certbot |
| Hot reload | ✅ Sí | ⚠️ Con reload |
| Dashboard | ✅ Sí | ❌ No |
| Curva aprendizaje | ⚠️ Media | ✅ Baja |
| Ya instalado | ✅ Sí (tu caso) | ❌ No |

---

## ✅ Recomendación

### Usar Traefik es la mejor opción porque:

1. ✅ **Ya lo tienes instalado** - No necesitas instalar Nginx
2. ✅ **Let's Encrypt automático** - Certificados SSL sin intervención
3. ✅ **Hot reload** - Cambios sin reiniciar
4. ✅ **Dashboard** - Monitoreo visual
5. ✅ **Consistencia** - Todo en Traefik (no mezclar con Nginx)

### Configuración sugerida:

1. **Frontend estático**: Servido por Nginx en puerto 8080 (interno)
   - Traefik hace reverse proxy a `localhost:8080` para `/invoice-dashboard`

2. **API FastAPI**: Corriendo en puerto 8001
   - Traefik hace reverse proxy a `localhost:8001` para `/api`
   - Middleware para quitar el prefijo `/api`

3. **SSL**: Traefik maneja Let's Encrypt automáticamente

---

## 🎯 Pasos para Implementar (Sin aplicar cambios)

1. **Identificar configuración actual de Traefik**
   - Ubicación de archivos de configuración
   - Cómo está configurado actualmente

2. **Configurar router para API**
   - Regla: `Host(82.25.101.32) && PathPrefix(/api)`
   - Service: `http://localhost:8001`
   - Middleware: Strip prefix `/api`

3. **Configurar router para Frontend** (si no existe)
   - Regla: `Host(82.25.101.32) && PathPrefix(/invoice-dashboard)`
   - Service: `http://localhost:8080` (o donde esté el frontend)

4. **Verificar SSL**
   - Traefik puede manejar Let's Encrypt automáticamente
   - Configurar certificificados si es necesario

---

## ⚠️ Consideraciones

1. **No romper configuración existente**
   - Revisar configuración actual de Traefik
   - Agregar nuevas rutas sin modificar las existentes

2. **Testing**
   - Probar en entorno de desarrollo primero
   - Verificar que las rutas existentes siguen funcionando

3. **Backup**
   - Hacer backup de configuración actual antes de cambios

---

## 📝 Próximos Pasos

1. **Investigar configuración actual de Traefik**
   - Ubicación de archivos
   - Estructura actual
   - Servicios ya configurados

2. **Proponer configuración específica**
   - Basada en tu setup actual
   - Sin romper nada existente

3. **Implementar gradualmente**
   - Primero API
   - Luego verificar frontend
   - Testing completo

---

**Estado:** 🔍 Evaluación completada - Traefik es viable y recomendado

**Siguiente paso:** Investigar configuración actual de Traefik para proponer cambios específicos

