# Acciones de Limpieza de Disco - Priorizadas por Impacto

**Fecha de análisis:** 2025-01-27  
**Ubicación analizada:** `~/proyectos`  
**Total espacio recuperable estimado:** ~39GB

---

## Resumen Ejecutivo

Análisis realizado sobre el servidor VPS (82.25.101.32) para identificar oportunidades de liberación de espacio en disco, basado en las mejoras sugeridas en `SERVER_ARCHITECTURE_OVERVIEW.md` y verificación real de tamaños.

**Espacio total analizado:** 4.6GB en `~/proyectos` + ~39GB en Docker

---

## Acciones Priorizadas (Mayor a Menor Impacto)

### 1. 🐳 Limpiar Imágenes Docker Sin Usar
**Impacto estimado:** ~28.83GB  
**Ubicación:** Sistema Docker  
**Riesgo:** Bajo (solo imágenes no referenciadas)

**Acción:**
```bash
# Ver imágenes sin usar (dangling)
docker images --filter "dangling=true"

# Eliminar imágenes sin usar
docker image prune -a --force

# O más agresivo: eliminar todas las imágenes no usadas por contenedores activos
docker image prune -a --force --filter "until=168h"  # imágenes >7 días sin usar
```

**Detalles:**
- Docker reporta 28.83GB recuperables (83% del total de imágenes)
- 127 imágenes dangling detectadas
- Solo se eliminarán imágenes no referenciadas por contenedores activos
- **Recomendación:** Ejecutar primero `docker images` para revisar manualmente

**Comando de verificación:**
```bash
docker system df  # Ver espacio antes/después
```

---

### 2. 🏗️ Limpiar Build Cache de Docker
**Impacto estimado:** ~9.81GB  
**Ubicación:** Docker build cache  
**Riesgo:** Muy bajo (solo cache de builds)

**Acción:**
```bash
# Limpiar todo el build cache
docker builder prune -a --force

# O con límite de tiempo (más conservador)
docker builder prune --force --filter "until=168h"  # cache >7 días
```

**Detalles:**
- 9.809GB de build cache completamente recuperable
- No afecta imágenes o contenedores existentes
- Se regenerará automáticamente en próximos builds
- **Recomendación:** Ejecutar periódicamente (semanal/mensual)

---

### 3. 📦 Limpiar Cache de Next.js (.next/cache)
**Impacto estimado:** ~127MB  
**Ubicación:** `~/proyectos/investment-dashboard/.next/cache`  
**Riesgo:** Muy bajo (cache regenerable)

**Acción:**
```bash
cd ~/proyectos/investment-dashboard
rm -rf .next/cache
```

**Detalles:**
- Cache de webpack y otros assets de Next.js
- Se regenera automáticamente en el próximo build
- No afecta funcionalidad, solo velocidad de rebuild inicial
- **Recomendación:** Limpiar periódicamente o después de cambios grandes

**Alternativa (más conservadora):**
```bash
# Limpiar solo cache antiguo (>30 días)
find ~/proyectos/investment-dashboard/.next/cache -type f -mtime +30 -delete
```

---

### 4. 📝 Limpiar Logs Antiguos del Trading Bot
**Impacto estimado:** ~46MB  
**Ubicación:** `~/proyectos/bot-trading/backtrader_engine/logs`  
**Riesgo:** Bajo (solo logs históricos)

**Acción:**
```bash
cd ~/proyectos/bot-trading/backtrader_engine/logs

# Opción 1: Eliminar logs >30 días
find . -type f -name "*.log" -mtime +30 -delete

# Opción 2: Eliminar logs >7 días (más agresivo)
find . -type f -name "*.log" -mtime +7 -delete

# Opción 3: Comprimir logs antiguos en lugar de eliminar
find . -type f -name "*.log" -mtime +7 -exec gzip {} \;
```

**Detalles:**
- 46MB de logs en `backtrader_engine/logs`
- Logs antiguos no son críticos para operación diaria
- **Recomendación:** Implementar rotación automática (logrotate) para futuro
- Verificar que no haya logs críticos antes de eliminar

**Verificación:**
```bash
# Ver tamaño antes
du -sh ~/proyectos/bot-trading/backtrader_engine/logs

# Ver logs más antiguos
ls -lth ~/proyectos/bot-trading/backtrader_engine/logs | tail -10
```

---

