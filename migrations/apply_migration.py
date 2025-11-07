#!/usr/bin/env python3
"""
Script para aplicar migración 001: Sistema de Detección de Duplicados

Uso:
    python3 migrations/apply_migration.py [--rollback]
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from db.database import get_database
from logging_conf import get_logger
from security.secrets import load_env

logger = get_logger(__name__)

def apply_migration(db, migration_file: Path):
    """Aplicar migración SQL desde archivo"""
    logger.info(f"Aplicando migración: {migration_file.name}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    with db.get_session() as session:
        try:
            session.execute(sql)
            session.commit()
            
            logger.info(f"✅ Migración {migration_file.name} aplicada exitosamente")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error aplicando migración: {e}", exc_info=True)
            return False

def rollback_migration(db):
    """Revertir migración 001"""
    logger.warning("Revirtiendo migración 001...")
    
    rollback_sql = """
    DROP INDEX IF EXISTS idx_facturas_hash_contenido_unique;
    ALTER TABLE facturas DROP CONSTRAINT IF EXISTS check_estado_values;
    ALTER TABLE facturas ADD CONSTRAINT check_estado_values 
        CHECK (estado IN ('procesado', 'pendiente', 'error', 'revisar'));
    DROP INDEX IF EXISTS idx_facturas_proveedor_numero;
    DROP INDEX IF EXISTS idx_facturas_fecha_emision;
    DROP INDEX IF EXISTS idx_facturas_estado;
    DROP INDEX IF EXISTS idx_facturas_duplicate_check;
    DROP INDEX IF EXISTS idx_facturas_drive_modified;
    ALTER TABLE facturas DROP COLUMN IF EXISTS revision;
    ALTER TABLE facturas DROP COLUMN IF EXISTS drive_modified_time;
    ALTER TABLE ingest_events DROP COLUMN IF EXISTS hash_contenido;
    ALTER TABLE ingest_events DROP COLUMN IF EXISTS decision;
    DROP VIEW IF EXISTS v_duplicate_analysis;
    DROP FUNCTION IF EXISTS get_last_ingest_timestamp();
    """
    
    with db.get_session() as session:
        try:
            session.execute(rollback_sql)
            session.commit()
            
            logger.info("✅ Migración revertida exitosamente")
            return True
        
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error revirtiendo migración: {e}", exc_info=True)
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Aplicar migración de detección de duplicados')
    parser.add_argument('--rollback', action='store_true', help='Revertir la migración')
    args = parser.parse_args()
    
    load_env()
    
    logger.info("Conectando a base de datos...")
    db = get_database()
    
    if args.rollback:
        success = rollback_migration(db)
    else:
        migration_file = Path(__file__).parent / '001_add_duplicate_detection.sql'
        
        if not migration_file.exists():
            logger.error(f"Archivo de migración no encontrado: {migration_file}")
            sys.exit(1)
        
        success = apply_migration(db, migration_file)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
