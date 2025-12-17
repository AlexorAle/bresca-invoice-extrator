# Problema Recurrente: Error 404 en Frontend después de Cambios Pequeños

## 📋 Descripción del Problema

### Síntoma
Después de realizar cambios pequeños en el frontend (como ajustar estilos de columnas, agregar campos, o modificar componentes), el sitio web deja de ser accesible desde el exterior, mostrando un **error 404** al intentar acceder a `https://alexforge.online/invoice-dashboard/`.

### Frecuencia
Este problema ocurre **cada vez** que se redespliega el frontend, especialmente cuando se usa el comando `docker run` directamente o cuando se recrea el contenedor sin seguir el proceso completo.

---

## 🔍 Análisis Técnico del Problema

### Arquitectura Actual

```
Navegador → Traefik (Reverse Proxy) → Contenedor Frontend (puerto 80)
           ↓
    https://alexforge.online/invoice-dashboard/*
           ↓
    Traefik aplica reglas de routing basadas en LABELS del contenedor
```

### Causa Raíz

El problema se origina en la **configuración de labels de Traefik** en el contenedor Docker. Cuando se recrea el contenedor, si los labels no están **exactamente correctos**, Traefik no puede enrutar correctamente las peticiones.

### Labels Incorrectos (Causan 404)

```bash
# ❌ CONFIGURACIÓN INCORRECTA
docker run -d \
  --name invoice-frontend-prod \
  --network traefik-public \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.invoice-frontend.rule=Host(\`alexforge.online\`)" \
  --label "traefik.http.routers.invoice-frontend.entrypoints=websecure" \
  --label "traefik.http.routers.invoice-frontend.tls.certresolver=letsencrypt" \
  --label "traefik.http.services.invoice-frontend.loadbalancer.server.port=80" \
  invoice-frontend
```

**Problemas en esta configuración:**
1. ❌ **`entrypoints=websecure`** → Debería ser `https` (el entrypoint correcto en Traefik)
2. ❌ **Sin `PathPrefix`** → La regla no incluye `/invoice-dashboard`, por lo que Traefik no sabe que debe enrutar esa ruta
3. ❌ **Sin middleware de strip prefix** → Aunque Traefik reciba la petición, no elimina el prefijo `/invoice-dashboard` antes de enviarla al contenedor
4. ❌ **Sin servicio explícito** → Traefik no puede crear correctamente el servicio de balanceo de carga

### Labels Correctos (Funcionan)

```bash
# ✅ CONFIGURACIÓN CORRECTA
docker run -d \
  --name invoice-frontend-prod \
  --network traefik-public \
  --restart unless-stopped \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.invoice-frontend.rule=Host(\`alexforge.online\`) && PathPrefix(\`/invoice-dashboard\`)" \
  --label "traefik.http.routers.invoice-frontend.entrypoints=https" \
  --label "traefik.http.routers.invoice-frontend.service=invoice-frontend-service" \
  --label "traefik.http.routers.invoice-frontend.tls.certresolver=letsencrypt" \
  --label "traefik.http.routers.invoice-frontend.middlewares=invoice-strip-prefix" \
  --label "traefik.http.middlewares.invoice-strip-prefix.stripprefix.prefixes=/invoice-dashboard" \
  --label "traefik.http.services.invoice-frontend-service.loadbalancer.server.port=80" \
  invoice-frontend
```

**Por qué funciona:**
1. ✅ **`entrypoints=https`** → Usa el entrypoint correcto configurado en Traefik
2. ✅ **`PathPrefix(\`/invoice-dashboard\`)`** → Traefik sabe que debe enrutar todas las peticiones que empiecen con `/invoice-dashboard`
3. ✅ **Middleware `invoice-strip-prefix`** → Elimina el prefijo `/invoice-dashboard` antes de enviar la petición al contenedor (el contenedor espera rutas sin prefijo)
4. ✅ **Servicio explícito** → Traefik puede crear correctamente el servicio de balanceo de carga

---

## 🔄 Por Qué Ocurre Después de Cambios Pequeños

### Flujo Problemático Actual

