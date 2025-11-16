#!/usr/bin/env python3
"""
Script para resetear last_sync_time a enero 2024 y ejecutar pipeline incremental
con monitoreo y reporte detallado
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.db.database import Database
from src.sync.state_store import get_state_store
from src.pipeline.ingest_incremental import IncrementalIngestPipeline
from src.logging_conf import get_logger
import json

logger = get_logger(__name__)

def reset_sync_time_to_january_2024():
    """Resetear last_sync_time a 1 de enero 2024"""
    load_env()
    db = Database()
    state_store = get_state_store(db)
    
    # Establecer fecha a 1 de enero 2024, 00:00:00 UTC
    january_2024 = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    print("="*70)
    print("🔄 RESETEANDO LAST_SYNC_TIME")
    print("="*70)
    
    # Obtener valor actual
    current_sync = state_store.get_last_sync_time()
    if current_sync:
        print(f"Valor actual: {current_sync.isoformat()}")
    else:
        print("Valor actual: None (primera ejecución)")
    
    # Establecer nuevo valor
    state_store.set_last_sync_time(january_2024)
    print(f"✅ Nuevo valor: {january_2024.isoformat()}")
    print()
    
    # Verificar
    verify = state_store.get_last_sync_time()
    if verify and verify == january_2024:
        print("✅ Verificación exitosa: last_sync_time actualizado correctamente")
    else:
        print("❌ ERROR: No se pudo verificar el cambio")
        db.close()
        return False
    
    db.close()
    return True

def run_incremental_pipeline():
    """Ejecutar pipeline incremental sin límite"""
    load_env()
    
    print("="*70)
    print("🚀 EJECUTANDO PIPELINE INCREMENTAL")
    print("="*70)
    print(f"⏰ Inicio: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    try:
        # Crear pipeline (sin límite de páginas - pasar 999999 para simular sin límite)
        # El pipeline se inicializa internamente con todos sus componentes
        pipeline = IncrementalIngestPipeline(
            folder_id=os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
            batch_size=int(os.getenv('BATCH_SIZE', '10')),
            max_pages_per_run=999999  # Valor muy alto para simular sin límite
        )
        
        # Ejecutar pipeline
        stats = pipeline.run()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error ejecutando pipeline: {e}", exc_info=True)
        raise

def generate_detailed_report(stats: dict):
    """Generar reporte detallado de la ejecución"""
    load_env()
    db = Database()
    
    from src.db.repositories import FacturaRepository
    
    print()
    print("="*70)
    print("📊 GENERANDO REPORTE DETALLADO")
    print("="*70)
    print()
    
    # Estadísticas del pipeline
    print("📈 ESTADÍSTICAS DE PROCESAMIENTO:")
    print("-" * 70)
    print(f"  Duración total: {stats.get('duration_seconds', 0):.1f} segundos")
    print(f"  Archivos listados en Drive: {stats.get('drive_items_listed_total', 0)}")
    print(f"  Páginas procesadas: {stats.get('drive_pages_fetched_total', 0)}")
    print()
    
    print("📦 FACTURAS PROCESADAS:")
    print("-" * 70)
    print(f"  ✅ Exitosas: {stats.get('invoices_processed_ok_total', 0)}")
    print(f"  ⚠️  En revisar: {stats.get('invoices_revision_total', 0)}")
    print(f"  🔄 Duplicados: {stats.get('invoices_duplicate_total', 0)}")
    print(f"  ❌ Errores: {stats.get('invoices_error_total', 0)}")
    print(f"  🚫 Ignoradas: {stats.get('invoices_ignored_total', 0)}")
    print()
    
    if stats.get('files_rejected_size', 0) > 0:
        print(f"  📏 Rechazadas por tamaño: {stats.get('files_rejected_size', 0)}")
        print()
    
    # Estadísticas de BD
    factura_repo = FacturaRepository(db)
    
    with db.get_session() as session:
        from src.db.models import Factura
        from sqlalchemy import func
        
        total_facturas = session.query(Factura).count()
        
        estados = session.query(
            Factura.estado,
            func.count(Factura.id).label('count')
        ).group_by(Factura.estado).all()
        
        print("💾 ESTADO EN BASE DE DATOS:")
        print("-" * 70)
        print(f"  Total facturas en BD: {total_facturas}")
        print()
        print("  Distribución por estado:")
        for estado, count in sorted(estados):
            porcentaje = (count / total_facturas * 100) if total_facturas > 0 else 0
            print(f"    - {estado}: {count} ({porcentaje:.1f}%)")
        print()
        
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
        
        print("💰 CAMPOS FISCALES:")
        print("-" * 70)
        print(f"  Con impuestos_total: {con_impuestos} ({con_impuestos/total_facturas*100 if total_facturas > 0 else 0:.1f}%)")
        print(f"  Con base_imponible: {con_base} ({con_base/total_facturas*100 if total_facturas > 0 else 0:.1f}%)")
        print(f"  Con iva_porcentaje: {con_iva} ({con_iva/total_facturas*100 if total_facturas > 0 else 0:.1f}%)")
        print()
        
        # Últimas facturas procesadas
        print("🕐 ÚLTIMAS 10 FACTURAS PROCESADAS:")
        print("-" * 70)
        ultimas = session.query(Factura).order_by(Factura.creado_en.desc()).limit(10).all()
        for f in ultimas:
            print(f"  - {f.drive_file_name} (estado: {f.estado}, creado: {f.creado_en})")
        print()
    
    # Verificar errores en logs
    print("🔍 ANÁLISIS DE ERRORES:")
    print("-" * 70)
    
    error_count = stats.get('invoices_error_total', 0)
    if error_count > 0:
        print(f"  ⚠️  Se detectaron {error_count} errores durante el procesamiento")
        print()
        print("  Revisa los logs para detalles específicos de cada error.")
        print("  Los archivos con errores pueden estar en:")
        print("    - data/quarantine/ (archivos en cuarentena)")
        print("    - Estado 'error' o 'revisar' en la base de datos")
    else:
        print("  ✅ No se detectaron errores en el procesamiento")
    
    print()
    
    # Timestamps
    print("⏰ TIMESTAMPS:")
    print("-" * 70)
    if stats.get('last_sync_time_before'):
        print(f"  Última sync antes: {stats['last_sync_time_before']}")
    if stats.get('last_sync_time_after'):
        print(f"  Última sync después: {stats['last_sync_time_after']}")
    print()
    
    # Guardar reporte en archivo
    report_file = project_root / 'data' / f'reporte_carga_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.json'
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'stats': stats,
        'bd_total': total_facturas,
        'bd_estados': {estado: count for estado, count in estados},
        'campos_fiscales': {
            'impuestos_total': con_impuestos,
            'base_imponible': con_base,
            'iva_porcentaje': con_iva
        }
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"💾 Reporte guardado en: {report_file}")
    print()
    
    db.close()
    
    return report_file

def main():
    """Función principal"""
    try:
        # Paso 1: Resetear sync time
        if not reset_sync_time_to_january_2024():
            print("❌ Error reseteando sync time. Abortando.")
            return 1
        
        # Paso 2: Ejecutar pipeline
        print()
        stats = run_incremental_pipeline()
        
        # Paso 3: Generar reporte
        report_file = generate_detailed_report(stats)
        
        print("="*70)
        print("✅ PROCESO COMPLETADO")
        print("="*70)
        print()
        print(f"📄 Reporte detallado guardado en: {report_file}")
        
        return 0
        
    except KeyboardInterrupt:
        print()
        print("⚠️  Ejecución interrumpida por usuario")
        return 130
    except Exception as e:
        logger.error(f"Error crítico: {e}", exc_info=True)
        print()
        print("❌ ERROR CRÍTICO:")
        print(f"   {str(e)}")
        print()
        print("Revisa los logs para más detalles.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

