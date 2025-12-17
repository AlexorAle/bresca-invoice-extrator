#!/usr/bin/env python3
"""
Script de limpieza completa de la base de datos
Elimina todos los datos de todas las tablas para preparar una carga nueva
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import Database
from src.db.models import Base
from src.logging_conf import get_logger
from sqlalchemy import text, inspect

logger = get_logger(__name__, component="backend")

def limpiar_base_datos():
    """
    Limpiar todas las tablas de la base de datos
    """
    try:
        logger.info("="*60)
        logger.info("INICIANDO LIMPIEZA COMPLETA DE BASE DE DATOS")
        logger.info("="*60)
        
        # Conectar a la base de datos
        db = Database()
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        logger.info(f"Tablas encontradas: {', '.join(tables)}")
        
        # Obtener conteos antes de limpiar
        counts_before = {}
        with db.get_session() as session:
            for table in tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    counts_before[table] = count
                    logger.info(f"  {table}: {count} registros")
                except Exception as e:
                    logger.warning(f"  {table}: Error al contar ({e})")
                    counts_before[table] = 0
        
        # Confirmar limpieza
        total_registros = sum(counts_before.values())
        logger.info(f"\nTotal de registros a eliminar: {total_registros}")
        logger.info("\n⚠️  ADVERTENCIA: Esta operación eliminará TODOS los datos.")
        logger.info("   Procediendo con la limpieza...")
        
        # Limpiar cada tabla
        logger.info("\nIniciando limpieza...")
        with db.get_session() as session:
            for table in tables:
                try:
                    # Desactivar foreign keys temporalmente si es PostgreSQL
                    if 'postgresql' in str(db.database_url):
                        session.execute(text("SET session_replication_role = 'replica'"))
                    
                    # Eliminar todos los registros
                    result = session.execute(text(f"DELETE FROM {table}"))
                    deleted = result.rowcount
                    
                    # Reactivar foreign keys
                    if 'postgresql' in str(db.database_url):
                        session.execute(text("SET session_replication_role = 'origin'"))
                    
                    session.commit()
                    logger.info(f"  ✅ {table}: {deleted} registros eliminados")
                    
                except Exception as e:
                    logger.error(f"  ❌ {table}: Error al limpiar - {e}")
                    session.rollback()
        
        # Verificar limpieza
        logger.info("\nVerificando limpieza...")
        counts_after = {}
        with db.get_session() as session:
            for table in tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    counts_after[table] = count
                    if count == 0:
                        logger.info(f"  ✅ {table}: Limpia ({count} registros)")
                    else:
                        logger.warning(f"  ⚠️  {table}: Aún tiene {count} registros")
                except Exception as e:
                    logger.error(f"  ❌ {table}: Error al verificar - {e}")
        
        # Resumen
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DE LIMPIEZA")
        logger.info("="*60)
        for table in tables:
            antes = counts_before.get(table, 0)
            despues = counts_after.get(table, 0)
            logger.info(f"{table:20} | Antes: {antes:6} | Después: {despues:6} | Eliminados: {antes - despues:6}")
        
        total_eliminados = sum(counts_before.values()) - sum(counts_after.values())
        logger.info(f"\nTotal eliminado: {total_eliminados} registros")
        logger.info("="*60)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Limpieza cancelada por el usuario")
        return False
    except Exception as e:
        logger.error(f"❌ Error durante la limpieza: {e}", exc_info=True)
        return False

def limpiar_cuarentena():
    """
    Limpiar archivos de cuarentena
    """
    try:
        quarantine_path = Path(os.getenv('QUARANTINE_PATH', 'data/quarantine'))
        
        # Si es ruta absoluta, ajustar
        if quarantine_path.is_absolute():
            parts = quarantine_path.parts
            if 'data' in parts and 'quarantine' in parts:
                data_idx = parts.index('data')
                quarantine_path = Path('/app') / Path(*parts[data_idx:])
            else:
                quarantine_path = Path('/app') / quarantine_path
        
        logger.info(f"\nLimpiando archivos de cuarentena en: {quarantine_path}")
        
        if not quarantine_path.exists():
            logger.info("  ⚠️  Directorio de cuarentena no existe")
            return 0
        
        # Contar archivos
        files = list(quarantine_path.rglob('*'))
        file_count = len([f for f in files if f.is_file()])
        dir_count = len([f for f in files if f.is_dir()])
        
        logger.info(f"  Archivos encontrados: {file_count}")
        logger.info(f"  Directorios encontrados: {dir_count}")
        
        if file_count == 0:
            logger.info("  ✅ Directorio de cuarentena ya está vacío")
            return 0
        
        # Eliminar todo
        import shutil
        for item in quarantine_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        
        logger.info(f"  ✅ {file_count} archivos eliminados de cuarentena")
        return file_count
        
    except Exception as e:
        logger.error(f"❌ Error limpiando cuarentena: {e}", exc_info=True)
        return 0

if __name__ == "__main__":
    logger.info("Iniciando proceso de limpieza completa...")
    
    # Limpiar base de datos
    success_bd = limpiar_base_datos()
    
    # Limpiar cuarentena
    files_quarantine = limpiar_cuarentena()
    
    if success_bd:
        logger.info("\n✅ Limpieza completada exitosamente")
        sys.exit(0)
    else:
        logger.error("\n❌ Limpieza completada con errores")
        sys.exit(1)
