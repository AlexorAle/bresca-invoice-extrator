#!/bin/bash
# Script maestro de instalación para Invoice Extractor
# Versión: 1.0
# Idempotente: se puede ejecutar múltiples veces sin problemas

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="${PWD}"
LOG_FILE="${PROJECT_DIR}/infra/setup.log"
USER_NAME="${USER:-alex}"
PROJECT_USER="${USER_NAME}"

# Función de logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
    echo -e "${GREEN}✓${NC} $*"
}

log_warn() {
    log "WARN" "$@"
    echo -e "${YELLOW}⚠${NC} $*"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}✗${NC} $*" >&2
}

# Función para verificar comandos
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# Función para verificar si es root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Este script NO debe ejecutarse como root. Ejecuta como usuario normal con sudo."
        exit 1
    fi
}

# ============================================
# A. VALIDACIONES INICIALES
# ============================================
log_info "============================================"
log_info "INICIO DE SETUP - Invoice Extractor"
log_info "============================================"
log_info "Directorio del proyecto: $PROJECT_DIR"
log_info "Usuario: $PROJECT_USER"
log_info "Log file: $LOG_FILE"

check_root

# Verificar Ubuntu/Debian
if [[ ! -f /etc/os-release ]]; then
    log_error "No se puede detectar el sistema operativo"
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
    log_warn "Sistema detectado: $ID (se esperaba Ubuntu/Debian)"
fi

log_info "Sistema detectado: $NAME $VERSION_ID"

# Verificar conexión a internet
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    log_error "No hay conexión a internet"
    exit 1
fi
log_info "Conexión a internet: OK"

# Inicializar log file
mkdir -p "$(dirname "$LOG_FILE")"
echo "=== Setup iniciado $(date) ===" > "$LOG_FILE"

# ============================================
# B. ACTUALIZAR SISTEMA
# ============================================
log_info "Actualizando lista de paquetes..."
sudo apt update >> "$LOG_FILE" 2>&1 || {
    log_error "Falló apt update"
    exit 1
}

log_info "Actualizando paquetes del sistema..."
sudo apt upgrade -y >> "$LOG_FILE" 2>&1 || {
    log_warn "Algunas actualizaciones fallaron (continuando...)"
}

# ============================================
# C. INSTALAR DEPENDENCIAS BASE
# ============================================
log_info "Instalando dependencias del sistema..."

sudo apt install -y \
    python3 python3-venv python3-pip \
    postgresql postgresql-contrib \
    tesseract-ocr tesseract-ocr-spa \
    poppler-utils \
    curl git htop vim \
    build-essential \
    libpq-dev \
    >> "$LOG_FILE" 2>&1 || {
    log_error "Falló la instalación de dependencias"
    exit 1
}

log_info "Dependencias instaladas correctamente"

# Verificar instalación de Python
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
log_info "Python instalado: $PYTHON_VERSION"

# ============================================
# D. INSTALAR OLLAMA
# ============================================
log_info "Verificando instalación de Ollama..."

if ! command -v ollama &> /dev/null; then
    log_info "Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh >> "$LOG_FILE" 2>&1 || {
        log_error "Falló la instalación de Ollama"
        exit 1
    }
    log_info "Ollama instalado correctamente"
else
    log_info "Ollama ya está instalado"
fi

# Añadir Ollama al PATH si no está
if ! command -v ollama &> /dev/null; then
    export PATH="$PATH:/usr/local/bin"
fi

# Descargar modelo (verificar si ya existe cualquier versión)
log_info "Verificando modelo llama3.2-vision..."
if ollama list 2>/dev/null | grep -q "llama3.2-vision"; then
    MODEL_VERSION=$(ollama list 2>/dev/null | grep "llama3.2-vision" | awk '{print $1}' | head -n1)
    log_info "Modelo llama3.2-vision ya existe: $MODEL_VERSION"
else
    log_info "Descargando modelo llama3.2-vision:latest (esto puede tardar varios minutos)..."
    ollama pull llama3.2-vision:latest >> "$LOG_FILE" 2>&1 || {
        log_error "Falló la descarga del modelo"
        log_warn "Intenta descargarlo manualmente: ollama pull llama3.2-vision:latest"
        exit 1
    }
    log_info "Modelo descargado correctamente"
fi

# Configurar systemd service
if [[ -f "${PROJECT_DIR}/infra/ollama.service" ]]; then
    log_info "Configurando servicio systemd de Ollama..."
    
    # Reemplazar USER en el servicio
    sed "s/User=user/User=${PROJECT_USER}/g" "${PROJECT_DIR}/infra/ollama.service" | \
        sudo tee /etc/systemd/system/ollama.service > /dev/null
    
    sudo systemctl daemon-reload
    sudo systemctl enable ollama >> "$LOG_FILE" 2>&1 || log_warn "No se pudo habilitar ollama service"
    sudo systemctl start ollama >> "$LOG_FILE" 2>&1 || log_warn "No se pudo iniciar ollama service"
    
    # Verificar que arrancó
    sleep 5
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        log_info "Ollama está corriendo en http://localhost:11434"
    else
        log_warn "Ollama no responde, pero el servicio está configurado"
    fi
