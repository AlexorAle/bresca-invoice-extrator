# Índice de Documentación - Arquitectura y Operaciones

**Última actualización:** 2025-12-11  
**Propósito:** Referencia rápida de todos los documentos disponibles para creación de prompts y consulta  
**Ubicación:** `~/proyectos/docs/` (también copiados en cada proyecto en `docs/`)

---

## 📚 Documentos Principales (`~/proyectos/docs/`)

### Arquitectura General
- **`SERVER_ARCHITECTURE_OVERVIEW.md`** ⭐
  - Visión general completa de la arquitectura del servidor
  - Detalles de cada aplicación
  - Configuración de infraestructura
  - Mapeo de servicios y puertos
  - **Útil para:** Arquitecto general, Full Stack Developer, Infraestructura

- **`MAPA_PUERTOS.md`** ⭐
  - Mapa completo de puertos (públicos e internos)
  - URLs de acceso a servicios
  - Configuración de Traefik
  - **Útil para:** Infraestructura, DevOps, Full Stack Developer

### Infraestructura Específica
- **`LOKI_INTEGRATION.md`** ⭐
  - Integración de Loki/Promtail para logging centralizado
  - Configuración y uso
  - Integración con Grafana
  - **Útil para:** Infraestructura, DevOps, Full Stack Developer

- **`COMMAND_CENTER_DASHBOARD.md`** ⭐
  - Documentación del Command Center
  - Funcionalidades del dashboard
  - APIs y endpoints
  - **Útil para:** Full Stack Developer, Infraestructura

- **`LIMPIEZA_DISCO_ACCIONES.md`**
  - Acciones de limpieza de disco priorizadas
  - Espacio recuperable
  - Comandos de limpieza
  - **Útil para:** Infraestructura, DevOps

### Mantenimiento
- **`LIMPIEZA_DISCO_ACCIONES.md`**
  - Acciones de limpieza de disco priorizadas
  - Espacio recuperable
  - Comandos de limpieza
  - **Útil para:** Infraestructura, DevOps

**Nota:** Documentos de migraciones pasadas (Traefik, Investment Portfolio) han sido eliminados. Su información está consolidada en `SERVER_ARCHITECTURE_OVERVIEW.md` y `MAPA_PUERTOS.md`.

---

## 📁 Documentos por Proyecto

### Trading Bot (`bot-trading/docs/`)
- **`SERVER_ARCHITECTURE_OVERVIEW.md`** - Copia del documento maestro
- **`IMPLEMENTACION_LOGGING_CENTRALIZADO.md`** ⭐
  - Especificaciones técnicas para implementar logging centralizado
  - Integración con live test logger
  - **Útil para:** Full Stack Developer, Trading Specialist
- **`LOKI_INTEGRATION.md`** - Integración específica de Loki
- **`IMPLEMENTACION_LIVE_TEST.md`** - Preparación para live test
- **`REPORTE_EJECUTIVO_IMPLEMENTACION.md`** - Reporte de implementación

### Investment Dashboard (`investment-dashboard/docs/`)
- **`SERVER_ARCHITECTURE_OVERVIEW.md`** - Copia del documento maestro
- **`IMPLEMENTACION_LOGGING_CENTRALIZADO.md`** ⭐
  - Implementación completa de logging estructurado
  - Configuración desde cero
  - **Útil para:** Full Stack Developer
- **`ARQUITECTURA.md`** - Arquitectura específica del proyecto

### Invoice Extractor (`invoice-extractor/docs/`)
- **`SERVER_ARCHITECTURE_OVERVIEW.md`** - Copia del documento maestro
- **`IMPLEMENTACION_LOGGING_CENTRALIZADO.md`** ⭐
  - Ajustes al sistema de logging existente
  - Eventos startup/shutdown
  - **Útil para:** Full Stack Developer

### Command Center (`infra/command-center/docs/`)
- **`SERVER_ARCHITECTURE_OVERVIEW.md`** - Copia del documento maestro
- **`ANALISIS_ARQUITECTURA_MONITOREO_LOGS.md`** ⭐
  - Análisis arquitectónico del sistema de logs
  - Diseño de solución unificada
  - **Útil para:** Arquitecto general, Full Stack Developer

