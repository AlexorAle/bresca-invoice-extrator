#!/usr/bin/env python3
"""
Script de prueba: Procesar 30 facturas y monitorear logs en tiempo real
Detiene la ejecución si detecta errores críticos
"""
import sys
import os
import subprocess
import time
import signal
from pathlib import Path
from datetime import datetime

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# Configurar variables de entorno para limitar procesamiento
os.environ['REPROCESS_REVIEW_MAX_COUNT'] = '30'
os.environ['BATCH_SIZE'] = '10'
os.environ['MAX_PAGES'] = '3'  # Limitar páginas para no procesar demasiados archivos nuevos

print("="*70)
print("PRUEBA: Procesamiento de 30 Facturas")
print("="*70)
print(f"⏰ Inicio: {datetime.now().isoformat()}")
print(f"📊 Configuración:")
print(f"   - Máximo facturas a reprocesar: 30")
print(f"   - Tamaño de batch: 10")
print(f"   - Máximo páginas: 3")
print()

# Proceso del job
job_process = None
log_file = project_root / "logs" / "extractor.log"

def signal_handler(sig, frame):
    """Manejar interrupción (Ctrl+C)"""
    print("\n\n⚠️  Interrupción recibida. Deteniendo job...")
    if job_process:
        job_process.terminate()
        try:
            job_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            job_process.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Contadores de errores
error_count = 0
warning_count = 0
critical_errors = []

def check_log_line(line):
    """Verificar si una línea de log indica un error crítico"""
    global error_count, warning_count
    
    # Buscar errores críticos
    if '"level":"ERROR"' in line:
        error_count += 1
        # Extraer mensaje de error
        try:
            import json
            data = json.loads(line.strip())
            error_msg = data.get('message', '')
            exception = data.get('exception', '')
            
            # Errores críticos que deben detener la ejecución
            critical_patterns = [
                'CheckViolation',
                'IntegrityError',
                'DatabaseError',
                'ConnectionError',
                'Timeout',
                'FATAL',
                'cannot access',
                'violates check constraint'
            ]
            
            full_error = f"{error_msg} {exception}"
            for pattern in critical_patterns:
                if pattern in full_error:
                    critical_errors.append({
                        'message': error_msg,
                        'exception': exception[:200] if exception else '',
                        'timestamp': data.get('timestamp', '')
                    })
                    return True  # Error crítico detectado
        except:
            pass
    
    # Contar warnings
    if '"level":"WARNING"' in line:
        warning_count += 1
    
    return False

def monitor_logs():
    """Monitorear logs en tiempo real"""
    print("📊 Monitoreando logs en tiempo real...")
    print("   (Presiona Ctrl+C para detener)\n")
    
    if not log_file.exists():
        print(f"⚠️  Archivo de log no encontrado: {log_file}")
        return False
    
    # Leer desde el final del archivo
    with open(log_file, 'r') as f:
        # Ir al final del archivo
        f.seek(0, 2)
        
        last_position = f.tell()
        consecutive_errors = 0
        
        while job_process and job_process.poll() is None:
            # Leer nuevas líneas
            f.seek(last_position)
            new_lines = f.readlines()
            last_position = f.tell()
            
            for line in new_lines:
                if check_log_line(line):
                    consecutive_errors += 1
                    print(f"\n❌ ERROR CRÍTICO DETECTADO:")
                    try:
                        import json
                        data = json.loads(line.strip())
                        print(f"   Mensaje: {data.get('message', 'N/A')[:100]}")
                        if data.get('exception'):
                            print(f"   Excepción: {data.get('exception', '')[:200]}")
                    except:
                        print(f"   Línea: {line[:200]}")
                    
                    # Si hay 3 errores críticos consecutivos, detener
                    if consecutive_errors >= 3:
                        print(f"\n🛑 DETENIENDO: {consecutive_errors} errores críticos consecutivos detectados")
                        return True
                else:
                    consecutive_errors = 0
            
            time.sleep(0.5)  # Esperar antes de leer más
        
        # Verificar si el proceso terminó con error
        if job_process.poll() != 0:
            print(f"\n⚠️  El job terminó con código de error: {job_process.returncode}")
            return True
    
    return False

# Ejecutar el job
print("🚀 Iniciando job incremental...")
print()

try:
    # Ejecutar el job en background
    job_process = subprocess.Popen(
        [sys.executable, str(project_root / "scripts" / "run_ingest_incremental.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Monitorear logs
    should_stop = monitor_logs()
    
    if should_stop:
        print("\n🛑 Deteniendo job debido a errores críticos...")
        job_process.terminate()
        try:
            job_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            job_process.kill()
        print("✅ Job detenido")
    else:
        # Esperar a que termine
        print("\n⏳ Esperando que el job termine...")
        job_process.wait()
        
        if job_process.returncode == 0:
            print("✅ Job completado exitosamente")
        else:
            print(f"⚠️  Job terminó con código: {job_process.returncode}")

except KeyboardInterrupt:
    print("\n\n⚠️  Interrupción por usuario")
    if job_process:
        job_process.terminate()
        job_process.wait()

finally:
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE LA PRUEBA")
    print("="*70)
    print(f"⏰ Fin: {datetime.now().isoformat()}")
    print(f"❌ Errores detectados: {error_count}")
    print(f"⚠️  Warnings detectados: {warning_count}")
    print(f"🔴 Errores críticos: {len(critical_errors)}")
    
    if critical_errors:
        print("\n🔴 ERRORES CRÍTICOS ENCONTRADOS:")
        for i, err in enumerate(critical_errors[:5], 1):  # Mostrar solo los primeros 5
            print(f"\n   {i}. {err['message'][:100]}")
            if err['exception']:
                print(f"      {err['exception'][:150]}")
    
    if error_count == 0 and len(critical_errors) == 0:
        print("\n✅ PRUEBA EXITOSA: No se detectaron errores críticos")
    else:
        print(f"\n⚠️  PRUEBA CON PROBLEMAS: Se detectaron {len(critical_errors)} errores críticos")
    
    print()

