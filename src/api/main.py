"""
API REST principal para el dashboard de facturas
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os
import sys
import uuid

# Cargar variables de entorno PRIMERO (antes de importar rutas que las necesitan)
load_dotenv()

# Importar rutas después de cargar .env
from src.api.routes import facturas, system, proveedores, categorias, ingresos, auth, costos_personal
from src.logging_conf import get_logger

# Logger
logger = get_logger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Invoice Extractor API",
    description="API REST para el dashboard de facturas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
# Nota: El origen en CORS es solo protocolo + dominio + puerto, no incluye la ruta
cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://82.25.101.32",
    "https://82.25.101.32",
    "https://alexforge.online",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://(82\.25\.101\.32|alexforge\.online)(:.*)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para agregar request_id a logs
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

# Configurar sesiones (debe ir después de CORS pero antes de otros middlewares)
# Usar clave secreta desde variable de entorno (obligatoria en producción)
SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY')
if not SESSION_SECRET_KEY:
    logger.warning(
        "SESSION_SECRET_KEY no configurada. Usando clave por defecto insegura. "
        "Configurar en producción."
    )
    SESSION_SECRET_KEY = 'change-this-secret-key-in-production-use-env-var'

# Determinar si estamos en producción (HTTPS)
# En producción, ajustar según tu configuración
IS_PRODUCTION = os.getenv('ENVIRONMENT', '').lower() == 'production'
IS_HTTPS_ONLY = os.getenv('HTTPS_ONLY', 'false').lower() == 'true'

# Middleware de autenticación para proteger rutas
class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware para proteger rutas que requieren autenticación"""
    
    # Rutas públicas que no requieren autenticación (sin prefijo /api/)
    PUBLIC_PATHS = {
        '/',
        '/healthz',
        '/docs',
        '/redoc',
        '/openapi.json',
    }
    
    # Rutas de API públicas (no requieren autenticación)
    PUBLIC_API_PATHS = {
        '/api/auth/google',
        '/api/auth/me',
        '/api/auth/logout',
        '/api/auth/check',
        '/api/system/sync-status',  # Endpoint de estado de sincronización (usado por dashboard)
        '/api/system/data-load-stats',  # Estadísticas de carga (usado por dashboard)
    }
    
    async def dispatch(self, request, call_next):
        # Verificar si la ruta es pública
        path = request.url.path
        
        # Permitir rutas públicas (sin /api/) - estas no pasan por el middleware de auth
        if path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Permitir rutas de API públicas (autenticación)
        if path in self.PUBLIC_API_PATHS or path.startswith('/api/auth/'):
            return await call_next(request)
        
        # Para todas las demás rutas de /api, verificar autenticación
        if path.startswith('/api/'):
            # Verificar que session esté disponible (SessionMiddleware debe estar activo)
            if not hasattr(request, 'session'):
                logger.error("SessionMiddleware no está activo - request.session no disponible")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Error de configuración del servidor"}
                )
            
            user = request.session.get('user')
            if not user:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "No autenticado. Por favor, inicia sesión."}
                )
        
        return await call_next(request)

# IMPORTANTE: En FastAPI, los middlewares se ejecutan en orden INVERSO
# (el último agregado se ejecuta PRIMERO)
# Por lo tanto:
# 1. AuthMiddleware se agrega PRIMERO → se ejecuta ÚLTIMO
# 2. SessionMiddleware se agrega DESPUÉS → se ejecuta PRIMERO
# Esto asegura que SessionMiddleware configure request.session antes de que AuthMiddleware lo use
app.add_middleware(AuthMiddleware)

# SessionMiddleware debe ejecutarse ANTES de AuthMiddleware
# Por eso se agrega DESPUÉS (para ejecutarse PRIMERO)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    max_age=86400,  # 24 horas
    same_site='lax' if not IS_PRODUCTION else 'strict',  # Strict en producción
    https_only=IS_HTTPS_ONLY,  # True si solo usas HTTPS
)

# Incluir routers
app.include_router(auth.router, prefix="/api")
app.include_router(facturas.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(proveedores.router, prefix="/api")
app.include_router(categorias.router, prefix="/api")
app.include_router(ingresos.router, prefix="/api/ingresos")
app.include_router(costos_personal.router, prefix="/api/costos-personal")


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


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Invoice Extractor API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    request_id = getattr(request.state, 'request_id', None)
    logger.error(
        f"Error no manejado: {exc}",
        extra={"request_id": request_id} if request_id else {},
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

