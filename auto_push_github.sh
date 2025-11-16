#!/bin/bash
# Script que intenta hacer push automáticamente hasta que el repositorio exista

REPO_NAME="bresca-invoice-extrator"
GITHUB_USER="alex"
MAX_ATTEMPTS=60  # Intentar por 30 minutos (30 segundos x 60)
ATTEMPT=0

echo "🚀 Intentando subir repositorio a GitHub..."
echo "📋 Repositorio: https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "⚠️  IMPORTANTE: Crea el repositorio en GitHub primero:"
echo "   https://github.com/new"
echo "   Nombre: $REPO_NAME"
echo "   NO marques 'Initialize with README'"
echo ""
echo "⏳ Esperando que el repositorio exista..."
echo "   (Intentando cada 30 segundos, máximo $MAX_ATTEMPTS intentos)"
echo ""

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "[Intento $ATTEMPT/$MAX_ATTEMPTS] Intentando push..."
    
    OUTPUT=$(git push -u origin main 2>&1)
    EXIT_CODE=$?
    echo "$OUTPUT" | tee /tmp/push_output.log
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✅ ¡ÉXITO! Repositorio subido correctamente"
        echo "🌐 URL: https://github.com/$GITHUB_USER/$REPO_NAME"
        exit 0
    else
        if echo "$OUTPUT" | grep -q "Repository not found"; then
            echo "   ⏸️  Repositorio aún no existe en GitHub"
            echo "   ⏳ Esperando 30 segundos antes del siguiente intento..."
            sleep 30
        else
            echo ""
            echo "❌ Error al hacer push:"
            echo "$OUTPUT"
            echo ""
            echo "Verifica tus credenciales de GitHub o crea el repositorio manualmente."
            exit 1
        fi
    fi
done

echo ""
echo "⏰ Tiempo máximo de espera alcanzado ($MAX_ATTEMPTS intentos)"
echo "❌ No se pudo hacer push. Verifica que:"
echo "   1. El repositorio existe en GitHub"
echo "   2. Tienes permisos para hacer push"
echo "   3. Tus credenciales de GitHub están configuradas"
echo ""
echo "Para crear el repositorio: https://github.com/new"
echo "Nombre: $REPO_NAME"

