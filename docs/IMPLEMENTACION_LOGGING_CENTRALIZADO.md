# Implementación de Logging Centralizado - Invoice Extractor

**Proyecto:** Invoice Extractor  
**Fecha:** 2025-11-14  
**Objetivo:** Alinear logging con estándar centralizado para integración con Command Center  
**Nivel:** Técnico - Full Stack Developer

---

## 📋 Resumen Ejecutivo

Este documento especifica los cambios necesarios en **Invoice Extractor** para implementar logging centralizado normalizado. El proyecto ya tiene una base sólida con `logging_conf.py` y formato JSON, pero requiere ajustes para cumplir con el estándar unificado del Command Center.

### Estado Actual
- ✅ **Logging estructurado:** Ya implementado con `JSONFormatter`
- ✅ **Rotación de logs:** Configurada (10MB, 5 backups)
- ⚠️ **Formato:** Casi compatible, requiere ajustes menores
- ❌ **Eventos startup/shutdown:** No implementados
- ❌ **Campos estándar:** Faltan `component`, `app`, `service`

### Cambios Requeridos
1. Ajustar formato JSON para incluir campos estándar
2. Implementar eventos de startup/shutdown en FastAPI
3. Asegurar que todos los logs incluyan metadatos requeridos
4. Verificar que logs se escriban a stdout/stderr (para Docker)

---

## 🎯 Estándar de Logging Centralizado

### Formato JSON Estándar

Todos los logs deben seguir este formato:

```json
{
  "ts": "2025-11-14T10:30:00Z",           // RFC3339 UTC (REQUERIDO)
  "level": "INFO",                         // INFO, WARN, ERROR, DEBUG (REQUERIDO)
  "component": "backend",                  // backend, frontend, db (REQUERIDO)
  "app": "invoice-extractor",              // app_id (REQUERIDO)
  "service": "fastapi",                    // fastapi, uvicorn, etc. (OPCIONAL)
  "msg": "Application startup complete",   // Mensaje principal (REQUERIDO)
  "module": "main",                        // Módulo Python (OPCIONAL)
  "function": "startup_event",             // Función (OPCIONAL)
  "line": 45,                              // Línea de código (OPCIONAL)
  "request_id": "abc123",                  // ID de request (OPCIONAL)
  "trace_id": "xyz789",                    // ID de trace (OPCIONAL)
  "elapsed_ms": 150,                       // Tiempo transcurrido (OPCIONAL)
  "drive_file_id": "file123",              // Campos específicos de dominio (OPCIONAL)
  "etapa": "procesamiento"                 // Campos específicos de dominio (OPCIONAL)
}
```

### Campos Requeridos vs Opcionales

| Campo | Requerido | Descripción | Ejemplo |
|-------|-----------|-------------|---------|
| `ts` | ✅ | Timestamp RFC3339 UTC | `"2025-11-14T10:30:00Z"` |
| `level` | ✅ | Nivel de log normalizado | `"INFO"`, `"WARN"`, `"ERROR"`, `"DEBUG"` |
| `component` | ✅ | Componente de la aplicación | `"backend"`, `"frontend"`, `"db"` |
| `app` | ✅ | Identificador de la aplicación | `"invoice-extractor"` |
| `msg` | ✅ | Mensaje principal del log | `"Application startup complete"` |
| `service` | ⚠️ | Servicio específico | `"fastapi"`, `"uvicorn"` |
| `module`, `function`, `line` | ⚠️ | Información de código | Para debugging |
| `request_id`, `trace_id` | ⚠️ | IDs de trazabilidad | Para correlación |
| Campos de dominio | ⚠️ | Específicos de Invoice Extractor | `drive_file_id`, `etapa`, etc. |

---

## 🔧 Cambios Técnicos Requeridos

### 1. Actualizar `src/logging_conf.py`

**Archivo:** `src/logging_conf.py`

**Cambios necesarios:**

