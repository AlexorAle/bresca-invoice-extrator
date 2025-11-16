#!/usr/bin/env python3
"""
Script para limpiar completamente la base de datos
Elimina todas las facturas, eventos y estados de sincronización
"""
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.db.database import Database
from src.db.repositories import FacturaRepository, EventRepository, SyncStateRepository
from src.logging_conf import get_logger

load_env()
logger = get_logger(__name__)

def main():
    print("="*70)
    print("🧹 LIMPIEZA COMPLETA DE BASE DE DATOS")
    print("="*70)
    print()
    
    # Confirmar
    respuesta = input("⚠️  ¿Estás seguro de que quieres eliminar TODOS los datos? (escribe 'SI' para confirmar): ")
    if respuesta != 'SI':
        print("❌ Operación cancelada")
        return
    
    db = Database()
    
    try:
        factura_repo = FacturaRepository(db)
        event_repo = EventRepository(db)
        sync_repo = SyncStateRepository(db)
        
        with db.get_session() as session:
            from src.db.models import Factura, IngestEvent
            
            # Contar antes de eliminar
            total_facturas = session.query(Factura).count()
            total_eventos = session.query(IngestEvent).count()
            
            print(f"\n📊 Datos a eliminar:")
            print(f"   - Facturas: {total_facturas}")
            print(f"   - Eventos: {total_eventos}")
            print()
            
            # Eliminar eventos primero (foreign keys)
            print("🗑️  Eliminando eventos...")
            session.query(IngestEvent).delete()
            session.commit()
            print("   ✅ Eventos eliminados")
            
            # Eliminar facturas
            print("🗑️  Eliminando facturas...")
            session.query(Factura).delete()
            session.commit()
            print("   ✅ Facturas eliminadas")
            
            # Limpiar sync_state (eliminar registro en lugar de poner None)
            print("🗑️  Limpiando estados de sincronización...")
            with db.get_session() as session:
                from src.db.models import SyncState
                session.query(SyncState).filter(SyncState.key == 'last_sync_time').delete()
                session.commit()
            print("   ✅ Estados limpiados")
            
            # Verificar
            facturas_restantes = session.query(Factura).count()
            eventos_restantes = session.query(IngestEvent).count()
            
            print()
            print("="*70)
            print("✅ LIMPIEZA COMPLETADA")
            print("="*70)
            print(f"Facturas restantes: {facturas_restantes}")
            print(f"Eventos restantes: {eventos_restantes}")
            print()
            print("✅ Base de datos lista para pruebas desde cero")
    
    except Exception as e:
        logger.error(f"Error durante la limpieza: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()

