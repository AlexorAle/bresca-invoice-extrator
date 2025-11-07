# Propuesta: Configurar Invoice Extractor en Traefik

**Fecha:** 6 de noviembre de 2025  
**Contexto:** Traefik ya está instalado y funcionando. Necesitamos agregar el API sin romper configuración existente.

---

## 🔍 Configuración Actual de Traefik

### Hallazgos

- ✅ **Traefik corriendo** en Docker (traefik:v2.10)
- ✅ **File provider** configurado en `/config/` (montado desde `./config/`)
- ✅ **Docker provider** activo (auto-discovery)
- ✅ **Frontend funcionando** en `http://82.25.101.32/invoice-dashboard/`
- ❌ **API no configurado** (devuelve 404)

### Estructura Actual

```
/home/alex/proyectos/infra/traefik/
├── docker-compose.traefik.yml
├── traefik.yml
├── config/
│   └── no-redirect.yml
└── acme.json
```

**Volúmenes montados:**
- `./traefik.yml:/traefik.yml:ro` - Configuración principal
- `./config/:/config/:ro` - Configuraciones dinámicas (file provider)
- `/var/run/docker.sock:/var/run/docker.sock:ro` - Docker provider

---

## 🎯 Propuesta: Agregar API sin Romper Nada

### Opción 1: File Provider (Recomendado - No requiere Docker)

**Ventajas:**
- ✅ No requiere que el API esté en Docker
- ✅ Funciona con el API corriendo como proceso (systemd)
- ✅ Configuración en archivo YAML (fácil de mantener)
- ✅ Hot reload automático (Traefik detecta cambios)

**Archivo a crear:** `/home/alex/proyectos/infra/traefik/config/invoice-api.yml`

```yaml
http:
  routers:
    invoice-api:
      rule: "Host(`82.25.101.32`) && PathPrefix(`/api`)"
      service: invoice-api-service
      entryPoints:
        - http
        - https
      middlewares:
        - invoice-api-stripprefix
      # SSL opcional (si quieres forzar HTTPS)
      # tls:
      #   certResolver: letsencrypt

  services:
    invoice-api-service:
      loadBalancer:
        servers:
          - url: "http://host.docker.internal:8001"
        # O si el API está en la misma máquina:
        # - url: "http://172.17.0.1:8001"  # IP del host desde Docker
        # O usar network_mode: host en docker-compose

  middlewares:
    invoice-api-stripprefix:
      stripPrefix:
        prefixes:
          - "/api"
```

**Problema:** `host.docker.internal` puede no funcionar en Linux. Alternativas:

### Opción 1.1: Usar IP del host desde Docker

```yaml
http:
  services:
    invoice-api-service:
      loadBalancer:
        servers:
          - url: "http://172.17.0.1:8001"  # IP por defecto de Docker bridge
```

**Para encontrar la IP correcta:**
```bash
docker network inspect bridge | grep Gateway
```

### Opción 1.2: Usar network_mode: host (Más simple)

Modificar `docker-compose.traefik.yml` para agregar:
```yaml
services:
  traefik:
    network_mode: host  # Acceso directo a localhost
```

Luego en la configuración:
```yaml
http:
  services:
    invoice-api-service:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:8001"  # localhost funciona
```

---

### Opción 2: Docker Provider (Si el API está en Docker)

Si decides poner el API en Docker:

```yaml
# En docker-compose del API
services:
  invoice-api:
    # ... configuración del API ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.invoice-api.rule=Host(`82.25.101.32`) && PathPrefix(`/api`)"
      - "traefik.http.routers.invoice-api.entrypoints=http,https"
      - "traefik.http.routers.invoice-api.service=invoice-api-service"
      - "traefik.http.routers.invoice-api.middlewares=invoice-api-stripprefix"
      - "traefik.http.services.invoice-api-service.loadbalancer.server.port=8001"
      - "traefik.http.middlewares.invoice-api-stripprefix.stripprefix.prefixes=/api"
    networks:
      - traefik-public
```

---

## 📋 Recomendación Final

### Usar Opción 1.2 (File Provider + network_mode: host)

**Razones:**
1. ✅ No requiere poner el API en Docker
2. ✅ Funciona con el API como proceso (systemd)
3. ✅ Configuración simple (un archivo YAML)
4. ✅ Hot reload automático
5. ✅ No rompe configuración existente

### Pasos (Sin aplicar cambios):

1. **Verificar IP del host desde Docker:**
   ```bash
   docker network inspect bridge | grep Gateway
   ```

2. **Crear archivo de configuración:**
   ```bash
   # /home/alex/proyectos/infra/traefik/config/invoice-api.yml
   ```

3. **O usar network_mode: host** (más simple):
   - Modificar `docker-compose.traefik.yml`
   - Agregar `network_mode: host`
   - Usar `http://127.0.0.1:8001` en la configuración

4. **Verificar que no rompe nada:**
   - Probar rutas existentes
   - Verificar que el frontend sigue funcionando
   - Probar el nuevo endpoint `/api`

---

## 🔒 Consideraciones de Seguridad

### SSL/TLS

Si quieres forzar HTTPS para el API:

```yaml
http:
  routers:
    invoice-api:
      # ...
      entryPoints:
        - https  # Solo HTTPS
      tls:
        certResolver: letsencrypt
```

O permitir ambos HTTP y HTTPS:

```yaml
entryPoints:
  - http
  - https
```

---

## ✅ Ventajas de esta Solución

1. ✅ **No rompe nada existente** - Solo agrega nueva configuración
2. ✅ **Hot reload** - Traefik detecta cambios automáticamente
3. ✅ **Simple** - Un archivo YAML
4. ✅ **Mantenible** - Fácil de modificar después
5. ✅ **Consistente** - Todo en Traefik (no mezclar con Nginx)

---

## 📝 Checklist de Implementación

- [ ] Verificar IP del host desde Docker (o usar network_mode: host)
- [ ] Crear archivo `/home/alex/proyectos/infra/traefik/config/invoice-api.yml`
- [ ] Verificar que Traefik detecta el archivo (logs)
- [ ] Probar endpoint `/api/facturas/summary?month=7&year=2025`
- [ ] Verificar que rutas existentes siguen funcionando
- [ ] Configurar SSL si es necesario

---

**Estado:** 📋 Propuesta completa - Lista para implementar

**Recomendación:** Usar File Provider con network_mode: host para simplicidad

