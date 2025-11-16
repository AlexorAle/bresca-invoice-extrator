#!/usr/bin/env python3
"""
Script para reconciliar facturas en BD con archivos en Drive
Marca facturas cuyos archivos fueron eliminados de Drive

Uso:
    python scripts/reconcile_deleted_files.py
    python scripts/reconcile_deleted_files.py --dry-run
    python scripts/reconcile_deleted_files.py --batch-size 100
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import List

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.db.database import Database
from src.db.repositories import FacturaRepository, EventRepository
from src.drive_client import DriveClient
from src.logging_conf import get_logger

# Cargar variables de entorno
load_env()

logger = get_logger(__name__)


def parse_args():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Reconciliar facturas en BD con archivos en Drive'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Mostrar qué se marcaría sin ejecutar'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Tamaño de lote para procesar (default: 100)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Límite de facturas a procesar (útil para testing)'
    )
    
    return parser.parse_args()


def main():
    """Función principal"""
    args = parse_args()
    
    print("="*70)
    print("RECONCILIACIÓN DE ARCHIVOS ELIMINADOS DE DRIVE")
    print("="*70)
    print(f"Dry-run: {args.dry_run}")
    print(f"Batch size: {args.batch_size}")
    if args.limit:
        print(f"Límite: {args.limit} facturas")
    print()
    
    # Inicializar componentes
    try:
        db = Database()
        factura_repo = FacturaRepository(db)
        event_repo = EventRepository(db)
        drive_client = DriveClient()
    except Exception as e:
        print(f"❌ Error inicializando componentes: {e}")
        logger.error(f"Error inicializando componentes: {e}", exc_info=True)
        sys.exit(1)
    
    # Obtener facturas no eliminadas
    print("📥 Obteniendo facturas de BD...")
    with db.get_session() as session:
        from src.db.models import Factura
        query = session.query(Factura).filter(
            Factura.deleted_from_drive == False
        )
        
        if args.limit:
            query = query.limit(args.limit)
        
        facturas = query.all()
        total = len(facturas)
    
    print(f"✅ {total} facturas encontradas para verificar")
    print()
    
    if total == 0:
        print("ℹ️  No hay facturas para verificar")
        sys.exit(0)
    
    # Procesar en lotes
    marked_count = 0
    exists_count = 0
    error_count = 0
    batch_num = 0
    
    for i in range(0, total, args.batch_size):
        batch_num += 1
        batch = facturas[i:i + args.batch_size]
        batch_size = len(batch)
        
        print(f"📦 Procesando lote {batch_num} ({batch_size} facturas)...")
        
        for factura in batch:
            drive_file_id = factura.drive_file_id
            file_name = factura.drive_file_name
            
            try:
                # Verificar existencia en Drive
                file_metadata = drive_client.get_file_by_id(drive_file_id)
                
                if file_metadata is None:
                    # Archivo no existe en Drive
                    if args.dry_run:
                        print(f"  🔍 [DRY-RUN] Marcaría como eliminado: {file_name} (ID: {drive_file_id})")
                    else:
                        # Marcar como eliminado
                        with db.get_session() as session:
                            factura_obj = session.query(Factura).filter(
                                Factura.id == factura.id
                            ).first()
                            if factura_obj:
                                factura_obj.deleted_from_drive = True
                                factura_obj.actualizado_en = datetime.utcnow()
                                session.commit()
                        
                        # Registrar evento
                        event_repo.registrar_evento(
                            drive_file_id=drive_file_id,
                            etapa='reconciliacion',
                            nivel='info',
                            detalle=f'Archivo marcado como eliminado de Drive: {file_name}',
                            decision='deleted_from_drive'
                        )
                        
                        logger.info(f"Archivo marcado como eliminado: {file_name} (ID: {drive_file_id})")
                    
                    marked_count += 1
                else:
                    exists_count += 1
                    if i < 10:  # Log primeros 10 para verificar
                        logger.debug(f"Archivo existe en Drive: {file_name}")
            
            except Exception as e:
                error_count += 1
                logger.error(f"Error verificando archivo {drive_file_id}: {e}", exc_info=True)
                print(f"  ⚠️  Error verificando {file_name}: {e}")
        
        print(f"  ✅ Lote {batch_num} completado")
        print()
    
    # Resumen
    print("="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Total facturas verificadas: {total}")
    print(f"Archivos que existen en Drive: {exists_count}")
    print(f"Archivos marcados como eliminados: {marked_count}")
    print(f"Errores: {error_count}")
    print()
    
    if args.dry_run:
        print("ℹ️  DRY-RUN: No se realizaron cambios en BD")
    else:
        print(f"✅ Reconciliación completada")
        if marked_count > 0:
            print(f"   {marked_count} facturas marcadas como eliminadas de Drive")
    
    db.close()


if __name__ == '__main__':
    main()