else
    log_warn "Archivo ollama.service no encontrado, omitiendo configuración de systemd"
fi

# ============================================
# E. CONFIGURAR POSTGRESQL
# ============================================
log_info "Configurando PostgreSQL..."

# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql >> "$LOG_FILE" 2>&1 || log_warn "No se pudo habilitar postgresql"

# Verificar que PostgreSQL está corriendo
if ! sudo systemctl is-active --quiet postgresql; then
    log_error "PostgreSQL no está corriendo"
    exit 1
fi
log_info "PostgreSQL está activo"

# Ejecutar script de inicialización de DB
if [[ -f "${PROJECT_DIR}/infra/database_init.sql" ]]; then
    log_info "Ejecutando inicialización de base de datos..."
    # Leer el archivo y pasarlo a psql vía stdin para evitar problemas de permisos
    sudo -u postgres psql < "${PROJECT_DIR}/infra/database_init.sql" >> "$LOG_FILE" 2>&1 || {
        log_error "Falló la inicialización de la base de datos"
        log_warn "Es posible que la DB ya exista (esto es normal si se ejecuta múltiples veces)"
    }
    
    # Verificar conexión
    if PGPASSWORD='changeme_produccion' psql -U extractor_user -h localhost -d negocio_db -c "SELECT 1;" > /dev/null 2>&1; then
        log_info "Conexión a PostgreSQL verificada correctamente"
    else
        log_warn "No se pudo verificar la conexión a PostgreSQL (verifica profundamente)"
    fi
else
    log_warn "Archivo database_init.sql no encontrado, omitiendo inicialización de DB"
fi

# ============================================
# F. CREAR ESTRUCTURA DE CARPETAS
# ============================================
log_info "Creando estructura de carpetas..."

mkdir -p "${PROJECT_DIR}/src/{db,pipeline,dashboard,security}" 2>/dev/null || true
mkdir -p "${PROJECT_DIR}/data/{quarantine,pending,backups}"
mkdir -p "${PROJECT_DIR}/temp" "${PROJECT_DIR}/logs" "${PROJECT_DIR}/scripts"

# Crear .gitkeep files
touch "${PROJECT_DIR}/data/quarantine/.gitkeep"
touch "${PROJECT_DIR}/data/pending/.gitkeep"
touch "${PROJECT_DIR}/data/backups/.gitkeep"
touch "${PROJECT_DIR}/temp/.gitkeep"
touch "${PROJECT_DIR}/logs/.gitkeep"

log_info "Estructura de carpetas creada"

# ============================================
# G. CONFIGURAR PYTHON VIRTUAL ENVIRONMENT
# ============================================
log_info "Configurando entorno virtual Python..."

if [[ ! -d "${PROJECT_DIR}/venv" ]]; then
    python3 -m venv "${PROJECT_DIR}/venv" >> "$LOG_FILE" 2>&1 || {
        log_error "Falló la creación del entorno virtual"
        exit 1
    }
    log_info "Entorno virtual creado"
else
    log_info "Entorno virtual ya existe"
fi

# Activar y actualizar pip
source "${PROJECT_DIR}/venv/bin/activate"
pip install --upgrade pip >> "$LOG_FILE" 2>&1 || log_warn "No se pudo actualizar pip"

# Nota: requirements.txt se instalará cuando esté disponible
if [[ -f "${PROJECT_DIR}/requirements.txt" ]]; then
    log_info "Instalando dependencias de Python..."
    pip install -r "${PROJECT_DIR}/requirements.txt" >> "$LOG_FILE" 2>&1 || {
        log_warn "Algunas dependencias fallaron (revisa requirements.txt)"
    }
fi

log_info "Entorno Python configurado"

# ============================================
# H. CONFIGURAR PERMISOS
# ============================================
log_info "Configurando permisos..."

chmod +x "${PROJECT_DIR}/infra"/*.sh 2>/dev/null || true
chmod +x "${PROJECT_DIR}/scripts"/*.sh 2>/dev/null || true

log_info "Permisos configurados"

# ============================================
# I. RESUMEN FINAL
# ============================================
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ SETUP COMPLETADO${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Servicios:"
echo "  PostgreSQL: $(sudo systemctl is-active postgresql)"
echo "  Ollama: $(sudo systemctl is-active ollama 2>/dev/null || echo 'no configurado frecindamente')"
echo ""
echo "Estructura creada en: $PROJECT_DIR"
echo "Log completo: $LOG_FILE"
echo ""
echo -e "${YELLOW}⚠ IMPORTANTE:${NC}"
echo "  1. Cambia la contraseña de PostgreSQL:"
echo "     sudo -u postgres psql"
echo "     ALTER USER extractor_user WITH PASSWORD 'tu_password_segura';"
echo ""
echo "  2. Configura tu archivo .env basado en .env.example"
echo ""
echo "  3. Siguiente paso:"
echo -e "     ${GREEN}./infra/smoke_test.sh${NC}"
echo ""

log_info "Setup finalizado exitosamente"
exit 0

