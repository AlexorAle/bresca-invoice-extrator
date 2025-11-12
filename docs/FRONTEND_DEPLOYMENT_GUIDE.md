# Guía de Deployment Frontend - Invoice Extractor

**Última actualización:** 2025-11-12  
**Stack:** React + Vite + Traefik (sin Nginx)

---

## 📋 Configuración Actual

### Arquitectura de Rutas

```
Browser → Traefik (puerto 80) → Frontend Container (puerto 80)
         ↓
    /invoice-dashboard/* → strip prefix → / → serve
```

### Configuración de Vite

**Archivo:** `frontend/vite.config.js`

```javascript
export default defineConfig({
  plugins: [react()],
  base: '/invoice-dashboard/', // ✅ Ruta absoluta (OBLIGATORIO)
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
```

**⚠️ IMPORTANTE:** `base` debe ser `/invoice-dashboard/` (ruta absoluta con trailing slash).  
**❌ NO usar:** `base: './'` (rutas relativas) - causa problemas con rutas internas de React Router.

### Configuración de Traefik

**Archivo:** `bot-trading/infrastructure/docker-compose.yml`

```yaml
invoice-frontend:
  labels:
    - "traefik.http.routers.invoice-frontend.rule=Host(`82.25.101.32`) && PathPrefix(`/invoice-dashboard`)"
    - "traefik.http.middlewares.invoice-dashboard-strip.stripprefix.prefixes=/invoice-dashboard"
    - "traefik.http.routers.invoice-frontend.middlewares=invoice-dashboard-strip"
```

**Flujo de rutas:**
1. Browser solicita: `http://82.25.101.32/invoice-dashboard/assets/index-xxx.js`
2. Traefik recibe: `/invoice-dashboard/assets/index-xxx.js`
3. Traefik aplica strip prefix: elimina `/invoice-dashboard` → queda `/assets/index-xxx.js`
4. Traefik envía al container: `/assets/index-xxx.js`
5. Container (`serve`) sirve el archivo desde `/app/dist/assets/index-xxx.js` ✅

---

## 🔧 Proceso de Build y Deploy

### 1. Hacer Cambios en el Código

Realizar cualquier cambio estético o funcional en:
- `frontend/src/components/*`
- `frontend/src/utils/*`
- `frontend/src/hooks/*`
- Cualquier archivo del frontend

### 2. Rebuild del Frontend

```bash
# Desde el directorio del proyecto
cd /home/alex/proyectos/invoice-extractor/frontend

# Rebuild de la imagen Docker (incluye npm run build automáticamente)
docker build --no-cache -t infrastructure-invoice-frontend .

# O si prefieres hacer build local primero (para testing):
npm run build
# Luego rebuild de Docker
docker build -t infrastructure-invoice-frontend .
```

### 3. Deploy del Contenedor

```bash
# Desde el directorio de infrastructure
cd /home/alex/proyectos/bot-trading/infrastructure

# Recrear y levantar el contenedor
docker-compose up -d invoice-frontend
```

### 4. Verificación

```bash
# Verificar que el contenedor está corriendo
docker ps | grep invoice-frontend

# Verificar logs
docker logs invoice-frontend --tail=20

# Probar acceso (desde el servidor)
curl -H "Host: 82.25.101.32" http://localhost/invoice-dashboard/ | head -20

# O desde fuera del servidor
curl http://82.25.101.32/invoice-dashboard/ | head -20
```

---

## ✅ Checklist de Cambios

Antes de hacer cualquier cambio que afecte rutas o builds:

- [ ] **Verificar `vite.config.js`:** `base: '/invoice-dashboard/'` (nunca cambiar a `./`)
- [ ] **Verificar `docker-compose.yml`:** strip prefix configurado correctamente
- [ ] **Hacer build:** `docker build` desde `frontend/`
- [ ] **Deploy:** `docker-compose up -d invoice-frontend`
- [ ] **Verificar:** Acceder a `/invoice-dashboard/` y probar rutas internas (ej: `/invoice-dashboard/` → tab "Pendientes")

---

## 🚨 Problemas Comunes y Soluciones

### Problema: 404 en assets (JS/CSS no cargan)

**Causa:** `base` en Vite no coincide con la ruta en Traefik.

**Solución:**
1. Verificar `vite.config.js`: debe ser `base: '/invoice-dashboard/'`
2. Rebuild completo: `docker build --no-cache -t infrastructure-invoice-frontend .`
3. Reiniciar contenedor: `docker-compose up -d invoice-frontend`

### Problema: Rutas internas de React Router no funcionan

**Causa:** Rutas relativas (`base: './'`) o configuración incorrecta de `serve`.

**Solución:**
- Usar `base: '/invoice-dashboard/'` (ruta absoluta)
- Verificar que `serve` esté en modo SPA: `serve -s dist -l 80 -n`

### Problema: Cambios no se reflejan después del rebuild

**Causa:** Caché del navegador o contenedor no se recreó.

**Solución:**
1. Rebuild sin caché: `docker build --no-cache`
2. Recrear contenedor: `docker-compose up -d --force-recreate invoice-frontend`
3. Limpiar caché del navegador: Ctrl+Shift+R (o Cmd+Shift+R en Mac)

---

## 📝 Notas Técnicas

### ¿Por qué rutas absolutas y no relativas?

1. **React Router:** Necesita rutas absolutas para navegación interna
2. **Assets estáticos:** El navegador siempre solicita desde la URL completa
3. **Traefik strip prefix:** Funciona correctamente con rutas absolutas
4. **Multi-proyecto:** Permite tener múltiples apps bajo diferentes paths

### ¿Por qué no usar Nginx?

- **Simplificación:** `serve` es más simple y suficiente para SPA estáticas
- **Menos configuración:** No requiere archivos de configuración de Nginx
- **Mismo resultado:** Ambos sirven archivos estáticos correctamente

### Estructura de Archivos en el Container

```
/app/
  └── dist/              # Build de Vite
      ├── index.html     # HTML principal
      ├── assets/        # JS, CSS, imágenes
      │   ├── index-xxx.js
      │   └── index-xxx.css
      └── vite.svg
```

El container ejecuta: `serve -s dist -l 80 -n`
- `-s`: Modo SPA (sirve index.html para todas las rutas)
- `-l 80`: Puerto 80
- `-n`: Sin banner

---

## 🔄 Historial de Cambios

### 2025-11-12: Migración a configuración robusta

**Cambios:**
- ✅ Configurado `base: '/invoice-dashboard/'` en Vite (rutas absolutas)
- ✅ Verificado strip prefix en Traefik
- ✅ Documentado proceso de build y deploy
- ✅ Eliminada dependencia de Nginx (usando `serve`)

**Razón:** Garantizar builds reproducibles y evitar problemas con rutas internas de React Router.

---

**Fin del documento**


