#!/bin/bash
# Smoke test - Verificaciones post-instalación
# Verifica que todos los componentes estén correctamente instalados y configurados

set -uo pipefail  # Sin -e para que continúe aunque alguna verificación falle

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variables
PROJECT_DIR="${PWD}"
PASSED=0
FAILED=0

# Funciones de utilidad
check_pass() {
    local test_name="$1"
    echo -e "${GREEN}✓${NC} $test_name"
    PASSED=$((PASSED + 1))
}

check_fail() {
    local test_name="$1"
    local details="${2:-}"
    echo -e "${RED}✗${NC} $test_name"
    if [[ -n "$details" ]]; then
        echo "    → $details"
    fi
    FAILED=$((FAILED + 1))
}

# ============================================
# INICIO DE VERIFICACIONES
# ============================================
echo "============================================"
echo "SMOKE TEST - Invoice Extractor"
echo "============================================"
echo ""

# 1. Python 3.9+
echo "1. Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE "3\.[0-9]+" || echo "")
    if [[ -n "$PYTHON_VERSION" ]]; then
        MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        if [[ $MAJOR -eq 3 && $MINOR -ge 9 ]]; then
            check_pass "Python $PYTHON_VERSION instalado"
        else
            check_fail "Python" "Versión $PYTHON_VERSION encontrada, se requiere 3.9+"
        fi
    else
        check_fail "Python" "No se pudo determinar la versión"
    fi
else
    check_fail "Python" "python3 no encontrado"
fi

# 2. PostgreSQL
echo ""
echo "2. Verificando PostgreSQL..."
if systemctl is-active --quiet postgresql; then
    check_pass "PostgreSQL está corriendo"
    
    # Verificar conexión y tablas
    if PGPASSWORD='changeme_produccion' psql -U extractor_user -h localhost -d negocio_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" &> /dev/null; then
        TABLE_COUNT=$(PGPASSWORD='changeme_produccion' psql -U extractor_user -h localhost -d negocio_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
        if [[ $TABLE_COUNT -ge 3 ]]; then
            check_pass "Base de datos negocio_db con $TABLE_COUNT tablas"
        else
            check_fail "Base de datos" "Solo se encontraron $TABLE_COUNT tablas (se esperaban al menos 3)"
        fi
    else
        check_fail "Conexión a PostgreSQL" "No se pudo conectar con extractor_user"
    fi
else
    check_fail "PostgreSQL" "Servicio no está corriendo"
fi

# 3. Ollama
echo ""
echo "3. Verificando Ollama..."
if systemctl is-active --quiet ollama 2>/dev/null || pgrep -x ollama &> /dev/null; then
    check_pass "Ollama está corriendo"
    
    # Verificar API
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        check_pass "API de Ollama responde en http://localhost:11434"
        
        # Verificar modelo (cualquier versión de llama3.2-vision)
        if ollama list 2>/dev/null | grep -q "llama3.2-vision"; then
            MODEL_VERSION=$(ollama list 2>/dev/null | grep "llama3.2-vision" | awk '{print $1}' | head -n1)
            check_pass "Modelo llama3.2-vision disponible: $MODEL_VERSION"
        else
            check_fail "Modelo Ollama" "llama3.2-vision no encontrado (descarga con: ollama pull llama3.2-vision:latest)"
        fi
    else
        check_fail "API de Ollama" "No responde en http://localhost:11434"
    fi
else
    check_fail "Ollama" "Servicio no está corriendo"
fi

# 4. Tesseract OCR
echo ""
echo "4. Verificando Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    TESS_VERSION=$(tesseract --version 2>&1 | head -n1)
    check_pass "Tesseract instalado: $TESS_VERSION"
    
    # Verificar idioma español
    if tesseract --list-langs 2>/dev/null | grep -q "^spa$"; then
        check_pass "Idioma español (spa) disponible en Tesseract"
    else
        check_fail "Idioma Tesseract" "Español (spa) no encontrado"
    fi
else
    check_fail "Tesseract" "tesseract no encontrado"
fi

# 5. Poppler
echo ""
echo "5. Verificando Poppler..."
if command -v pdftoppm &> /dev/null; then
    POPPLER_VERSION=$(pdftoppm -v 2>&1 | head -n1 | grep -oE "[0-9]+\.[0-9]+" | head -n1 || echo "instalado")
    check_pass "Poppler instalado (pdftoppm disponible)"
else
    check_fail "Poppler" "pdftoppm no encontrado"
fi

# 6. Estructura de carpetas
echo ""
echo "6. Verificando estructura de carpetas..."
REQUIRED_DIRS=(
    "src/db"
    "src/pipeline"
    "src/dashboard"
    "src/security"
    "data/quarantine"
    "data/pending"
    "data/backups"
    "temp"
    "logs"
    "scripts"
)

ALL_DIRS_OK=true
for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ -d "${PROJECT_DIR}/${dir}" ]]; then
        check_pass "Directorio $dir existe"
    else
        check_fail "Directorio" "$dir no existe"
        ALL_DIRS_OK=false
    fi
done

# 7. Virtual environment
echo ""
echo "7. Verificando entorno virtual Python..."
if [[ -d "${PROJECT_DIR}/venv" ]]; then
    if [[ -f "${PROJECT_DIR}/venv/bin/activate" ]]; then
        check_pass "Entorno virtual existe y está configurado"
        
        # Verificar pip
        if [[ -f "${PROJECT_DIR}/venv/bin/pip" ]]; then
            check_pass "pip disponible en venv"
        else
            check_fail "pip" "No encontrado en venv"
        fi
    else
        check_fail "Entorno virtual" "venv/bin/activate no encontrado"
    fi
else
    check_fail "Entorno virtual" "Directorio venv no existe"
fi

# 8. Archivos de configuración
echo ""
echo "8. Verificando archivos de configuración..."
REQUIRED_FILES=(
    ".env.example"
    ".gitignore"
    "requirements.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "${PROJECT_DIR}/${file}" ]]; then
        check_pass "Archivo $file existe"
    else
        check_fail "Archivo" "$file no encontrado"
    fi
done

# ============================================
# RESUMEN FINAL
# ============================================
echo ""
echo "============================================"
echo "RESUMEN"
echo "============================================"
echo -e "${GREEN}✓ Exitosos: $PASSED${NC}"
if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}✗ Fallidos: $FAILED${NC}"
    echo ""
    echo "Revisa los errores arriba y ejecuta nuevamente ./infra/setup.sh si es necesario"
    exit 1
else
    echo -e "${GREEN}✓ Fallidos: 0${NC}"
    echo ""
    echo -e "${GREEN}¡Todos los checks pasaron! El sistema está listo.${NC}"
    exit 0
fi