1. **Desarrollador hace un cambio pequeño** (ej: ajustar estilo de columna)
2. **Reconstruye la imagen** con `docker build`
3. **Recrea el contenedor** con `docker run` pero **olvida o copia mal los labels**
4. **Labels incorrectos** → Traefik no puede enrutar → **404**
5. **Desarrollador se da cuenta** → Tiene que corregir manualmente los labels
6. **Proceso se repite** en el siguiente cambio

### Razones por las que se rompe fácilmente:

1. **Comando manual propenso a errores**: Copiar/pegar los labels es fácil de hacer mal
2. **Falta de automatización**: No hay un script que siempre use los labels correctos
3. **Documentación dispersa**: Los labels correctos están en varios lugares
4. **Sin validación**: No hay verificación automática de que los labels sean correctos

---

## ✅ Solución Actual

### Script de Redeploy (`scripts/redeploy_frontend.sh`)

El script actual automatiza el proceso y **siempre usa los labels correctos**:

```bash
#!/bin/bash
# ... código de build ...

docker run -d \
  --name invoice-frontend-prod \
  --network traefik-public \
  --restart unless-stopped \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.invoice-frontend.rule=Host(\`alexforge.online\`) && PathPrefix(\`/invoice-dashboard\`)" \
  --label "traefik.http.routers.invoice-frontend.entrypoints=https" \
  --label "traefik.http.routers.invoice-frontend.service=invoice-frontend-service" \
  --label "traefik.http.routers.invoice-frontend.tls.certresolver=letsencrypt" \
  --label "traefik.http.routers.invoice-frontend.middlewares=invoice-strip-prefix" \
  --label "traefik.http.middlewares.invoice-strip-prefix.stripprefix.prefixes=/invoice-dashboard" \
  --label "traefik.http.services.invoice-frontend-service.loadbalancer.server.port=80" \
  invoice-frontend
```

**Ventajas:**
- ✅ Labels siempre correctos
- ✅ Automatiza todo el proceso
- ✅ Reduce errores humanos

**Desventajas:**
- ❌ Si alguien recrea el contenedor manualmente, puede romperlo
- ❌ No hay validación de que el contenedor tenga los labels correctos
- ❌ No hay rollback automático si algo falla

---

## 🚀 Propuesta de Mejora

### Problema con la Solución Actual

Aunque el script funciona, **el problema persiste** porque:
1. Los desarrolladores pueden recrear contenedores manualmente
2. No hay validación automática de configuración
3. No hay forma de prevenir que se use una configuración incorrecta

### Soluciones Propuestas

#### Opción 1: Docker Compose (Recomendada)

**Ventajas:**
- ✅ Configuración versionada en código
- ✅ Imposible olvidar labels (están en el archivo)
- ✅ Fácil de mantener y actualizar
- ✅ Rollback simple (git revert)

