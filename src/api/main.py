"""
API REST principal para el dashboard de facturas
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
import os
import sys
import uuid

# Cargar variables de entorno
load_dotenv()

from src.api.routes import facturas, system
from src.logging_conf import get_logger

# Logger con componente backend
logger = get_logger(__name__, component="backend")

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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://82\.25\.101\.32(:.*)?",
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

# Incluir routers
app.include_router(facturas.router, prefix="/api")
app.include_router(system.router, prefix="/api")


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

