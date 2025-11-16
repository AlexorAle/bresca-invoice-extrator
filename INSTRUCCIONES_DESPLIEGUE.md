# Instrucciones para Desplegar el Nuevo Frontend

## ✅ Build Completado

La nueva imagen Docker se ha construido exitosamente:
- **Imagen:** `invoice-frontend:latest`
- **Build:** Completado con los cambios del componente compacto
- **Verificación local:** ✅ Funcionando correctamente

## Pasos para Desplegar en Producción

### Opción 1: Si usas docker-compose

```bash
cd /home/alex/proyectos/invoice-extractor
docker-compose stop frontend
docker-compose build frontend
docker-compose up -d frontend
```

### Opción 2: Si usas contenedores individuales

```bash
# 1. Detener el contenedor actual
docker stop invoice-frontend
docker rm invoice-frontend

# 2. Iniciar el nuevo contenedor con la imagen actualizada
docker run -d \
  --name invoice-frontend \
  --restart unless-stopped \
  -p 80:80 \
  invoice-frontend:latest

# O si está en una red Docker específica:
docker run -d \
  --name invoice-frontend \
  --restart unless-stopped \
  --network tu-red-docker \
  invoice-frontend:latest
```

### Opción 3: Si usas Traefik o proxy inverso

```bash
# 1. Detener contenedor actual
docker stop invoice-frontend

# 2. Reconstruir (si usas docker-compose con Traefik)
docker-compose build frontend
docker-compose up -d frontend

# 3. Verificar que Traefik detecta el nuevo contenedor
docker logs traefik | tail -20
```

## Verificación

Después de desplegar, verifica que:

1. **El contenedor está corriendo:**
   ```bash
   docker ps | grep invoice-frontend
   ```

2. **Los logs no muestran errores:**
   ```bash
   docker logs invoice-frontend | tail -20
   ```

3. **Accede desde el navegador:**
   - URL: `http://82.25.101.32/invoice-dashboard/`
   - Deberías ver el **componente compacto oscuro** en lugar de la barra de meses
   - El componente muestra: Mes grande + Año en azul
   - Al hacer click se abre el dropdown con los meses

## Cambios Implementados

✅ Componente compacto tipo "icono" con diseño oscuro (slate-900/800)
✅ Muestra mes actual en grande y año en azul
✅ Dropdown con selector de año (flechas izquierda/derecha)
✅ Grid de 3 columnas con los 12 meses
✅ Eliminada la barra horizontal de meses
✅ Eliminado el selector de año separado

## Rollback (si es necesario)

Si necesitas volver a la versión anterior:

```bash
# Si tienes la imagen anterior etiquetada
docker run -d --name invoice-frontend infrastructure-invoice-frontend:latest

# O reconstruir desde el commit anterior
git checkout HEAD~1 frontend/
docker-compose build frontend
docker-compose up -d frontend
```

## Notas

- El build incluye todos los cambios del componente compacto
- La imagen está lista para producción
- No se modificó ninguna configuración de acceso o rutas
- Solo se cambió el diseño visual del Header
