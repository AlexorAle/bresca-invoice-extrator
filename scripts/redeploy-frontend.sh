#!/bin/bash
set -e

# Detener y eliminar contenedor si existe (por si docker compose no lo hace)
docker stop invoice-frontend-prod 2>/dev/null || true
docker rm invoice-frontend-prod 2>/dev/null || true

# Usar docker compose para rebuild y deploy
docker compose -f docker-compose.frontend.yml down || true
docker compose -f docker-compose.frontend.yml up -d --build

echo "✅ Frontend redeployado correctamente"

