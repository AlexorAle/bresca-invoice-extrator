#!/bin/bash
# Script para crear y subir repositorio a GitHub

REPO_NAME="bresca-invoice-extrator"
GITHUB_USER="alex"

echo "🚀 Subiendo repositorio a GitHub..."
echo ""

# Verificar si el repositorio ya existe
if git ls-remote --exit-code origin &>/dev/null; then
    echo "✅ Repositorio remoto encontrado"
    echo "📤 Subiendo código..."
    git push -u origin main
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ ¡Éxito! Repositorio subido a:"
        echo "   https://github.com/$GITHUB_USER/$REPO_NAME"
    else
        echo ""
        echo "❌ Error al subir. Verifica tus credenciales de GitHub."
        echo "   Puedes configurarlas con:"
        echo "   git config --global credential.helper store"
    fi
else
    echo "⚠️  El repositorio no existe en GitHub aún."
    echo ""
    echo "📋 Opciones para crear el repositorio:"
    echo ""
    echo "OPCIÓN 1 - Manual (más fácil):"
    echo "1. Ve a: https://github.com/new"
    echo "2. Nombre: $REPO_NAME"
    echo "3. NO marques 'Initialize with README'"
    echo "4. Clic en 'Create repository'"
    echo "5. Ejecuta este script de nuevo"
    echo ""
    echo "OPCIÓN 2 - Con Token de GitHub:"
    echo "1. Crea un token en: https://github.com/settings/tokens/new"
    echo "2. Permisos: marca 'repo'"
    echo "3. Ejecuta:"
    echo "   export GITHUB_TOKEN='tu_token_aqui'"
    echo "   curl -X POST -H \"Authorization: token \$GITHUB_TOKEN\" \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"name\":\"$REPO_NAME\",\"private\":false}' \\"
    echo "     https://api.github.com/user/repos"
    echo "4. Ejecuta este script de nuevo"
    echo ""
fi