### 5. 💾 Limpiar Datos Antiguos de Backtrader Engine
**Impacto estimado:** ~59MB  
**Ubicación:** `~/proyectos/bot-trading/backtrader_engine/data`  
**Riesgo:** Medio (verificar qué datos son necesarios)

**Acción:**
```bash
cd ~/proyectos/bot-trading/backtrader_engine/data

# Ver contenido antes de eliminar
ls -lth

# Eliminar datos de backtesting antiguos (>90 días)
find . -type f -mtime +90 -delete

# O más conservador: mover a backup antes de eliminar
mkdir -p ../backups/data_old
find . -type f -mtime +90 -exec mv {} ../backups/data_old/ \;
```

**Detalles:**
- 59MB de datos de backtesting
- **IMPORTANTE:** Verificar qué archivos son necesarios antes de eliminar
- Algunos datos pueden ser resultados de backtests históricos importantes
- **Recomendación:** Hacer backup antes de eliminar, o mover a almacenamiento externo

**Verificación previa:**
```bash
# Ver archivos más antiguos
find ~/proyectos/bot-trading/backtrader_engine/data -type f -mtime +90 -ls
```

---

### 6. 📋 Limpiar Logs del Invoice Extractor
**Impacto estimado:** ~12MB  
**Ubicación:** `~/proyectos/invoice-extractor/logs`  
**Riesgo:** Bajo (solo logs históricos)

**Acción:**
```bash
cd ~/proyectos/invoice-extractor/logs

# Eliminar logs >30 días
find . -type f -name "*.log" -mtime +30 -delete

# O comprimir en lugar de eliminar
find . -type f -name "*.log" -mtime +30 -exec gzip {} \;
```

**Detalles:**
- 12MB de logs
- Similar a acción #4, pero para Invoice Extractor
- **Recomendación:** Implementar rotación automática

---

### 7. 🗑️ Limpiar Archivos __pycache__ y .pyc
**Impacto estimado:** ~11MB  
**Ubicación:** Múltiples proyectos (4,855 directorios __pycache__ detectados)  
**Riesgo:** Muy bajo (archivos regenerables)

**Acción:**
```bash
# Desde ~/proyectos, eliminar todos los __pycache__
find ~/proyectos -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Eliminar archivos .pyc y .pyo sueltos
find ~/proyectos -type f -name "*.pyc" -delete
find ~/proyectos -type f -name "*.pyo" -delete
```

**Detalles:**
- 4,855 directorios `__pycache__` detectados
- ~11MB de archivos .pyc
- Se regeneran automáticamente al ejecutar Python
- **Recomendación:** Agregar `__pycache__/` y `*.pyc` a `.gitignore` si no están ya

**Nota:** Los `__pycache__` dentro de `venv/` y `.venv/` NO deben eliminarse (son parte de los paquetes instalados).

---

### 8. 📊 Limpiar api_timings.jsonl (Investment Dashboard)
**Impacto estimado:** ~128KB  
**Ubicación:** `~/proyectos/investment-dashboard/backend/app/api_timings.jsonl`  
**Riesgo:** Muy bajo (archivo de métricas)

**Acción:**
```bash
# Opción 1: Truncar archivo (mantener últimas 1000 líneas)
cd ~/proyectos/investment-dashboard/backend/app
tail -n 1000 api_timings.jsonl > api_timings.jsonl.tmp
mv api_timings.jsonl.tmp api_timings.jsonl

# Opción 2: Eliminar completamente (se regenerará)
rm ~/proyectos/investment-dashboard/backend/app/api_timings.jsonl
```

**Detalles:**
- 128KB de métricas de timing de API
- Archivo mencionado en documentación como candidato a limpieza
- **Recomendación:** Implementar rotación automática o límite de tamaño en el código

---

### 9. 💿 Limpiar Backups Antiguos
**Impacto estimado:** ~1MB  
**Ubicación:** 
- `~/proyectos/invoice-extractor/data/backups` (876KB)
- `~/proyectos/bot-trading/backtrader_engine/backups` (72KB)

**Riesgo:** Medio (verificar qué backups son necesarios)

**Acción:**
```bash
# Invoice Extractor
cd ~/proyectos/invoice-extractor/data/backups
# Ver backups antiguos (>90 días)
find . -type f -mtime +90 -ls
# Eliminar o mover a almacenamiento externo
find . -type f -mtime +90 -delete

# Trading Bot
cd ~/proyectos/bot-trading/backtrader_engine/backups
find . -type f -mtime +90 -ls
find . -type f -mtime +90 -delete
```