```python
"""
Configuración de logging estructurado con rotación
Alineado con estándar de Command Center
"""
import logging
import logging.handlers
import json
from datetime import datetime, timezone
from pathlib import Path
import os

class JSONFormatter(logging.Formatter):
    """Formatter para logs en formato JSON - Estándar Command Center"""
    
    def __init__(self, app_id: str = "invoice-extractor", component: str = "backend"):
        super().__init__()
        self.app_id = app_id
        self.component = component
    
    def format(self, record):
        # Timestamp en RFC3339 UTC
        ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Nivel normalizado (asegurar mayúsculas)
        level = record.levelname.upper()
        if level not in ['INFO', 'WARN', 'ERROR', 'DEBUG']:
            level = 'INFO'  # Default
        
        # Estructura base requerida
        log_data = {
            'ts': ts,
            'level': level,
            'component': self.component,
            'app': self.app_id,
            'msg': record.getMessage(),
        }
        
        # Campos opcionales estándar
        if hasattr(record, 'module'):
            log_data['module'] = record.module
        if hasattr(record, 'funcName'):
            log_data['function'] = record.funcName
        if hasattr(record, 'lineno'):
            log_data['line'] = record.lineno
        
        # Service (identificar si es FastAPI, Uvicorn, etc.)
        if hasattr(record, 'name'):
            if 'uvicorn' in record.name.lower():
                log_data['service'] = 'uvicorn'
            elif 'fastapi' in record.name.lower():
                log_data['service'] = 'fastapi'
            else:
                log_data['service'] = 'python'
        
        # Request ID y Trace ID (si existen)
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'trace_id'):
            log_data['trace_id'] = record.trace_id
        
        # Campos específicos de dominio (mantener compatibilidad)
        if hasattr(record, 'drive_file_id'):
            log_data['drive_file_id'] = record.drive_file_id
        if hasattr(record, 'etapa'):
            log_data['etapa'] = record.etapa
        if hasattr(record, 'elapsed_ms'):
            log_data['elapsed_ms'] = record.elapsed_ms
        
        # Excepciones
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(
    name: str, 
    log_file: str = None, 
    level: str = 'INFO',
    app_id: str = "invoice-extractor",
    component: str = "backend"
):
    """
    Configurar logger con rotación y formato JSON estándar
    
    Args:
        name: Nombre del logger
        log_file: Ruta del archivo de log (opcional)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        app_id: Identificador de la aplicación (default: invoice-extractor)
        component: Componente (backend, frontend, db) (default: backend)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicados
    if logger.handlers:
        return logger
    
    # Formatter estándar
    formatter = JSONFormatter(app_id=app_id, component=component)
    
    # Handler para consola (stdout) - CRÍTICO para Docker logs
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo con rotación (opcional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, component: str = "backend"):
    """
    Obtener logger ya configurado con estándar Command Center
    
    Args:
        name: Nombre del logger (usualmente __name__)
        component: Componente (backend, frontend, db)
    
    Returns:
        Logger configurado
    """
    log_file = os.getenv('LOG_PATH', 'logs/extractor.log')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    app_id = os.getenv('APP_ID', 'invoice-extractor')
    
    return setup_logger(name, log_file, log_level, app_id, component)
```

**Cambios clave:**
1. ✅ Agregado `app_id` y `component` como parámetros
2. ✅ Timestamp en RFC3339 UTC con timezone
3. ✅ Nivel normalizado (asegurar mayúsculas)
4. ✅ Campo `service` automático basado en logger name
5. ✅ Mantiene compatibilidad con campos de dominio existentes

---

### 2. Implementar Eventos de Startup/Shutdown en FastAPI

**Archivo:** `src/api/main.py` o `src/main.py` (según estructura)

**Cambios necesarios:**

```python
from fastapi import FastAPI
from src.logging_conf import get_logger
import sys

# Logger con componente backend
logger = get_logger(__name__, component="backend")

app = FastAPI(
    title="Invoice Extractor API",
    description="API para extracción y procesamiento de facturas",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """
    Evento de inicio de la aplicación.
    CRÍTICO: Debe loguearse para que Command Center detecte el inicio.
    """
    logger.info(
        "Application startup complete",
        extra={
            "event": "startup",
            "service": "fastapi",
            "version": "1.0.0"
        }
    )
    logger.info(
        f"FastAPI application started on {sys.version}",
        extra={"event": "startup", "service": "fastapi"}
    )

@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento de cierre de la aplicación.
    CRÍTICO: Debe loguearse para que Command Center detecte el cierre.
    """
    logger.info(
        "Application shutdown initiated",
        extra={
            "event": "shutdown",
            "service": "fastapi"
        }
    )

# Middleware para agregar request_id a logs
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Agregar request_id al logger para este request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path
            }
        )
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response

app.add_middleware(RequestIDMiddleware)
```

**Notas importantes:**
- ✅ Los eventos `startup` y `shutdown` son **obligatorios**
- ✅ Deben loguearse con `level: "INFO"`
- ✅ Deben incluir `event: "startup"` o `event: "shutdown"` en `extra`
- ✅ El middleware de `request_id` es opcional pero recomendado

---

### 3. Actualizar Uso de Logger en Todo el Código

**Patrón recomendado:**

```python
from src.logging_conf import get_logger

logger = get_logger(__name__, component="backend")

# Log simple
logger.info("Processing invoice", extra={"invoice_id": "12345"})

# Log con contexto adicional
logger.info(
    "Invoice processed successfully",
    extra={
        "invoice_id": "12345",
        "drive_file_id": "file_abc123",
        "etapa": "extraccion",
        "elapsed_ms": 150
    }
)

# Log de error
try:
    # código
    pass
except Exception as e:
    logger.error(
        f"Error processing invoice: {str(e)}",
        extra={
            "invoice_id": "12345",
            "error_type": type(e).__name__
        },
        exc_info=True  # Incluir stack trace
    )
```

