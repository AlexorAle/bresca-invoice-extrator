"""
Rutas de autenticación con Google OAuth
Verifica tokens de Google y gestiona sesiones seguras
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google.auth.transport import requests
from google.oauth2 import id_token
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from src.logging_conf import get_logger

# Cargar .env si existe (por si se importa antes de que main.py lo cargue)
env_path = Path(__file__).parents[3] / '.env'
if env_path.exists():
    load_dotenv(env_path)

logger = get_logger(__name__, component="auth")

# Client ID de Google OAuth
GOOGLE_CLIENT_ID = "871033191224-40qifv1fp6ovn9kuk0b998e3ubl695ni.apps.googleusercontent.com"

# Cargar whitelist desde variable de entorno (obligatoria)
_raw_allowed = os.getenv("ALLOWED_EMAILS", "").strip()
if not _raw_allowed:
    raise RuntimeError(
        "Variable de entorno ALLOWED_EMAILS no configurada. "
        "Debe contener emails separados por coma."
    )

ALLOWED_EMAILS = {email.strip().lower() for email in _raw_allowed.split(",") if email.strip()}

if not ALLOWED_EMAILS:
    raise RuntimeError("ALLOWED_EMAILS está vacía después de procesar.")

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleTokenRequest(BaseModel):
    """Request body para autenticación con Google"""
    token: str


class UserResponse(BaseModel):
    """Response con información del usuario autenticado"""
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None


def get_session_user(request: Request) -> Optional[dict]:
    """
    Obtiene el usuario de la sesión si existe
    
    Returns:
        dict con información del usuario o None si no hay sesión
    """
    session = request.session
    return session.get('user')


def require_auth(request: Request) -> dict:
    """
    Dependency que requiere autenticación
    Lanza HTTPException 401 si no hay usuario en sesión
    
    Returns:
        dict con información del usuario autenticado
    """
    user = get_session_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="No autenticado. Por favor, inicia sesión."
        )
    return user


@router.post("/google", response_model=UserResponse)
async def google_login(
    token_request: GoogleTokenRequest,
    request: Request,
    response: Response
):
    """
    Endpoint para autenticación con Google OAuth
    
    Verifica el ID token de Google, valida el email contra la whitelist,
    y crea una sesión segura si el usuario está autorizado.
    """
    try:
        # Verificar el token de Google
        idinfo = id_token.verify_oauth2_token(
            token_request.token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Extraer email y normalizarlo a lowercase
        email = idinfo.get('email', '').lower()
        
        if not email:
            logger.warning("Token de Google sin email")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El token de Google no contiene un email válido"
            )
        
        # Verificar que el email esté verificado por Google y esté en la whitelist
        if idinfo.get("email_verified") is not True or email not in ALLOWED_EMAILS:
            logger.warning(f"Intento de login con email no autorizado o no verificado: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Acceso no autorizado: email no permitido"
            )
        
        # Crear sesión segura
        user_data = {
            'email': email,
            'name': idinfo.get('name'),
            'picture': idinfo.get('picture'),
        }
        
        # Guardar en sesión
        request.session['user'] = user_data
        
        logger.info(
            f"Login exitoso para {email}",
            extra={"email": email, "component": "auth"}
        )
        
        return UserResponse(**user_data)
        
    except ValueError as e:
        # Token inválido
        logger.warning(f"Token de Google inválido: {e}")
        raise HTTPException(
            status_code=401,
            detail="Token de Google inválido"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en autenticación: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor durante la autenticación"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request):
    """
    Endpoint para verificar la sesión actual
    
    Returns:
        Información del usuario si hay sesión activa
        401 si no hay sesión
    """
    user = get_session_user(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="No hay sesión activa"
        )
    
    return UserResponse(**user)


@router.get("/check")
async def check_auth(request: Request):
    """
    Endpoint simple para verificar autenticación (usado por middleware)
    
    Returns:
        200 si autenticado, 401 si no
    """
    user = get_session_user(request)
    
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    return {"authenticated": True}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Endpoint para cerrar sesión
    
    Elimina la sesión del usuario
    """
    user = get_session_user(request)
    
    if user:
        email = user.get('email', 'unknown')
        logger.info(f"Logout para {email}", extra={"email": email, "component": "auth"})
    
    # Limpiar sesión
    request.session.clear()
    
    return {"message": "Sesión cerrada exitosamente"}
