#!/usr/bin/env python3
"""
Monitor de logs en tiempo real - muestra procesamiento de facturas de forma legible
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

log_file = Path("logs/extractor.log")

if not log_file.exists():
    print(f"❌ Archivo de log no encontrado: {log_file}")
    sys.exit(1)

print("="*70)
print("📊 MONITOR DE LOGS - PROCESAMIENTO DE FACTURAS")
print("="*70)
print("Mostrando logs en tiempo real...")
print("Presiona Ctrl+C para detener\n")

# Contadores
procesadas = 0
exitosas = 0
fallidas = 0
errores_criticos = []

try:
    with open(log_file, 'r') as f:
        # Ir al final del archivo
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            
            if not line:
                time.sleep(0.5)
                continue
            
            try:
                data = json.loads(line.strip())
                level = data.get('level', '')
                message = data.get('message', '')
                module = data.get('module', '')
                
                # Mostrar solo mensajes relevantes
                if 'Reprocesando:' in message:
                    procesadas += 1
                    # Extraer número y nombre
                    if '[' in message and ']' in message:
                        num = message.split('[')[1].split(']')[0]
                        nombre = message.split(':')[1].strip() if ':' in message else message
                        print(f"🔄 [{num}] {nombre}")
                
                elif 'Batch completado' in message:
                    # Extraer estadísticas
                    if 'exitosos' in message.lower():
                        print(f"   ✅ Batch completado")
                    elif 'fallidos' in message.lower():
                        print(f"   ❌ Batch con fallos")
                
                elif 'ERROR' in level:
                    errores_criticos.append(message[:200])
                    print(f"❌ ERROR: {message[:150]}")
                
                elif 'Máximo de intentos alcanzado' in message:
                    nombre = message.split(':')[1].strip() if ':' in message else message
                    print(f"   ⚠️  Máximo intentos: {nombre}")
                
                elif 'marcada como error_permanente' in message:
                    print(f"   🔴 Marcada como error_permanente")
                
            except json.JSONDecodeError:
                # Ignorar líneas que no son JSON
                pass
            except Exception as e:
                # Ignorar otros errores de parsing
                pass

except KeyboardInterrupt:
    print("\n\n" + "="*70)
    print("📊 RESUMEN")
    print("="*70)
    print(f"Facturas procesadas: {procesadas}")
    print(f"Errores críticos: {len(errores_criticos)}")
    if errores_criticos:
        print("\nÚltimos errores:")
        for err in errores_criticos[-5:]:
            print(f"  - {err[:100]}")

