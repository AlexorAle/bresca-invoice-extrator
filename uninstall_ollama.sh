#!/bin/bash

# Desinstalación completa de Ollama
# Ejecutar en VPS: chmod +x uninstall_ollama.sh && ./uninstall_ollama.sh

echo "Deteniendo servicio Ollama..."

pkill -f ollama



echo "Eliminando binario..."

sudo rm -f /usr/local/bin/ollama



echo "Eliminando modelos y datos..."

rm -rf ~/.ollama



echo "Limpiando logs..."

rm -f /home/user/ollama.log



echo "Ollama desinstalado completamente."

echo "Recursos liberados: ~4GB de modelos + proceso en background"

