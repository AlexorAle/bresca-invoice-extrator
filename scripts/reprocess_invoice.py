#!/usr/bin/env python3
"""
Script para reprocesar una factura específica manualmente

Uso:
    python scripts/reprocess_invoice.py --drive-file-id <id>
    python scripts/reprocess_invoice.py --drive-file-id <id> --force
    python scripts/reprocess_invoice.py --drive-file-id <id> --reset-attempts
    python scripts/reprocess_invoice.py --drive-file-id <id> --dry-run
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.db.database import Database
from src.db.repositories import FacturaRepository, EventRepository
from src.drive_client import DriveClient
from src.ocr_extractor import InvoiceExtractor
from src.pipeline.ingest import process_batch
from src.pipeline.validate import sanitize_filename
from src.logging_conf import get_logger

# Cargar variables de entorno
load_env()

logger = get_logger(__name__)


def parse_args():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Reprocesar una factura específica por drive_file_id'
    )
    
    parser.add_argument(
        '--drive-file-id',
        type=str,
        required=True,
        help='ID del archivo en Google Drive (drive_file_id)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Forzar reprocesamiento aunque esté en estado "procesado"'
    )
    
    parser.add_argument(
        '--reset-attempts',
        action='store_true',
        help='Resetear contador de intentos de reprocesamiento antes de reprocesar'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mostrar qué se haría sin ejecutar'
    )
    
    return parser.parse_args()


def main():
    """Función principal"""
    args = parse_args()
    drive_file_id = args.drive_file_id
    
    print("="*70)
    print("REPROCESAMIENTO MANUAL DE FACTURA")
    print("="*70)
    print(f"Drive File ID: {drive_file_id}")
    print(f"Force: {args.force}")
    print(f"Reset attempts: {args.reset_attempts}")
    print(f"Dry-run: {args.dry_run}")
    print()
    
    # Inicializar componentes
    try:
        db = Database()
        factura_repo = FacturaRepository(db)
        event_repo = EventRepository(db)
        drive_client = DriveClient()
        extractor = InvoiceExtractor()
    except Exception as e:
        print(f"❌ Error inicializando componentes: {e}")
        logger.error(f"Error inicializando componentes: {e}", exc_info=True)
        sys.exit(1)
    
    # Buscar factura en BD
    factura = factura_repo.find_by_file_id(drive_file_id)
    
    if not factura:
        print(f"❌ Error: Factura con drive_file_id '{drive_file_id}' no encontrada en BD")
        print()
        print("   Verifica que el ID sea correcto o que la factura haya sido procesada al menos una vez.")
        sys.exit(1)
    
    estado_actual = factura.get('estado')
    reprocess_attempts = factura.get('reprocess_attempts', 0)
    drive_file_name = factura.get('drive_file_name', 'unknown')
    
    print(f"📄 Factura encontrada: {drive_file_name}")
    print(f"   Estado actual: {estado_actual}")
    print(f"   Intentos de reprocesamiento: {reprocess_attempts}")
    print()
    
    # Validar si se puede reprocesar
    if estado_actual == 'procesado' and not args.force:
        print("⚠️  ADVERTENCIA: Factura está en estado 'procesado'")
        print("   Usa --force para forzar reprocesamiento")
        sys.exit(1)
    
    if args.dry_run:
        print("🔍 DRY-RUN: Mostrando qué se haría...")
        print()
        print(f"   1. Obtener metadata de archivo desde Drive")
        print(f"   2. Descargar archivo: {drive_file_name}")
        print(f"   3. Reprocesar con OCR y validaciones")
        if args.reset_attempts:
            print(f"   4. Resetear reprocess_attempts a 0")
        print(f"   5. Actualizar factura en BD")
        print()
        print("ℹ️  Dry-run completado. No se ejecutó ningún cambio.")
        sys.exit(0)
    
    # Resetear intentos si se solicita
    if args.reset_attempts:
        print("🔄 Reseteando contador de intentos...")
        with db.get_session() as session:
            from src.db.models import Factura
            factura_obj = session.query(Factura).filter(
                Factura.drive_file_id == drive_file_id
            ).first()
            if factura_obj:
                factura_obj.reprocess_attempts = 0
                factura_obj.reprocessed_at = None
                factura_obj.reprocess_reason = None
                session.commit()
                print("✅ Contador reseteado")
            else:
                print("⚠️  No se pudo resetear (factura no encontrada)")
        print()
    
    # Crear directorio temporal
    temp_dir = Path(tempfile.mkdtemp(prefix='reprocess_invoice_'))
    print(f"📁 Directorio temporal: {temp_dir}")
    print()
    
    try:
        # Obtener metadata del archivo desde Drive
        print("📥 Obteniendo metadata desde Drive...")
        file_metadata = drive_client.get_file_by_id(drive_file_id)
        
        if not file_metadata:
            print(f"❌ Error: No se pudo obtener metadata de archivo {drive_file_id}")
            print("   Verifica que el archivo existe en Drive y que tienes permisos")
            sys.exit(1)
        
        # Validar que es PDF
        if file_metadata.get('mimeType') != 'application/pdf':
            print(f"❌ Error: Archivo no es PDF: {file_metadata.get('mimeType')}")
            sys.exit(1)
        
        print(f"✅ Metadata obtenida: {file_metadata.get('name')}")
        print()
        
        # Descargar archivo
        print("📥 Descargando archivo desde Drive...")
        safe_name = sanitize_filename(file_metadata.get('name', 'unknown.pdf'))
        local_path = temp_dir / f"{drive_file_id}_{safe_name}"
        
        success = drive_client.download_file(
            drive_file_id,
            str(local_path),
            file_size=file_metadata.get('size')
        )
        
        if not success:
            print(f"❌ Error: No se pudo descargar archivo {drive_file_id}")
            sys.exit(1)
        
        print(f"✅ Archivo descargado: {local_path}")
        print()
        
        # Preparar file_info compatible con process_batch
        file_info = {
            'id': drive_file_id,
            'name': file_metadata.get('name'),
            'local_path': str(local_path),
            'folder_name': factura.get('drive_folder_name', file_metadata.get('folder_name', 'unknown')),
            'modifiedTime': file_metadata.get('modifiedTime'),
            'size': file_metadata.get('size')
        }
        
        # Reprocesar
        print("🔄 Reprocesando factura...")
        print()
        
        batch_stats = process_batch([file_info], extractor, db)
        
        # Verificar resultado
        if batch_stats.get('exitosos', 0) > 0:
            print("✅ Reprocesamiento exitoso")
            
            # Verificar estado actualizado
            factura_actualizada = factura_repo.find_by_file_id(drive_file_id)
            nuevo_estado = factura_actualizada.get('estado') if factura_actualizada else None
            
            print()
            print("📊 RESULTADO:")
            print(f"   Estado anterior: {estado_actual}")
            print(f"   Estado nuevo: {nuevo_estado}")
            print(f"   Intentos: {factura_actualizada.get('reprocess_attempts', 0) if factura_actualizada else 'N/A'}")
            
            if nuevo_estado == 'procesado':
                print()
                print("✅ Factura ahora está en estado 'procesado'")
            elif nuevo_estado == 'revisar':
                print()
                print("⚠️  Factura sigue en estado 'revisar' (validación falló)")
                error_msg = factura_actualizada.get('error_msg', '') if factura_actualizada else ''
                if error_msg:
                    print(f"   Error: {error_msg[:100]}")
        else:
            print("❌ Reprocesamiento falló")
            print()
            print("📊 ESTADÍSTICAS:")
            print(f"   Exitosos: {batch_stats.get('exitosos', 0)}")
            print(f"   Fallidos: {batch_stats.get('fallidos', 0)}")
            print(f"   Errores: {batch_stats.get('error', 'N/A')}")
            
            # Verificar estado
            factura_actualizada = factura_repo.find_by_file_id(drive_file_id)
            if factura_actualizada:
                print(f"   Estado actual: {factura_actualizada.get('estado')}")
                print(f"   Intentos: {factura_actualizada.get('reprocess_attempts', 0)}")
            
            sys.exit(1)
    
    except KeyboardInterrupt:
        print()
        print("⚠️  Reprocesamiento interrumpido por usuario")
        sys.exit(130)
    
    except Exception as e:
        print()
        print(f"❌ Error crítico: {e}")
        logger.error(f"Error en reprocesamiento manual: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # Limpiar directorio temporal
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print()
            print("🧹 Directorio temporal limpiado")


if __name__ == '__main__':
    main()

