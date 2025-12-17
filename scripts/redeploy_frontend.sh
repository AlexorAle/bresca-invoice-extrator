#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "🔄 REDEPLOY COMPLETO DEL FRONTEND"
echo "════════════════════════════════════════════════════════════════"

cd /home/alex/proyectos/invoice-extractor/frontend

# 1. Rebuild sin caché
echo ""
echo "📦 Step 1/5: Rebuilding imagen (sin caché)..."
docker build -f Dockerfile -t invoice-frontend --no-cache . > /tmp/frontend_build.log 2>&1 &
BUILD_PID=$!

# Mostrar progreso
while kill -0 $BUILD_PID 2>/dev/null; do
    echo -n "."
    sleep 2
done
wait $BUILD_PID
echo " ✅"

# Verificar si el build fue exitoso
if ! grep -q "Successfully tagged invoice-frontend" /tmp/frontend_build.log; then
    echo "❌ ERROR: Build falló"
    tail -20 /tmp/frontend_build.log
    exit 1
fi

# 2. Detener y eliminar contenedor viejo
echo ""
echo "🛑 Step 2/5: Deteniendo contenedor anterior..."
docker stop invoice-frontend-prod 2>/dev/null || true
docker rm invoice-frontend-prod 2>/dev/null || true
echo "   ✅"

# 3. Desplegar nuevo contenedor
echo ""
echo "🚀 Step 3/5: Desplegando nuevo contenedor..."
docker run -d \
  --name invoice-frontend-prod \
  --network traefik-public \
  --label "traefik.enable=true" \
  --label "traefik.http.routers.invoice-frontend.rule=Host(\`alexforge.online\`) && PathPrefix(\`/invoice-dashboard\`)" \
  --label "traefik.http.routers.invoice-frontend.entrypoints=https" \
  --label "traefik.http.routers.invoice-frontend.tls.certresolver=letsencrypt" \
  --label "traefik.http.middlewares.invoice-strip-prefix.stripprefix.prefixes=/invoice-dashboard" \
  --label "traefik.http.routers.invoice-frontend.middlewares=invoice-strip-prefix" \
  --label "traefik.http.routers.invoice-frontend.service=invoice-frontend-service" \
  --label "traefik.http.services.invoice-frontend-service.loadbalancer.server.port=80" \
  --restart unless-stopped \
  invoice-frontend > /dev/null
echo "   ✅ Contenedor: $(docker ps --filter name=invoice-frontend-prod --format '{{.ID}}')"

# 4. Esperar que el contenedor esté listo
echo ""
echo "⏳ Step 4/5: Esperando que el servicio esté listo..."
sleep 5
echo "   ✅"

# 5. Verificar que el código nuevo está en el bundle
echo ""
echo "🔍 Step 5/5: Verificando bundle actualizado..."
IMAGE_DATE=$(docker inspect invoice-frontend --format='{{.Created}}' | cut -d'T' -f1-2)
BUNDLE_FILE=$(docker exec invoice-frontend-prod find /app/dist/assets -name "index-*.js" | head -1)

if [ -z "$BUNDLE_FILE" ]; then
    echo "   ❌ ERROR: No se encontró bundle"
    exit 1
fi

echo "   • Imagen construida: $IMAGE_DATE"
echo "   • Bundle: $(basename $BUNDLE_FILE)"

# Verificar contenido específico según el último cambio
if docker exec invoice-frontend-prod grep -q "proveedores" "$BUNDLE_FILE"; then
    echo "   ✅ Código 'proveedores' encontrado en bundle"
else
    echo "   ⚠️  WARNING: 'proveedores' no encontrado en bundle"
fi

# 6. Limpiar logs temporales
rm -f /tmp/frontend_build.log

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ REDEPLOY COMPLETADO"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📋 SIGUIENTE PASO PARA EL USUARIO:"
echo ""
echo "1. Abre una ventana INCÓGNITO en tu navegador"
echo "2. Ve a: https://alexforge.online/invoice-dashboard"
echo "3. Verifica los cambios"
echo ""
echo "IMPORTANTE: Si no ves los cambios, cierra TODAS las ventanas"
echo "incógnito y abre una nueva."
echo ""
echo "════════════════════════════════════════════════════════════════"