**Verificaciones:**
- ✅ Todos los módulos usan `get_logger(__name__, component="backend")`
- ✅ Logs importantes incluyen contexto en `extra`
- ✅ Errores usan `exc_info=True` para stack traces

---

### 4. Configuración de Uvicorn para Logging

**Archivo:** `Dockerfile.backend` o script de inicio

**Asegurar que Uvicorn loguee a stdout:**

```python
# En el punto de entrada (main.py o run.py):
import uvicorn
import logging

# Configurar logging de Uvicorn para que use nuestro formatter
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.handlers = []  # Limpiar handlers por defecto
uvicorn_logger.addHandler(logging.StreamHandler())

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",  # Ajustar según estructura
        host="0.0.0.0",
        port=8002,
        log_config=None,  # Deshabilitar config por defecto
        access_log=True,  # Mantener access logs
        use_colors=False  # Sin colores en logs (mejor para JSON)
    )
```

**O en docker-compose.yml:**

```yaml
invoice-backend:
  # ...
  command: uvicorn src.api.main:app --host 0.0.0.0 --port 8002 --log-config /dev/null --access-log
```

---

## ✅ Checklist de Implementación

### Fase 1: Configuración Base
- [ ] Actualizar `src/logging_conf.py` con nuevo formato
- [ ] Verificar que `JSONFormatter` incluye todos los campos requeridos
- [ ] Probar que logs se escriben a stdout (para Docker)

### Fase 2: Eventos de Aplicación
- [ ] Implementar `@app.on_event("startup")` en FastAPI
- [ ] Implementar `@app.on_event("shutdown")` en FastAPI
- [ ] Verificar que eventos se loguean correctamente

### Fase 3: Middleware y Request ID
- [ ] Implementar `RequestIDMiddleware` (opcional pero recomendado)
- [ ] Agregar middleware a FastAPI app
- [ ] Verificar que `request_id` aparece en logs

### Fase 4: Actualización de Código Existente
- [ ] Revisar todos los módulos que usan logging
- [ ] Actualizar llamadas a `get_logger()` con `component="backend"`
- [ ] Agregar contexto en `extra` donde sea relevante

### Fase 5: Testing y Validación
- [ ] Verificar formato JSON de logs generados
- [ ] Probar startup/shutdown y verificar logs en Command Center
- [ ] Validar que Docker logs capturan todos los eventos
- [ ] Verificar parsing en Command Center (`/api/logs/invoice-extractor`)

---

## 🧪 Testing

### Test 1: Formato de Log

```python
# test_logging_format.py
from src.logging_conf import get_logger
import json

logger = get_logger(__name__, component="backend")

# Generar log de prueba
logger.info("Test log message", extra={"test_field": "test_value"})

# Capturar output (en producción, esto va a stdout)
# Verificar que el JSON tiene:
# - ts (RFC3339 UTC)
# - level (INFO, WARN, ERROR, DEBUG)
# - component ("backend")
# - app ("invoice-extractor")
# - msg ("Test log message")
```

### Test 2: Startup/Shutdown

```bash
# Iniciar aplicación
docker-compose up invoice-backend

# Verificar logs de startup
docker logs invoice-backend | grep -i "startup"

# Debe aparecer:
# {"ts":"2025-11-14T10:30:00Z","level":"INFO","component":"backend","app":"invoice-extractor","msg":"Application startup complete",...}

# Detener aplicación
docker-compose stop invoice-backend

# Verificar logs de shutdown
docker logs invoice-backend | grep -i "shutdown"
```

### Test 3: Integración con Command Center

```bash
# Desde Command Center, verificar endpoint:
curl http://localhost:8001/api/logs/invoice-extractor?lines=20

# Debe retornar logs normalizados con formato estándar
```

---

## 📝 Notas Adicionales

### Frontend (React)
- El frontend de Invoice Extractor no genera logs de servidor
- Los logs del contenedor `invoice-frontend` mostrarán logs de `serve` (servidor HTTP)
- Si se necesita logging del frontend, considerar enviar eventos al backend vía API

### Base de Datos
- Los logs de PostgreSQL se capturan desde Docker logs del contenedor `postgres`
- No requiere cambios en Invoice Extractor

### Variables de Entorno

Agregar a `.env`:

```bash
# Logging
LOG_LEVEL=INFO
LOG_PATH=logs/extractor.log
APP_ID=invoice-extractor
```

---

## 🚀 Próximos Pasos

1. **Implementar cambios** según este documento
2. **Probar localmente** antes de desplegar
3. **Verificar en Command Center** que logs aparecen correctamente
4. **Documentar** cualquier desviación del estándar si es necesaria

---

**Fin del documento**


