# Investigación: Frontend en Producción muestra datos antiguos

**Fecha:** 6 de noviembre de 2025  
**Problema:** El frontend en producción (http://82.25.101.32/invoice-dashboard/) muestra datos antiguos, mientras que localmente se ven las 19 facturas correctas.

---

## 🔍 Investigación Realizada

### 1. Verificación de Configuración Local

**Archivo:** `frontend/src/utils/api.js`

El frontend local está configurado para apuntar a:
- `VITE_API_BASE_URL` (probablemente `http://localhost:8001/api`)

### 2. Posibles Causas

#### A. Build Antiguo en Producción

**Problema:** El frontend en producción puede tener un build antiguo que:
- Fue compilado antes de los cambios recientes
- Tiene referencias a APIs antiguas
- Tiene datos hardcodeados o en cache

**Ubicación probable:**
- `/var/www/html/invoice-dashboard/`
- `/var/www/invoice-dashboard/`
- Otro directorio servido por nginx/apache

#### B. Frontend apuntando a API diferente

**Problema:** El frontend en producción puede estar apuntando a:
- Una API en un puerto diferente
- Una API en otro servidor
- Una BD diferente

#### C. Cache del Browser/Servidor

**Problema:** 
- Nginx/Apache puede estar sirviendo archivos con cache
- El browser puede tener cache de archivos estáticos antiguos

#### D. Build no actualizado

**Problema:** 
- El build de producción no se ha actualizado después de los cambios
- Los archivos estáticos en `/var/www` son antiguos

---

## 📊 Verificaciones Necesarias

### 1. Verificar ubicación del frontend en producción

```bash
# Buscar directorio del frontend
find /var/www -name "*invoice*" -type d
ls -lah /var/www/html/invoice-dashboard/
```

### 2. Verificar fecha de los archivos

```bash
# Ver cuándo se modificaron los archivos
ls -lah /var/www/html/invoice-dashboard/assets/*.js
```

### 3. Verificar configuración de API en el build

```bash
# Buscar referencias a localhost o puertos en los JS compilados
grep -r "localhost\|127.0.0.1\|8001" /var/www/html/invoice-dashboard/assets/*.js
```

### 4. Verificar endpoint de API accesible

```bash
# Probar si el API es accesible desde fuera
curl http://82.25.101.32/api/facturas/summary?month=7&year=2025
```

### 5. Verificar configuración de nginx/apache

```bash
# Ver configuración del servidor web
cat /etc/nginx/sites-enabled/* | grep invoice
```

---

## 🎯 Diagnóstico Probable

Basado en la descripción del problema:

1. **El frontend en producción tiene un build antiguo**
   - Los archivos en `/var/www/html/invoice-dashboard/` son de antes de procesar las 19 facturas
   - El build fue hecho cuando había datos de prueba ("Proveedor Test")

2. **El frontend puede estar apuntando a localhost**
   - Si el build fue hecho con `VITE_API_BASE_URL=http://localhost:8001/api`
   - El frontend en producción intentaría conectarse a localhost del browser del usuario, no al servidor

3. **El API puede no estar accesible desde fuera**
   - El API puede estar corriendo solo en localhost
   - No está expuesto en el puerto 80/443 o en un puerto público

---

## 💡 Soluciones Recomendadas (sin aplicar cambios)

### Opción 1: Rebuild del Frontend

1. **Verificar configuración de API para producción:**
   ```bash
   # En frontend/.env.production o similar
   VITE_API_BASE_URL=http://82.25.101.32/api
   ```

2. **Hacer nuevo build:**
   ```bash
   cd frontend
   npm run build
   ```

3. **Copiar build a producción:**
   ```bash
   cp -r dist/* /var/www/html/invoice-dashboard/
   ```

### Opción 2: Verificar API accesible

1. **Verificar que el API esté corriendo y accesible:**
   ```bash
   # El API debe estar en 0.0.0.0:8001, no en 127.0.0.1:8001
   # Y debe estar accesible desde fuera (firewall, nginx reverse proxy)
   ```

2. **Verificar nginx reverse proxy:**
   ```nginx
   location /api {
       proxy_pass http://localhost:8001;
   }
   ```

### Opción 3: Limpiar cache

1. **Limpiar cache de nginx:**
   ```bash
   sudo systemctl reload nginx
   ```

2. **Verificar headers de cache en nginx:**
   ```nginx
   location /invoice-dashboard {
       add_header Cache-Control "no-cache, no-store, must-revalidate";
   }
   ```

---

## 📝 Checklist de Verificación

- [ ] Verificar ubicación del frontend en producción
- [ ] Verificar fecha de modificación de archivos en producción
- [ ] Verificar configuración de API en el build de producción
- [ ] Verificar que el API sea accesible desde fuera (http://82.25.101.32/api)
- [ ] Verificar configuración de nginx/apache
- [ ] Verificar que el build de producción apunte a la API correcta
- [ ] Verificar headers de cache del servidor web

---

## 🔍 Comandos de Diagnóstico

```bash
# 1. Verificar ubicación
find /var/www -name "*invoice*" -type d

# 2. Ver fecha de archivos
ls -lah /var/www/html/invoice-dashboard/assets/*.js

# 3. Verificar API en build
grep -r "localhost\|8001" /var/www/html/invoice-dashboard/assets/*.js

# 4. Probar API desde fuera
curl http://82.25.101.32/api/facturas/summary?month=7&year=2025

# 5. Ver configuración nginx
cat /etc/nginx/sites-enabled/* | grep -A 20 invoice
```

---

**Estado:** 🔍 Investigación completada - Pendiente de verificación en servidor