### Bresca Reportes (`bresca-reportes-drive-dash/docs/`)
- **`SERVER_ARCHITECTURE_OVERVIEW.md`** - Copia del documento maestro

---

## 🎯 Documentos por Rol

### Para Arquitecto General
1. `SERVER_ARCHITECTURE_OVERVIEW.md` - Visión completa
2. `MAPA_PUERTOS.md` - Mapeo de servicios
3. `LOKI_INTEGRATION.md` - Sistema de logging
4. `COMMAND_CENTER_DASHBOARD.md` - Panel de control
5. `infra/command-center/docs/ANALISIS_ARQUITECTURA_MONITOREO_LOGS.md` - Análisis de logs

### Para Full Stack Developer
1. `SERVER_ARCHITECTURE_OVERVIEW.md` - Contexto general
2. `{proyecto}/docs/IMPLEMENTACION_LOGGING_CENTRALIZADO.md` - Especificaciones técnicas
3. `MAPA_PUERTOS.md` - URLs y puertos
4. `COMMAND_CENTER_DASHBOARD.md` - APIs disponibles

### Para Especialista de Infraestructura
1. `MAPA_PUERTOS.md` - Configuración de puertos
2. `LOKI_INTEGRATION.md` - Sistema de logging
3. `LIMPIEZA_DISCO_ACCIONES.md` - Mantenimiento
4. `SERVER_ARCHITECTURE_OVERVIEW.md` - Visión general

### Para Trading Specialist
1. `bot-trading/docs/IMPLEMENTACION_LIVE_TEST.md` - Live test
2. `bot-trading/docs/REPORTE_EJECUTIVO_IMPLEMENTACION.md` - Estado actual
3. `SERVER_ARCHITECTURE_OVERVIEW.md` - Sección Trading Bot

### Para Documentador/Custodian
1. Todos los documentos marcados con ⭐
2. `SERVER_ARCHITECTURE_OVERVIEW.md` - Documento maestro
3. Este índice para referencia

---

## 📋 Checklist de Actualización

Al realizar cambios importantes, actualizar:

- [ ] `SERVER_ARCHITECTURE_OVERVIEW.md` (raíz)
- [ ] `MAPA_PUERTOS.md` (si cambian puertos/URLs)
- [ ] Documentos específicos del proyecto afectado
- [ ] Propagar `SERVER_ARCHITECTURE_OVERVIEW.md` a todos los proyectos
- [ ] Actualizar fecha en este índice

---

## 🔄 Sincronización

Todos los documentos principales se mantienen sincronizados en:
- **Maestro:** `~/proyectos/docs/` (ubicación principal)
- **Copias en proyectos:**
  - `~/proyectos/bot-trading/docs/`
  - `~/proyectos/investment-dashboard/docs/`
  - `~/proyectos/invoice-extractor/docs/`
  - `~/proyectos/bresca-reportes-drive-dash/docs/`
  - `~/proyectos/infra/command-center/docs/`

**Nota:** Los documentos se copian a cada proyecto para que cada agente tenga acceso local sin necesidad de cambiar configuración de infraestructura.

---

## 🚀 Uso para Prompts

### Ejemplo: Prompt para Arquitecto General
```
Usa estos documentos como referencia:
- @SERVER_ARCHITECTURE_OVERVIEW.md
- @MAPA_PUERTOS.md
- @LOKI_INTEGRATION.md
- @COMMAND_CENTER_DASHBOARD.md
```

### Ejemplo: Prompt para Full Stack Developer
```
Implementa feature X usando:
- @investment-dashboard/docs/IMPLEMENTACION_LOGGING_CENTRALIZADO.md
- @SERVER_ARCHITECTURE_OVERVIEW.md (sección Investment Dashboard)
- @MAPA_PUERTOS.md
```

### Ejemplo: Prompt para Infraestructura
```
Configura servicio Y usando:
- @MAPA_PUERTOS.md
- @LOKI_INTEGRATION.md
- @SERVER_ARCHITECTURE_OVERVIEW.md (sección Traefik)
```

---

**Fin del documento**