**Implementación:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  invoice-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_BASE_URL=/invoice-api/api
    container_name: invoice-frontend-prod
    networks:
      - traefik-public
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.invoice-frontend.rule=Host(\`alexforge.online\`) && PathPrefix(\`/invoice-dashboard\`)"
      - "traefik.http.routers.invoice-frontend.entrypoints=https"
      - "traefik.http.routers.invoice-frontend.service=invoice-frontend-service"
      - "traefik.http.routers.invoice-frontend.tls.certresolver=letsencrypt"
      - "traefik.http.routers.invoice-frontend.middlewares=invoice-strip-prefix"
      - "traefik.http.middlewares.invoice-strip-prefix.stripprefix.prefixes=/invoice-dashboard"
      - "traefik.http.services.invoice-frontend-service.loadbalancer.server.port=80"

networks:
  traefik-public:
    external: true
```

**Uso:**
```bash
# Rebuild y redeploy
docker-compose up -d --build invoice-frontend

# Solo redeploy (sin rebuild)
docker-compose up -d invoice-frontend
```

#### Opción 2: Script con Validación

Agregar validación al script para verificar que los labels sean correctos:

```bash
#!/bin/bash
# ... código existente ...

# Validar labels antes de crear contenedor
validate_traefik_labels() {
  local container_name=$1
  local labels=$(docker inspect $container_name --format '{{range $key, $value := .Config.Labels}}{{$key}}={{$value}}{{"\n"}}{{end}}' 2>/dev/null)
  
  if [ -z "$labels" ]; then
    return 0  # Contenedor no existe, OK
  fi
  
  # Verificar labels críticos
  if ! echo "$labels" | grep -q "entrypoints=https"; then
    echo "❌ ERROR: entrypoints debe ser 'https'"
    return 1
  fi
  
  if ! echo "$labels" | grep -q "PathPrefix"; then
    echo "❌ ERROR: Falta PathPrefix en la regla"
    return 1
  fi
  
  if ! echo "$labels" | grep -q "invoice-strip-prefix"; then
    echo "❌ ERROR: Falta middleware de strip prefix"
    return 1
  fi
  
  return 0
}

# Usar validación
if ! validate_traefik_labels invoice-frontend-prod; then
  echo "⚠️  Contenedor existente tiene labels incorrectos. Eliminando..."
  docker stop invoice-frontend-prod 2>/dev/null
  docker rm invoice-frontend-prod 2>/dev/null
fi
```

#### Opción 3: Pre-commit Hook

Validar configuración antes de hacer commit:

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Verificar que docker-compose.yml tiene los labels correctos
if ! grep -q "entrypoints=https" docker-compose.yml; then
  echo "❌ ERROR: docker-compose.yml tiene entrypoints incorrecto"
  exit 1
fi

if ! grep -q "PathPrefix" docker-compose.yml; then
  echo "❌ ERROR: docker-compose.yml falta PathPrefix"
  exit 1
fi
```

#### Opción 4: Health Check Automático

Agregar health check que valide que el sitio es accesible:

```bash
# En el script de redeploy
echo "🔍 Verificando que el sitio es accesible..."
sleep 10  # Esperar que Traefik actualice

if curl -f -s https://alexforge.online/invoice-dashboard/ > /dev/null; then
  echo "✅ Sitio accesible correctamente"
else
  echo "❌ ERROR: Sitio no accesible. Verifica labels de Traefik"
  exit 1
fi
```

---

## 📊 Comparación de Soluciones

| Solución | Complejidad | Prevención de Errores | Mantenibilidad | Recomendación |
|----------|-------------|----------------------|----------------|---------------|
| **Script actual** | Baja | Media | Media | ⚠️ Funciona pero propenso a errores |
| **Docker Compose** | Media | Alta | Alta | ✅ **Recomendada** |
| **Script + Validación** | Media | Alta | Media | ✅ Buena opción |
| **Pre-commit Hook** | Baja | Media | Baja | ⚠️ Solo previene en git |
| **Health Check** | Baja | Baja | Baja | ⚠️ Detecta pero no previene |

---

## 🎯 Recomendación Final

### Solución Híbrida (Mejor de ambos mundos)

1. **Usar Docker Compose** como fuente de verdad para la configuración
2. **Mantener el script** como wrapper que usa docker-compose internamente
3. **Agregar validación** en el script para verificar configuración
4. **Health check** después del deploy para confirmar que funciona

**Beneficios:**
- ✅ Configuración versionada (docker-compose.yml en git)
- ✅ Imposible olvidar labels (están en el archivo)
- ✅ Script sigue siendo fácil de usar
- ✅ Validación automática previene errores
- ✅ Health check confirma que todo funciona

---

## 📝 Checklist para Evitar el Error 404

- [ ] Usar siempre `docker-compose` o el script `redeploy_frontend.sh`
- [ ] Nunca recrear contenedores manualmente con `docker run`
- [ ] Verificar que los labels incluyan `PathPrefix` y `entrypoints=https`
- [ ] Verificar que existe el middleware de strip prefix
- [ ] Esperar 5-10 segundos después del deploy para que Traefik actualice
- [ ] Probar acceso desde navegador en modo incógnito
- [ ] Si falla, verificar logs de Traefik: `docker logs traefik | grep invoice-frontend`

---

## 🔗 Referencias

- Documentación de Traefik: https://doc.traefik.io/traefik/routing/routers/
- Script actual: `scripts/redeploy_frontend.sh`
- Documentación de deployment: `COMANDOS_DESPLIEGUE_FRONTEND.md`

---

*Última actualización: Diciembre 2025*

