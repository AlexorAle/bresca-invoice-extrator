# Implementación de Autenticación con Google Sign-In

## 📋 Resumen

Se ha implementado autenticación segura con Google Sign-In usando `@react-oauth/google` en el frontend y verificación de tokens en el backend FastAPI. Solo 3 usuarios específicos pueden acceder mediante whitelist de emails.

## ✅ Componentes Implementados

### Frontend (React)

1. **GoogleOAuthProvider** configurado en `main.jsx`
   - Client ID: `871033191224-40qifv1fp6ovn9kuk0b998e3ubl695ni.apps.googleusercontent.com`

2. **LoginPage.jsx** - Página de login con botón de Google
   - Usa `GoogleLogin` de `@react-oauth/google`
   - Envía token al backend en `/invoice-api/api/auth/google`
   - Diseño centrado con MUI

3. **AuthContext.jsx** - Contexto de autenticación
   - Verifica sesión con `/api/auth/me`
   - Maneja estado de autenticación
   - Proporciona `useAuth()` hook

4. **App.jsx** - Protección de rutas
   - Muestra `LoginPage` si no está autenticado
   - Muestra `AdminApp` si está autenticado

5. **authProvider.js** - Actualizado para React-admin
   - `checkAuth()` verifica sesión con backend
   - `logout()` cierra sesión y recarga página

### Backend (FastAPI)

1. **src/api/routes/auth.py** - Rutas de autenticación
   - `POST /api/auth/google` - Verifica token y crea sesión
   - `GET /api/auth/me` - Verifica sesión actual
   - `POST /api/auth/logout` - Cierra sesión

2. **src/api/main.py** - Configuración de sesiones
   - `SessionMiddleware` configurado con cookies HTTP-only
   - `AuthMiddleware` protege todas las rutas `/api/*` excepto `/api/auth/*`
   - CORS actualizado para incluir `alexforge.online`

3. **Whitelist de emails** - Configurada mediante variable de entorno `ALLOWED_EMAILS`
   - Los emails se cargan desde variable de entorno (obligatoria)
   - Se normalizan a lowercase y se triman automáticamente
   - Formato: emails separados por coma
   - Ejemplo: `ALLOWED_EMAILS=usuario1@gmail.com,usuario2@empresa.com,admin@cliente.com`

## 🔒 Seguridad

- ✅ Cookies HTTP-only (no accesibles desde JavaScript)
- ✅ Cookies firmadas con clave secreta
- ✅ Verificación de tokens de Google en el backend
- ✅ Whitelist de emails en el backend
- ✅ Middleware protege todas las rutas del dashboard
- ✅ SameSite=Lax para cookies (ajustable a Strict en producción)

## 📦 Dependencias

### Frontend
- `@react-oauth/google` - Agregado a `package.json`

### Backend
- `itsdangerous==2.1.2` - Para cookies firmadas
- `starlette-sessions==0.2.0` - Para manejo de sesiones
- `google-auth` - Ya estaba en requirements.txt

## 🚀 Próximos Pasos

1. **Instalar dependencias del frontend:**
   ```bash
   cd frontend
   npm install
   ```

2. **Instalar dependencias del backend:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno (OBLIGATORIO):**
   
   Crear archivo `.env` en la raíz del proyecto (nunca subir a Git):
   ```bash
   # Clave secreta para firmar cookies (generar con: openssl rand -hex 32)
   SESSION_SECRET_KEY=tu-clave-secreta-fuerte-minimo-32-caracteres-aqui
   
   # Emails autorizados separados por coma (sin espacios, o se triman automáticamente)
   ALLOWED_EMAILS=usuario1@gmail.com,usuario2@empresa.com,admin@cliente.com
   ```
   
   **Generar clave secreta segura:**
   ```bash
   openssl rand -hex 32
   ```

4. **En producción, configurar variables de entorno:**
   - En el panel de tu proveedor (Vercel, Railway, AWS, etc.)
   - Configurar `SESSION_SECRET_KEY` y `ALLOWED_EMAILS`
   - **NUNCA** subir estas variables a Git

