# 🔍 DIAGNÓSTICO TÉCNICO: Puertos y APIs

**Fecha:** 10 de noviembre de 2025

---

## 📊 RESUMEN EJECUTIVO

Investigación exhaustiva de puertos, rutas de APIs y logs. Se identificaron **múltiples APIs corriendo** y **conflicto de puertos**.

---

## 🔍 HALLAZGOS TÉCNICOS

### Procesos uvicorn Activos

| PID | Usuario | Puerto | Comando | Tiempo Activo | CWD |
|-----|---------|--------|---------|---------------|-----|
| **3981462** | root | **8001** | `uvicorn src.api.main:app` | 7:07 | ? |
| **3910217** | alex | **8003** | `uvicorn src.api.main:app` | 1:01:49 | `/home/alex/proyectos/invoice-extractor` |
| **401435** | root | **8002** | `uvicorn src.api.main:app` | 2d 22:35 | ? |
| **3971208** | root | **8000** | `uvicorn app.main:app` | 11:10 | ? |

---

### Estado de Puertos

#### Puerto 8000
- **Estado:** No responde a HTTP
- **Proceso:** `app.main:app` (diferente API)
- **Rutas facturas:** ❌ No tiene

#### Puerto 8001
- **Estado:** ✅ Health OK (`{"status":"ok"}`)
- **Proceso:** `src.api.main:app` (root, PID 3981462)
- **OpenAPI:** ❌ No responde
- **Endpoint `/api/facturas/failed`:** ❌ `{"detail": "Not Found"}`
- **Rutas facturas:** ❌ 0 rutas
- **Problema:** API diferente o código desactualizado

#### Puerto 8002
- **Estado:** ✅ Health OK (`{"status":"ok"}`)
- **Proceso:** `src.api.main:app` (root, PID 401435)
- **OpenAPI:** ❌ No responde
- **Endpoint `/api/facturas/failed`:** ⚠️ `{"data": []}` (endpoint existe pero sin datos)
- **Rutas facturas:** ⚠️ Endpoint existe pero no devuelve datos

#### Puerto 8003
- **Estado:** ✅ Health OK (`{"status":"ok"}`)
- **Proceso:** `src.api.main:app` (alex, PID 3910217)
- **OpenAPI:** ❌ No responde (pero endpoint funciona)
- **Endpoint `/api/facturas/failed`:** ✅ Funciona correctamente
- **Resultado:** Enero 2024 → 1 factura, Julio 2025 → 4 facturas
- **CWD:** `/home/alex/proyectos/invoice-extractor` ✅

---

## ⚠️ PROBLEMAS IDENTIFICADOS

### Problema 1: Múltiples APIs Corriendo

**Hay 3 instancias de `src.api.main:app` corriendo:**
- Puerto 8001 (root) - NO tiene rutas de facturas
- Puerto 8002 (root) - Tiene endpoint pero devuelve `[]`
- Puerto 8003 (alex) - ✅ Funciona correctamente

**Causa:** Procesos iniciados en diferentes momentos, posiblemente desde diferentes directorios o con código diferente.

### Problema 2: OpenAPI No Responde

**Ningún puerto responde a `/openapi.json`:**
- Esto sugiere que los APIs pueden estar usando código antiguo o configuración diferente
- El puerto 8003 funciona pero no expone OpenAPI

### Problema 3: Frontend Puede Estar Apuntando al Puerto Incorrecto

**Build del frontend:**
- ✅ Contiene `http://localhost:8003/api` (correcto)
- ✅ Build actualizado: 10 de noviembre de 2025, 14:14

**Pero:** Si el frontend está usando un servidor de desarrollo (`npm run dev`), puede estar usando configuración diferente o caché.

---

## 🔧 ANÁLISIS TÉCNICO

### Proceso Correcto (Puerto 8003)

- **PID:** 3910217
- **Usuario:** alex
- **CWD:** `/home/alex/proyectos/invoice-extractor` ✅
- **Comando:** `python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8003`
- **Estado:** ✅ Funcionando correctamente
- **Endpoint:** ✅ Devuelve datos

### Procesos Problemáticos

**Puerto 8001 (PID 3981462):**
- Usuario: root
- CWD: Desconocido (probablemente diferente)
- Estado: Health OK pero NO tiene rutas de facturas
- **Conclusión:** Probablemente usando código antiguo o diferente directorio

**Puerto 8002 (PID 401435):**
- Usuario: root
- CWD: Desconocido
- Estado: Endpoint existe pero devuelve `[]`
- **Conclusión:** Puede estar usando BD diferente o código desactualizado

---

## 📋 CONCLUSIÓN TÉCNICA

### Estado Real

1. ✅ **API correcto:** Puerto 8003 (PID 3910217) - Funciona perfectamente
2. ❌ **APIs incorrectos:** Puertos 8001 y 8002 - No funcionan o tienen código antiguo
3. ✅ **Frontend build:** Configurado para puerto 8003 (correcto)

### Problema Probable

**El frontend puede estar:**
1. **Usando servidor de desarrollo** que no recargó la configuración
2. **Cacheado** con URL antigua (puerto 8001)
3. **Sirviendo build antiguo** desde otro servidor web

### Solución Recomendada

1. **Verificar qué servidor está sirviendo el frontend:**
   - ¿Es `npm run dev` (puerto 5173)?
   - ¿Es un servidor web (nginx/apache)?
   - ¿Es el build de producción?

2. **Limpiar caché del navegador completamente**

3. **Verificar que el frontend esté usando el build nuevo**

---

*Diagnóstico técnico completado el 10 de noviembre de 2025*

