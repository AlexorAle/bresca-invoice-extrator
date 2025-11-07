"""
API REST principal para el dashboard de facturas
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

from src.api.routes import facturas, system
from src.logging_conf import get_logger

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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https?://82\.25\.101\.32(:.*)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(facturas.router, prefix="/api")
app.include_router(system.router, prefix="/api")


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
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