5. **Configuración adicional de producción (opcional):**
   ```bash
   # En .env de producción
   ENVIRONMENT=production
   HTTPS_ONLY=true  # Si solo usas HTTPS
   ```

## 🔧 Configuración de Producción

### Variables de Entorno Requeridas

**OBLIGATORIAS:**
```bash
# Clave secreta para firmar cookies (generar con: openssl rand -hex 32)
SESSION_SECRET_KEY=clave-secreta-fuerte-minimo-32-caracteres

# Emails autorizados separados por coma
ALLOWED_EMAILS=usuario1@gmail.com,usuario2@empresa.com,admin@cliente.com
```

**OPCIONALES (para configuración avanzada):**
```bash
# Activar modo producción (usa same_site='strict' y configuración más segura)
ENVIRONMENT=production

# Forzar solo HTTPS para cookies
HTTPS_ONLY=true
```

### Configuración Automática de Cookies

El sistema detecta automáticamente el entorno:
- **Desarrollo**: `same_site='lax'`, `https_only=False`
- **Producción** (con `ENVIRONMENT=production`): `same_site='strict'`, `https_only` según `HTTPS_ONLY`

### Generar Clave Secreta Segura

```bash
# Generar clave de 64 caracteres hexadecimales
openssl rand -hex 32

# O usar Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## 📝 Notas Importantes

- ✅ **ALLOWED_EMAILS** ahora se carga desde variable de entorno (obligatoria)
- ✅ **SESSION_SECRET_KEY** debe configurarse en `.env` (obligatoria en producción)
- ⚠️ El Client ID de Google está hardcodeado en el código. En producción, considerar moverlo a variables de entorno.
- ✅ Los emails se normalizan automáticamente a lowercase y se triman
- ✅ Se verifica que `email_verified` sea `True` antes de permitir acceso
- Las cookies tienen `max_age=86400` (24 horas). Ajustar según necesidad.
- El middleware de autenticación permite acceso a `/api/auth/*` sin autenticación.
- **NUNCA** subir `.env` a Git. Ya está en `.gitignore`.

## 🐛 Troubleshooting

### Error: "Variable de entorno ALLOWED_EMAILS no configurada"
- **Solución**: Crear archivo `.env` en la raíz del proyecto con:
  ```bash
  ALLOWED_EMAILS=tu-email@gmail.com,otro-email@empresa.com
  ```
- Verificar que el archivo `.env` esté en la raíz del proyecto (mismo nivel que `requirements.txt`)

### Error: "ALLOWED_EMAILS está vacía después de procesar"
- **Solución**: Verificar que la variable contenga emails válidos separados por coma
- Ejemplo correcto: `ALLOWED_EMAILS=email1@gmail.com,email2@gmail.com`
- Ejemplo incorrecto: `ALLOWED_EMAILS=  ` (solo espacios)

### Error: "Email no autorizado"
- Verificar que el email esté en la variable de entorno `ALLOWED_EMAILS`
- El email se normaliza a lowercase automáticamente
- Verificar que el email esté verificado por Google (`email_verified=True`)
- Revisar logs del backend para ver qué email intentó acceder

### Error: "Token de Google inválido"
- Verificar que el Client ID sea correcto
- Verificar que el token no haya expirado
- Verificar que el token sea válido y no haya sido revocado

### Las cookies no se guardan
- Verificar que `allow_credentials=True` en CORS
- Verificar que el origen esté en `cors_origins`
- En desarrollo, usar `http://localhost` (no `127.0.0.1`)
- Verificar que `SESSION_SECRET_KEY` esté configurada

### 401 en todas las rutas después de login
- Verificar que `SessionMiddleware` esté configurado correctamente
- Verificar que `SESSION_SECRET_KEY` esté definida en `.env`
- Verificar que el backend haya cargado las variables de entorno
- Revisar logs del backend para errores de sesión
- Verificar que las cookies se estén enviando en las peticiones (DevTools → Network → Headers)

### Error al iniciar el backend: "RuntimeError: ALLOWED_EMAILS..."
- **Solución**: Configurar la variable de entorno `ALLOWED_EMAILS` en `.env`
- El sistema falla rápido si no está configurada (comportamiento esperado)
