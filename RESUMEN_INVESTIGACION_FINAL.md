# 📋 RESUMEN INVESTIGACIÓN EXHAUSTIVA: Puertos y Rutas

**Fecha:** 10 de noviembre de 2025

---

## 🎯 OBJETIVO CUMPLIDO

Verificación exhaustiva realizada para evitar conflictos con otros proyectos y asegurar funcionamiento correcto.

---

## 📊 HALLAZGOS CRÍTICOS

### Mapeo de Puertos por Aplicación

| Puerto | Aplicación | PID | Usuario | Estado | Notas |
|--------|------------|-----|---------|--------|-------|
| **8000** | Investment Dashboard | 3971208 | root | ✅ OK | `app.main:app` - NO es Invoice |
| **8001** | Command Center Backend | - | - | ✅ OK | Docker container - NO es Invoice |
| **8002** | Invoice Extractor | 401435 | root | ⚠️ Sin datos | Responde pero `{"data": []}` |
| **8003** | Invoice Extractor | 3910217 | alex | ✅ Funciona | Devuelve datos correctamente |
| **8080** | Trading Bot | - | - | ✅ OK | Docker container - NO es Invoice |

### Verificación de Endpoints

#### Puerto 8003 (FUNCIONA CORRECTAMENTE) ✅

- ✅ `/api/facturas/failed` → Devuelve 1 factura para Enero 2024
- ✅ `/api/facturas/summary` → Devuelve datos correctos
- ✅ `/api/facturas/list` → Devuelve lista de facturas
- ✅ CWD: `/home/alex/proyectos/invoice-extractor` (correcto)
- ✅ BD: `negocio_db` (correcto)

#### Puerto 8002 (CONFIGURADO EN TRAEFIK) ⚠️

- ⚠️ `/api/facturas/failed` → `{"data": []}` (sin datos)
- ⚠️ `/api/facturas/summary` → Verificando...
- ❌ CWD: No accesible (probablemente iniciado desde otro directorio)
- ❓ BD: No verificable (puede estar usando BD diferente)

### Configuración Traefik

**Archivo:** `/home/alex/proyectos/infra/traefik/config/invoice-api.yml`

**Configuración actual:**
```yaml
servers:
  - url: "http://172.17.0.1:8002"  # ← Apunta a puerto 8002 (sin datos)
```

**Rutas:**
- Frontend llama a: `/invoice-api/api/facturas/*`
- Traefik strip prefix: `/invoice-api`
- Traefik envía a: `http://172.17.0.1:8002/api/facturas/*`

### Puertos Disponibles

- ✅ 8004, 8005, 8006, 8007, 8008, 8009: **DISPONIBLES**

---

## ⚠️ PROBLEMA IDENTIFICADO

**El proceso en puerto 8002 (configurado en Traefik) NO devuelve datos, mientras que el puerto 8003 funciona perfectamente.**

**Evidencia:**
1. Puerto 8002: `{"data": []}` (sin datos)
2. Puerto 8003: `{"data": [{"nombre": "Factura GLOVO 1 Enero 2024.pdf"}]}` (con datos)
3. Puerto 8003 está en directorio correcto: `/home/alex/proyectos/invoice-extractor`
4. Puerto 8002 no tiene CWD accesible (probablemente código antiguo)

---

## ✅ SOLUCIÓN RECOMENDADA

### Opción 1: Actualizar Traefik para usar Puerto 8003 (RECOMENDADO)

**Ventajas:**
- ✅ Puerto 8003 ya funciona correctamente
- ✅ Ambos endpoints (procesadas y no procesadas) funcionan
- ✅ No requiere reiniciar procesos
- ✅ Cambio mínimo en configuración
- ✅ No interfiere con otros proyectos

**Acción:**
1. Modificar `/home/alex/proyectos/infra/traefik/config/invoice-api.yml`:
   ```yaml
   servers:
     - url: "http://172.17.0.1:8003"  # Cambiar de 8002 a 8003
   ```
2. Recargar Traefik: `docker restart traefik`

### Opción 2: Reiniciar Proceso 8002 desde Directorio Correcto

**Ventajas:**
- Mantiene configuración actual de Traefik

**Desventajas:**
- Requiere detener proceso root (puede requerir sudo)
- Requiere reiniciar proceso

**Acción:**
1. Detener proceso 8002: `sudo kill 401435`
2. Iniciar desde directorio correcto:
   ```bash
   cd /home/alex/proyectos/invoice-extractor
   source venv/bin/activate
   nohup python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002 > /tmp/api_8002.log 2>&1 &
   ```

---

## 📊 VERIFICACIÓN DE SEGURIDAD

### ✅ No hay Conflictos con Otros Proyectos

- ✅ Puerto 8000: Investment Dashboard (diferente aplicación)
- ✅ Puerto 8001: Command Center Backend (Docker, diferente aplicación)
- ✅ Puerto 8080: Trading Bot (Docker, diferente aplicación)
- ✅ Puerto 8003: Invoice Extractor (nuestro proyecto, funciona correctamente)

### ✅ Endpoints Verificados

**Puerto 8003 (funciona):**
- ✅ `/api/facturas/failed` → Devuelve facturas no procesadas
- ✅ `/api/facturas/summary` → Devuelve resumen de facturas procesadas
- ✅ `/api/facturas/list` → Devuelve lista completa

---

## 🎯 CONCLUSIÓN

**Recomendación:** Usar **Opción 1** - Actualizar Traefik para apuntar al puerto 8003.

**Razones:**
1. Puerto 8003 funciona correctamente con ambos endpoints
2. No interfiere con otros proyectos
3. Cambio mínimo y seguro
4. No requiere reiniciar procesos root

---

*Investigación completada el 10 de noviembre de 2025*

