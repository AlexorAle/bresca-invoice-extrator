# Integración Loki/Promtail - Sistema de Logging Centralizado

**Fecha:** 2025-12-03  
**Estado:** Implementado y Activo  
**Ubicación:** `bot-trading/infrastructure/docker-compose.yml`

---

## 📋 Resumen Ejecutivo

Se ha implementado **Loki** (sistema de agregación de logs) y **Promtail** (agente de recolección) para centralizar y visualizar logs de todas las aplicaciones. La integración permite consultar logs desde Grafana usando LogQL.

---

## 🎯 Componentes Implementados

### Loki (Log Aggregation)
- **Imagen:** `grafana/loki:2.9.2`
- **Contenedor:** `loki`
- **Puerto interno:** `3100` (HTTP API)
- **Estado:** Activo
- **Función:** Agrega y almacena logs de todas las aplicaciones

### Promtail (Log Shipper)
- **Imagen:** `grafana/promtail:2.9.2`
- **Contenedor:** `promtail`
- **Puerto interno:** `9080` (métricas)
- **Estado:** Activo
- **Función:** Recolecta logs de archivos y contenedores Docker, envía a Loki

---

## 🔧 Configuración

### Ubicación de Archivos
- **Docker Compose:** `bot-trading/infrastructure/docker-compose.yml`
- **Config Loki:** `bot-trading/infrastructure/loki-config.yml`
- **Config Promtail:** `bot-trading/infrastructure/promtail-config.yml`

### Volúmenes Montados

**Loki:**
- `loki_data:/loki` - Almacenamiento persistente de logs

**Promtail:**
- `../backtrader_engine/logs:/var/log/trading-bot:ro` - Logs del trading bot (read-only)
- `promtail_positions:/tmp` - Tracking de posiciones de lectura

### Red Docker
- Ambos servicios están en la red `traefik-public`
- **No expuestos públicamente** (solo acceso interno)

---

## 🔗 Integración con Grafana

### Configuración de Datasource

Grafana está configurado para usar Loki como datasource de logs:

1. **URL de Loki:** `http://loki:3100` (dentro de la red Docker)
2. **Tipo:** Loki
3. **Query Language:** LogQL

### Consultas LogQL Ejemplos

```logql
# Logs de todas las aplicaciones
{app="trading-bot"}

# Logs por componente
{app="trading-bot", component="bot"}

# Logs de nivel ERROR
{app="trading-bot"} |= "ERROR"

# Logs con filtro de tiempo
{app="trading-bot"} [5m]
```

---

## 📊 Flujo de Logs

```
┌─────────────────┐
│ Trading Bot     │
│ (logs a archivo)│
└────────┬────────┘
         │
         │ (volumen montado)
         ▼
┌─────────────────┐
│   Promtail      │
│  (recolecta)    │
└────────┬────────┘
         │
         │ (envía vía HTTP)
         ▼
┌─────────────────┐
│     Loki        │
│  (almacena)     │
└────────┬────────┘
         │
         │ (consulta vía API)
         ▼
┌─────────────────┐
│    Grafana      │
│  (visualiza)    │
└─────────────────┘
```

---

## 🔍 Acceso y Consultas

### Desde Grafana

1. **Navegar a:** `https://82.25.101.32/grafana`
2. **Explorer → Loki datasource**
3. **Usar LogQL** para consultar logs

### Desde Command Center

El Command Center tiene integración con Grafana/Loki para abrir consultas directamente:

- Botón "Abrir Grafana" en la sección de logs
- Genera URLs pre-configuradas con filtros aplicados

---

## 📝 Labels y Metadatos

Promtail agrega labels a los logs para facilitar filtrado:

- `app`: Identificador de la aplicación (trading-bot, invoice-extractor, etc.)
- `component`: Componente (backend, frontend, bot, db)
- `level`: Nivel de log (INFO, WARN, ERROR, DEBUG)
- `source`: Fuente del log (docker, file)

---

## ✅ Estado Actual

- ✅ Loki corriendo (puerto 3100)
- ✅ Promtail corriendo (puerto 9080)
- ✅ Integración con Grafana configurada
- ✅ Logs del trading bot siendo recolectados
- ✅ Command Center con enlaces a Grafana/Loki

---

## 🚀 Próximos Pasos

1. **Expandir recolección:** Agregar más fuentes de logs (otros proyectos)
2. **Configurar retención:** Ajustar políticas de retención en Loki
3. **Alertas:** Configurar alertas en Grafana basadas en logs
4. **Dashboards:** Crear dashboards específicos para análisis de logs

---

## 🔧 Mantenimiento

### Verificar Estado

```bash
# Verificar contenedores
docker ps | grep -E "loki|promtail"

# Verificar logs de Loki
docker logs loki --tail 50

# Verificar logs de Promtail
docker logs promtail --tail 50

# Verificar salud
curl http://localhost:3100/ready  # Loki
curl http://localhost:9080/ready  # Promtail
```

### Limpieza de Datos

```bash
# Ver tamaño de volúmenes
docker volume ls | grep loki

# Limpiar datos antiguos (si es necesario)
# Editar loki-config.yml para ajustar retención
```

---

**Fin del documento**

