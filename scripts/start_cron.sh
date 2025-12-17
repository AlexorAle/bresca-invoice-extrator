#!/bin/bash
# Script para instalar, configurar e iniciar cron en el contenedor
# Este script debe ejecutarse al iniciar el contenedor o manualmente

set -e

echo "🔧 Configurando cron para ingesta incremental..."

# Verificar si cron está instalado
if ! command -v cron &> /dev/null; then
    echo "📦 Instalando cron..."
    apt-get update -qq
    apt-get install -y cron > /dev/null 2>&1
    echo "✅ Cron instalado"
else
    echo "✅ Cron ya está instalado"
fi

# Crear directorio de logs si no existe
mkdir -p /app/logs/cron

# Hacer scripts ejecutables
chmod +x /app/scripts/cron_ingest_incremental.sh

# Configurar crontab si no está configurado
CRON_ENTRY="0 */12 * * * /app/scripts/cron_ingest_incremental.sh"

# Verificar si ya existe la entrada
if crontab -l 2>/dev/null | grep -q "cron_ingest_incremental.sh"; then
    echo "⚠️  Crontab ya está configurado"
    echo "   Entrada actual:"
    crontab -l 2>/dev/null | grep "cron_ingest_incremental.sh"
else
    # Agregar nueva entrada de crontab
    # Ejecutar cada 12 horas (00:00 y 12:00)
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Crontab configurado: cada 12 horas (00:00 y 12:00)"
fi

# Iniciar servicio cron si no está corriendo
# Verificar si cron está corriendo (sin pgrep, usar ps)
if ! ps aux | grep -q '[c]ron'; then
    echo "🚀 Iniciando servicio cron..."
    cron
    echo "✅ Servicio cron iniciado"
else
    echo "✅ Servicio cron ya está corriendo"
fi

echo ""
echo "📋 Configuración de cron:"
echo "   Frecuencia: Cada 12 horas (00:00 y 12:00)"
echo "   Script: /app/scripts/cron_ingest_incremental.sh"
echo "   Log: /app/logs/cron/cron_ingest_incremental.log"
echo ""
echo "Para ver los cron jobs configurados:"
echo "   crontab -l"
echo ""
echo "Para ver los logs:"
echo "   tail -f /app/logs/cron/cron_ingest_incremental.log"
echo ""