**Detalles:**
- Impacto pequeño (~1MB) pero importante para mantener orden
- **IMPORTANTE:** Verificar que los backups antiguos no sean necesarios
- **Recomendación:** Implementar política de retención (ej: 7 diarios + 4 semanales + 12 mensuales)

---

## Acciones NO Recomendadas (Espacio Necesario)

### ❌ NO Eliminar Entornos Virtuales (venv/.venv)
**Razón:** Son necesarios para ejecutar las aplicaciones
- `bot-trading/venv`: 927MB
- `invoice-extractor/venv`: 836MB
- `bresca-reportes-drive-dash/.venv`: 581MB

### ❌ NO Eliminar node_modules
**Razón:** Necesario para compilar/build del frontend
- `investment-dashboard/node_modules`: 729MB

### ❌ NO Eliminar .next (completo)
**Razón:** Contiene el build de producción de Next.js
- `investment-dashboard/.next`: 199MB (solo cache es eliminable, ver acción #3)

### ❌ NO Eliminar Repositorios Git (.git)
**Razón:** Historial de versiones necesario
- Total: ~28MB (impacto mínimo)

---

## Script de Limpieza Automatizada (Opcional)

Puedes crear un script para ejecutar las acciones de bajo riesgo:

```bash
#!/bin/bash
# ~/proyectos/limpiar_disco.sh

set -e

echo "🧹 Iniciando limpieza de disco..."

# 1. Docker (requiere confirmación manual)
echo "📦 Limpiando Docker..."
read -p "¿Limpiar imágenes Docker sin usar? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker image prune -a --force
fi

read -p "¿Limpiar build cache de Docker? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker builder prune -a --force
fi

# 2. Next.js cache (automático)
echo "📦 Limpiando cache de Next.js..."
rm -rf ~/proyectos/investment-dashboard/.next/cache
echo "✅ Cache de Next.js limpiado"

# 3. Logs antiguos (>30 días)
echo "📝 Limpiando logs antiguos..."
find ~/proyectos/bot-trading/backtrader_engine/logs -type f -name "*.log" -mtime +30 -delete
find ~/proyectos/invoice-extractor/logs -type f -name "*.log" -mtime +30 -delete
echo "✅ Logs antiguos eliminados"

# 4. __pycache__
echo "🗑️ Limpiando __pycache__..."
find ~/proyectos -type d -name "__pycache__" ! -path "*/venv/*" ! -path "*/.venv/*" -exec rm -rf {} + 2>/dev/null || true
find ~/proyectos -type f -name "*.pyc" ! -path "*/venv/*" ! -path "*/.venv/*" -delete
find ~/proyectos -type f -name "*.pyo" ! -path "*/venv/*" ! -path "*/.venv/*" -delete
echo "✅ __pycache__ limpiado"

# 5. api_timings.jsonl (truncar)
echo "📊 Truncando api_timings.jsonl..."
if [ -f ~/proyectos/investment-dashboard/backend/app/api_timings.jsonl ]; then
    tail -n 1000 ~/proyectos/investment-dashboard/backend/app/api_timings.jsonl > /tmp/api_timings.jsonl.tmp
    mv /tmp/api_timings.jsonl.tmp ~/proyectos/investment-dashboard/backend/app/api_timings.jsonl
    echo "✅ api_timings.jsonl truncado"
fi

echo ""
echo "✅ Limpieza completada"
echo "💾 Espacio liberado (verificar con: docker system df && du -sh ~/proyectos)"
```

**Uso:**
```bash
chmod +x ~/proyectos/limpiar_disco.sh
~/proyectos/limpiar_disco.sh
```

---

## Resumen de Impacto Total

| Acción | Espacio Recuperable | Riesgo | Prioridad |
|--------|---------------------|--------|-----------|
| 1. Imágenes Docker sin usar | ~28.83GB | Bajo | 🔴 Alta |
| 2. Build cache Docker | ~9.81GB | Muy bajo | 🔴 Alta |
| 3. Cache Next.js | ~127MB | Muy bajo | 🟡 Media |
| 4. Logs Trading Bot | ~46MB | Bajo | 🟡 Media |
| 5. Datos Backtrader | ~59MB | Medio | 🟡 Media |
| 6. Logs Invoice Extractor | ~12MB | Bajo | 🟢 Baja |
| 7. __pycache__ | ~11MB | Muy bajo | 🟢 Baja |
| 8. api_timings.jsonl | ~128KB | Muy bajo | 🟢 Baja |
| 9. Backups antiguos | ~1MB | Medio | 🟢 Baja |
| **TOTAL ESTIMADO** | **~38.9GB** | - | - |

---

## Recomendaciones Post-Limpieza

1. **Implementar rotación automática de logs:**
   - Configurar `logrotate` para logs de aplicaciones
   - O implementar en código (ej: `RotatingFileHandler` en Python)

2. **Monitoreo de espacio:**
   ```bash
   # Agregar a crontab para alertas
   0 0 * * * df -h / | awk 'NR==2 {if ($5 > 80) print "ALERTA: Disco >80%"}' | mail -s "Alerta Disco" admin@example.com
   ```

3. **Limpieza periódica:**
   - Ejecutar acciones #2, #3, #7 mensualmente
   - Ejecutar acciones #4, #6 semanalmente
   - Revisar Docker trimestralmente

4. **Política de retención:**
   - Documentar qué datos deben conservarse y por cuánto tiempo
   - Implementar backups externos para datos críticos

---

**Última actualización:** 2025-01-27  
**Próxima revisión recomendada:** 2025-02-27

---

## ✅ Ejecución Realizada (2025-01-27)

### Acciones Completadas

#### ✅ 1. Limpieza de Imágenes Docker Sin Usar
**Estado:** ✅ COMPLETADO  
**Espacio liberado:** ~26.8GB  
**Resultado:**
- **Antes:** 148 imágenes, 34.52GB total
- **Después:** 19 imágenes, 7.724GB total
- **Eliminadas:** 129 imágenes dangling (sin tag, versiones antiguas)
- **Preservadas:** Todas las imágenes con tag, incluyendo:
  - ✅ `docker.n8n.io/n8nio/n8n:latest` (N8N - 718MB)
  - ✅ Todas las imágenes `latest` de proyectos activos
  - ✅ Imágenes base (postgres, redis, traefik, etc.)

**Verificación:**
- ✅ N8N sigue funcionando correctamente
- ✅ Todos los contenedores activos siguen operativos
- ✅ No se eliminaron imágenes en uso

#### ✅ 2. Limpieza de Build Cache de Docker
**Estado:** ✅ COMPLETADO  
**Espacio liberado:** ~9.77GB  
**Resultado:**
- **Antes:** 325 entradas de cache, 9.769GB
- **Después:** 0 entradas, 0B
- **Total eliminado:** 9.769GB de build cache

**Nota:** El cache se regenerará automáticamente en próximos builds.

### Resumen Total

| Métrica | Antes | Después | Liberado |
|---------|-------|---------|----------|
| **Imágenes Docker** | 34.52GB (148) | 7.724GB (19) | **~26.8GB** |
| **Build Cache** | 9.77GB | 0B | **~9.77GB** |
| **TOTAL LIBERADO** | - | - | **~36.57GB** |

### Verificación Post-Limpieza

✅ **Contenedores activos:** 15/15 funcionando correctamente  
✅ **N8N:** Operativo (`root-n8n-1` - Up 2 weeks)  
✅ **Aplicaciones críticas:** Todas operativas
- Trading Bot (Prometheus, Grafana)
- Investment Dashboard
- Invoice Extractor
- Command Center
- Traefik
- Portainer
- Uptime Kuma

### Comandos Ejecutados

```bash
# 1. Limpieza de imágenes dangling
docker image prune -f --filter "dangling=true"

# 2. Limpieza de build cache
docker builder prune -a -f

# 3. Verificación
docker system df
docker ps
docker images | grep n8n
```

### Notas Importantes

- ✅ **N8N preservado:** La imagen `docker.n8n.io/n8nio/n8n:latest` se mantuvo intacta
- ✅ **Imágenes con tag preservadas:** Todas las imágenes con tag (latest, versiones específicas) se mantuvieron
- ✅ **Sin impacto en servicios:** Todos los contenedores siguen funcionando normalmente
- ⚠️ **Build cache:** Se regenerará en próximos builds (no afecta funcionalidad)

### Próximos Pasos Recomendados

1. **Monitoreo:** Verificar uso de disco en los próximos días
2. **Limpieza periódica:** Ejecutar limpieza de build cache mensualmente
3. **Rotación de logs:** Implementar acciones #4, #6 del documento
4. **Cache Next.js:** Considerar limpiar `.next/cache` (acción #3) si es necesario

