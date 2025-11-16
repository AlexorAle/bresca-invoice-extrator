# 🔍 ANÁLISIS DETALLADO: Backend Puerto 8002

**Fecha:** 10 de noviembre de 2025

---

## 📊 HALLAZGOS

### Proceso 8002 (PID 401435)

- **Usuario:** root
- **Comando:** `/usr/local/bin/python3.11 /usr/local/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8002`
- **Estado:** ✅ Corriendo
- **CWD:** Verificando...

### Verificaciones Realizadas

1. **Health Check:**
   - `http://localhost:8002/healthz` → ✅ Responde `{"status":"ok"}`

2. **Endpoint `/api/facturas/failed`:**
   - `http://localhost:8002/api/facturas/failed` → Verificando respuesta

3. **A través de Traefik:**
   - `http://82.25.101.32/invoice-api/api/facturas/failed` → Verificando

4. **Gateway Docker:**
   - `http://172.17.0.1:8002/api/facturas/failed` → Verificando

### Comparación con Puerto 8003

- **Puerto 8003 (PID 3910217):**
  - ✅ Funciona correctamente
  - ✅ Devuelve datos: Enero 2024 → 1 factura
  - ⚠️ No está configurado en Traefik

---

*Análisis en progreso...*

