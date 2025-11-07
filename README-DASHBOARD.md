# Dashboard de Facturación - Guía de Inicio Rápido

## 🚀 Inicio Rápido

### Backend (API FastAPI)

**Opción 1: Usando el script (recomendado)**
```bash
./start-api.sh
```

**Opción 2: Manual**
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar API
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Endpoints disponibles:**
- API: http://localhost:8000/api
- Documentación Swagger: http://localhost:8000/docs
- Health Check: http://localhost:8000/healthz

### Frontend (React)

```bash
cd frontend

# Instalar dependencias (solo la primera vez)
npm install

# Ejecutar en desarrollo
npm run dev
```

**Frontend disponible en:** http://localhost:5173

---

## 📋 Verificación

### 1. Verificar que el backend funciona

```bash
curl http://localhost:8000/healthz
# Debe retornar: {"status":"ok"}
```

### 2. Verificar endpoints

Abre en el navegador: http://localhost:8000/docs

Deberías ver la documentación interactiva de Swagger con todos los endpoints.

### 3. Verificar frontend

Abre en el navegador: http://localhost:5173

Deberías ver el dashboard con:
- Header con selector de mes
- 4 KPIs
- Gráficos interactivos
- Paneles de análisis

---

## ⚠️ Solución de Problemas

### Error: "externally-managed-environment"

**Solución:** Siempre usar el entorno virtual:
```bash
source venv/bin/activate
```

### Error: "ModuleNotFoundError: No module named 'fastapi'"

**Solución:** Instalar dependencias en el entorno virtual:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Cannot connect to API"

**Verificar:**
1. Backend está corriendo en puerto 8000
2. Variable `VITE_API_BASE_URL` en `frontend/.env` apunta a `http://localhost:8000/api`
3. CORS está configurado correctamente

### Error: "No data available"

**Verificar:**
1. Hay facturas en la base de datos para el mes seleccionado
2. Las facturas tienen `fecha_emision` correcta
3. La conexión a la base de datos funciona

---

## 📚 Documentación Completa

- **Informe Ejecutivo**: `docs/informe-ejecutivo-dashboard.md`
- **Detalles Técnicos**: `docs/detalles-tecnicos-dashboard.md`
- **Resumen de Implementación**: `docs/resumen-dashboard-react.md`

---

## 🎯 Próximos Pasos

1. ✅ Instalar dependencias (completado)
2. ✅ Ejecutar backend
3. ✅ Ejecutar frontend
4. ✅ Verificar funcionamiento
5. 🔄 Personalizar según necesidades

---

**Nota:** Asegúrate de tener la base de datos PostgreSQL configurada y con datos antes de usar el dashboard.

