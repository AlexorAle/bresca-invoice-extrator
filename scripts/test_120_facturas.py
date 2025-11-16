#!/usr/bin/env python3
"""
Script de prueba: Procesar exactamente 120 facturas desde Drive
Muestra resumen detallado al final
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.db.database import Database
from src.db.repositories import FacturaRepository, EventRepository
from src.drive_client import DriveClient
from src.drive.drive_incremental import DriveIncrementalClient
from src.ocr_extractor import InvoiceExtractor
from src.pipeline.ingest import process_batch
from src.logging_conf import get_logger
import tempfile
import shutil

load_env()
logger = get_logger(__name__)

def main():
    print("="*70)
    print("🧪 PRUEBA: Procesamiento de 120 Facturas")
    print("="*70)
    print(f"⏰ Inicio: {datetime.now().isoformat()}")
    print()
    
    # Configuración
    MAX_FACTURAS = 120
    BATCH_SIZE = 10
    
    # Inicializar componentes
    db = Database()
    factura_repo = FacturaRepository(db)
    event_repo = EventRepository(db)
    drive_client = DriveClient()
    drive_incremental = DriveIncrementalClient()
    extractor = InvoiceExtractor()
    
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    if not folder_id:
        print("❌ GOOGLE_DRIVE_FOLDER_ID no configurado")
        sys.exit(1)
    
    temp_dir = Path(tempfile.mkdtemp(prefix='test_120_facturas_'))
    
    try:
        print("📁 Obteniendo PDFs desde Drive...")
        
        # Obtener todas las subcarpetas
        all_folders = drive_incremental._get_all_subfolders(folder_id)
        
        # Listar todos los PDFs
        all_pdfs = []
        for folder_id_item in all_folders:
            pdfs = drive_client.list_pdf_files(folder_id_item)
            all_pdfs.extend(pdfs)
        
        print(f"   ✅ Encontrados {len(all_pdfs)} PDFs en Drive")
        
        # Limitar a 120
        pdfs_to_process = all_pdfs[:MAX_FACTURAS]
        print(f"   📊 Procesando los primeros {len(pdfs_to_process)} PDFs")
        print()
        
        # Estadísticas
        stats = {
            'total': len(pdfs_to_process),
            'exitosos': 0,
            'fallidos': 0,
            'revisar': 0,
            'duplicados': 0,
            'procesados': 0
        }
        
        # Procesar en batches
        for batch_start in range(0, len(pdfs_to_process), BATCH_SIZE):
            batch = pdfs_to_process[batch_start:batch_start + BATCH_SIZE]
            batch_num = (batch_start // BATCH_SIZE) + 1
            total_batches = (len(pdfs_to_process) + BATCH_SIZE - 1) // BATCH_SIZE
            
            print(f"📦 Procesando batch {batch_num}/{total_batches} ({len(batch)} archivos)...")
            
            # Preparar file_info para cada archivo
            file_info_list = []
            for pdf in batch:
                drive_file_id = pdf['id']
                file_name = pdf['name']
                
                # Descargar archivo
                safe_name = file_name.replace('/', '_').replace('\\', '_')
                local_path = temp_dir / f"{drive_file_id}_{safe_name}"
                
                success = drive_client.download_file(drive_file_id, str(local_path))
                if not success:
                    print(f"   ⚠️  No se pudo descargar: {file_name}")
                    stats['fallidos'] += 1
                    continue
                
                file_info = {
                    'id': drive_file_id,
                    'name': file_name,
                    'local_path': str(local_path),
                    'folder_name': pdf.get('folder_name', 'unknown'),
                    'modifiedTime': pdf.get('modifiedTime'),
                    'size': pdf.get('size')
                }
                file_info_list.append(file_info)
            
            # Procesar batch
            if file_info_list:
                batch_stats = process_batch(file_info_list, extractor, db)
                
                stats['exitosos'] += batch_stats.get('exitosos', 0)
                stats['fallidos'] += batch_stats.get('fallidos', 0)
                stats['revisar'] += batch_stats.get('revisar', 0)
                stats['duplicados'] += batch_stats.get('duplicados', 0)
                stats['procesados'] += batch_stats.get('exitosos', 0) + batch_stats.get('revisar', 0)
                
                print(f"   ✅ Batch {batch_num} completado: {batch_stats.get('exitosos', 0)} exitosos, {batch_stats.get('fallidos', 0)} fallidos")
        
        # Obtener estadísticas finales de BD
        print()
        print("📊 Obteniendo estadísticas finales de BD...")
        
        with db.get_session() as session:
            from src.db.models import Factura
            from sqlalchemy import func
            
            total_bd = session.query(Factura).count()
            
            estados = session.query(
                Factura.estado,
                func.count(Factura.id).label('count')
            ).group_by(Factura.estado).all()
            
            extractores = session.query(
                Factura.extractor,
                func.count(Factura.id).label('count')
            ).group_by(Factura.extractor).all()
            
            # Verificar campos fiscales
            con_impuestos = session.query(Factura).filter(
                Factura.impuestos_total.isnot(None)
            ).count()
            con_base = session.query(Factura).filter(
                Factura.base_imponible.isnot(None)
            ).count()
            con_iva = session.query(Factura).filter(
                Factura.iva_porcentaje.isnot(None)
            ).count()
        
        # Resumen final
        print()
        print("="*70)
        print("📋 RESUMEN FINAL")
        print("="*70)
        print(f"⏰ Fin: {datetime.now().isoformat()}")
        print()
        print(f"📊 ESTADÍSTICAS DE PROCESAMIENTO:")
        print(f"   - Total PDFs procesados: {stats['total']}")
        print(f"   - Exitosos (procesado): {stats['exitosos']}")
        print(f"   - En revisar: {stats['revisar']}")
        print(f"   - Fallidos: {stats['fallidos']}")
        print(f"   - Duplicados: {stats['duplicados']}")
        print()
        print(f"📊 ESTADÍSTICAS EN BASE DE DATOS:")
        print(f"   - Total facturas en BD: {total_bd}")
        print()
        print(f"   Distribución por estado:")
        for estado, count in sorted(estados):
            porcentaje = (count / total_bd * 100) if total_bd > 0 else 0
            print(f"     - {estado}: {count} ({porcentaje:.1f}%)")
        print()
        print(f"   Distribución por extractor:")
        for extractor, count in sorted(extractores):
            porcentaje = (count / total_bd * 100) if total_bd > 0 else 0
            print(f"     - {extractor}: {count} ({porcentaje:.1f}%)")
        print()
        print(f"📊 CAMPOS FISCALES EXTRAÍDOS:")
        print(f"   - Facturas con impuestos_total: {con_impuestos} ({con_impuestos/total_bd*100 if total_bd > 0 else 0:.1f}%)")
        print(f"   - Facturas con base_imponible: {con_base} ({con_base/total_bd*100 if total_bd > 0 else 0:.1f}%)")
        print(f"   - Facturas con iva_porcentaje: {con_iva} ({con_iva/total_bd*100 if total_bd > 0 else 0:.1f}%)")
        print()
        
        # Análisis de resultados
        tasa_exito = (stats['exitosos'] / stats['total'] * 100) if stats['total'] > 0 else 0
        tasa_revisar = (stats['revisar'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        print(f"📈 ANÁLISIS:")
        print(f"   - Tasa de éxito: {tasa_exito:.1f}%")
        print(f"   - Tasa en revisar: {tasa_revisar:.1f}%")
        print(f"   - Tasa de fallos: {(stats['fallidos'] / stats['total'] * 100) if stats['total'] > 0 else 0:.1f}%")
        print()
        
        if stats['exitosos'] > 0:
            print("✅ Prueba completada con éxito")
        elif stats['revisar'] > 0:
            print("⚠️  Prueba completada, pero todas las facturas están en 'revisar'")
        else:
            print("❌ Prueba completada con errores")
        
        print()
    
    except Exception as e:
        logger.error(f"Error durante la prueba: {e}", exc_info=True)
        print(f"\n❌ Error crítico: {e}")
        raise
    finally:
        # Limpiar archivos temporales
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.info(f"Directorio temporal {temp_dir} eliminado")
        db.close()

if __name__ == '__main__':
    main()

