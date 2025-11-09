#!/usr/bin/env python3
"""
Script ejecutable para ingesta incremental desde Google Drive
Se puede ejecutar desde cron o manualmente

Uso:
    python scripts/run_ingest_incremental.py
    
    # Con parámetros opcionales:
    python scripts/run_ingest_incremental.py --folder-id FOLDER_ID --batch-size 20
    
    # Solo validar (dry-run):
    python scripts/run_ingest_incremental.py --dry-run
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.pipeline.ingest_incremental import IncrementalIngestPipeline
from src.pipeline.job_lock import JobLock
from src.drive.drive_incremental import DriveIncrementalClient
from src.sync.state_store import get_state_store
from src.db.database import Database
from src.logging_conf import get_logger
from filelock import Timeout

# Cargar variables de entorno
load_env()

logger = get_logger(__name__)


def parse_args():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Ingesta incremental de facturas desde Google Drive'
    )
    
    parser.add_argument(
        '--folder-id',
        type=str,
        help='ID de carpeta Drive objetivo (por defecto desde GOOGLE_DRIVE_FOLDER_ID)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        help='Número de archivos por lote (por defecto desde BATCH_SIZE)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        help='Máximo de páginas Drive a procesar (por defecto desde MAX_PAGES_PER_RUN)'
    )
    
    parser.add_argument(
        '--sleep-between-batch',
        type=int,
        help='Segundos entre lotes (por defecto desde SLEEP_BETWEEN_BATCH_SEC)'
    )
    
    parser.add_argument(
        '--advance-strategy',
        type=str,
        choices=['MAX_OK_TIME', 'CURRENT_TIME'],
        help='Estrategia para avanzar timestamp (por defecto desde ADVANCE_STRATEGY)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo validar configuración y mostrar archivos a procesar, sin procesarlos'
    )
    
    parser.add_argument(
        '--output-json',
        type=str,
        help='Guardar estadísticas en archivo JSON'
    )
    
    parser.add_argument(
        '--reset-state',
        action='store_true',
        help='PELIGRO: Resetear último timestamp de sincronización (forzar rescan completo)'
    )
    
    return parser.parse_args()


def print_banner(title: str):
    """Imprimir banner decorado"""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def validate_configuration() -> bool:
    """
    Validar que la configuración está completa
    
    Returns:
        True si la configuración es válida, False en caso contrario
    """
    print_banner("VALIDACIÓN DE CONFIGURACIÓN")
    
    required_vars = [
        'GOOGLE_SERVICE_ACCOUNT_FILE',
        'GOOGLE_DRIVE_FOLDER_ID',
        'DATABASE_URL',
        'STATE_BACKEND'
    ]
    
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"❌ {var}: NO CONFIGURADA")
        else:
            # Ocultar valores sensibles
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                display_value = "***"
            elif 'URL' in var:
                display_value = value[:30] + "..." if len(value) > 30 else value
            else:
                display_value = value
            
            print(f"✅ {var}: {display_value}")
    
    if missing:
        print()
        print(f"❌ Faltan {len(missing)} variables de entorno requeridas")
        return False
    
    print()
    print("✅ Configuración válida")
    return True


def dry_run_info(pipeline: IncrementalIngestPipeline):
    """
    Mostrar información de dry-run sin procesar
    
    Args:
        pipeline: Instancia del pipeline
    """
    print_banner("DRY RUN - INFORMACIÓN")
    
    # Obtener estado actual
    last_sync_time = pipeline.state_store.get_last_sync_time()
    
    print(f"📁 Carpeta objetivo: {pipeline.folder_id}")
    print(f"⏰ Última sincronización: {last_sync_time.isoformat() if last_sync_time else 'N/A (primera ejecución)'}")
    print(f"📦 Tamaño de lote: {pipeline.batch_size}")
    print(f"📄 Máximo de páginas: {pipeline.max_pages_per_run}")
    print(f"⏱️  Pausa entre lotes: {pipeline.sleep_between_batch}s")
    print(f"🔄 Estrategia de avance: {pipeline.advance_strategy}")
    print()
    
    # Validar acceso a carpeta
    print("🔍 Validando acceso a carpeta...")
    if not pipeline.drive_client.validate_folder_access(pipeline.folder_id):
        print("❌ No se puede acceder a la carpeta")
        return
    
    print("✅ Acceso validado")
    print()
    
    # Contar archivos a procesar
    print("🔍 Contando archivos a procesar...")
    try:
        count = pipeline.drive_client.get_file_count_since(
            pipeline.folder_id,
            last_sync_time
        )
        
        print(f"📊 Archivos a procesar: {count}")
        
        if count == 0:
            print("ℹ️  No hay archivos nuevos o modificados desde la última sincronización")
        elif count > 100:
            print(f"⚠️  Se encontraron muchos archivos ({count}). Considerar ejecutar en lotes.")
        
    except Exception as e:
        print(f"❌ Error contando archivos: {e}")


def reset_sync_state(db: Database):
    """
    Resetear estado de sincronización (PELIGRO)
    
    Args:
        db: Instancia de Database
    """
    print_banner("⚠️  RESETEAR ESTADO DE SINCRONIZACIÓN")
    
    print("ADVERTENCIA: Esta acción eliminará el timestamp de última sincronización.")
    print("La próxima ejecución procesará todos los archivos en la ventana de tiempo configurada.")
    print()
    
    response = input("¿Está seguro? Escriba 'RESETEAR' para confirmar: ")
    
    if response != 'RESETEAR':
        print("❌ Operación cancelada")
        return
    
    try:
        from src.db.repositories import SyncStateRepository
        repo = SyncStateRepository(db)
        repo.delete_value('drive_last_sync_time')
        
        print("✅ Estado de sincronización reseteado")
    
    except Exception as e:
        print(f"❌ Error reseteando estado: {e}")


def main():
    """Función principal"""
    args = parse_args()
    
    print_banner("🚀 INGESTA INCREMENTAL - GOOGLE DRIVE")
    
    print(f"⏰ Inicio: {datetime.utcnow().isoformat()}Z")
    print(f"💻 Host: {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}")
    print()
    
    # Validar configuración
    if not validate_configuration():
        print()
        print("❌ Configuración inválida. Abortando.")
        sys.exit(1)
    
    # Inicializar database
    try:
        db = Database()
        logger.info("Base de datos inicializada")
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        sys.exit(1)
    
    # Manejar reset de estado
    if args.reset_state:
        reset_sync_state(db)
        sys.exit(0)
    
    # Construir kwargs para pipeline
    pipeline_kwargs = {}
    
    if args.folder_id:
        pipeline_kwargs['folder_id'] = args.folder_id
    
    if args.batch_size:
        pipeline_kwargs['batch_size'] = args.batch_size
    
    if args.max_pages:
        pipeline_kwargs['max_pages_per_run'] = args.max_pages
    
    if args.sleep_between_batch:
        pipeline_kwargs['sleep_between_batch'] = args.sleep_between_batch
    
    if args.advance_strategy:
        pipeline_kwargs['advance_strategy'] = args.advance_strategy
    
    # Inicializar pipeline
    try:
        pipeline = IncrementalIngestPipeline(**pipeline_kwargs)
    except Exception as e:
        print(f"❌ Error inicializando pipeline: {e}")
        logger.error(f"Error inicializando pipeline: {e}", exc_info=True)
        sys.exit(1)
    
    # Dry run
    if args.dry_run:
        dry_run_info(pipeline)
        print()
        print("ℹ️  Dry run completado. No se procesaron archivos.")
        sys.exit(0)
    
    # Verificar lock antes de ejecutar (para dar mensaje más claro)
    job_lock = JobLock()
    if job_lock.is_locked():
        print()
        print("⚠️  ADVERTENCIA: Otra instancia del job está ejecutándose")
        print(f"   Lock file: {job_lock.lock_file_path}")
        print()
        print("   Si estás seguro de que no hay otra instancia ejecutándose,")
        print("   puedes forzar la liberación del lock (peligroso):")
        print("   python -c 'from src.pipeline.job_lock import JobLock; JobLock().force_release()'")
        print()
        sys.exit(1)
    
    # Ejecutar pipeline
    print_banner("⚙️  EJECUTANDO PIPELINE")
    
    try:
        stats = pipeline.run()
        
        # Mostrar resumen
        print_banner("📊 RESUMEN DE EJECUCIÓN")
        
        print(f"⏱️  Duración: {stats['duration_seconds']}s")
        print(f"📄 Páginas consultadas: {stats['drive_pages_fetched_total']}")
        print(f"📥 Archivos listados: {stats['drive_items_listed_total']}")
        print(f"💾 Archivos descargados: {stats['files_downloaded']}")
        print()
        print(f"✅ Procesados OK: {stats['invoices_processed_ok_total']}")
        print(f"🔄 Revisiones: {stats['invoices_revision_total']}")
        print(f"📋 Duplicados: {stats['invoices_duplicate_total']}")
        print(f"⚠️  Para revisión: {stats['invoices_review_total']}")
        print(f"🚫 Ignorados: {stats['invoices_ignored_total']}")
        print(f"❌ Errores: {stats['invoices_error_total']}")
        print()
        print(f"🕐 Timestamp anterior: {stats['last_sync_time_before'] or 'N/A'}")
        print(f"🕑 Timestamp nuevo: {stats['last_sync_time_after'] or 'Sin cambios'}")
        print()
        
        # Guardar JSON si se solicita
        if args.output_json:
            output_path = Path(args.output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Estadísticas guardadas en: {output_path}")
            print()
        
        # Determinar exit code
        if stats['invoices_error_total'] > 0 or stats['download_errors'] > 0:
            print("⚠️  Ejecución completada con errores parciales")
            exit_code = 2  # Errores parciales
        else:
            print("✅ Ejecución completada exitosamente")
            exit_code = 0
        
        print()
        print(f"⏰ Fin: {datetime.utcnow().isoformat()}Z")
        
        sys.exit(exit_code)
    
    except Timeout:
        print()
        print("❌ Error: Otra instancia del job está ejecutándose")
        print("   Espera a que termine o verifica procesos activos")
        logger.error("Job bloqueado: otra instancia en ejecución")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print()
        print("⚠️  Ejecución interrumpida por usuario")
        logger.warning("Ejecución interrumpida por usuario (KeyboardInterrupt)")
        sys.exit(130)
    
    except Exception as e:
        print()
        print(f"❌ Error crítico: {e}")
        logger.error(f"Error crítico en ejecución: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

