#!/usr/bin/env python3
"""
Script para actualizar proveedor_maestro_id en facturas después de agregar la columna
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import Database
from src.db.models import Factura, ProveedorMaestro
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def actualizar_proveedor_maestro_id():
    """Actualizar proveedor_maestro_id en todas las facturas"""
    db = Database()
    
    with db.get_session() as session:
        # Verificar que la columna existe
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        columnas = [col['name'] for col in inspector.get_columns('facturas')]
        
        if 'proveedor_maestro_id' not in columnas:
            logger.error("❌ La columna proveedor_maestro_id no existe en facturas")
            logger.error("   Ejecuta primero el SQL para agregar la columna")
            return
        
        logger.info("✅ Columna proveedor_maestro_id encontrada")
        
        # Actualizar facturas usando SQL directo (más eficiente)
        logger.info("🔄 Actualizando proveedor_maestro_id en facturas...")
        
        resultado = session.execute(text("""
            UPDATE facturas f
            SET proveedor_maestro_id = pm.id
            FROM proveedores_maestros pm
            WHERE f.proveedor_text = pm.nombre_canonico
            AND f.proveedor_maestro_id IS NULL;
        """))
        
        session.commit()
        
        facturas_actualizadas = resultado.rowcount
        logger.info(f"✅ {facturas_actualizadas} facturas actualizadas con proveedor_maestro_id")
        
        # Verificar cuántas quedan sin actualizar
        sin_maestro = session.query(Factura).filter(
            Factura.proveedor_maestro_id.is_(None),
            Factura.proveedor_text.isnot(None)
        ).count()
        
        if sin_maestro > 0:
            logger.warning(f"⚠️ {sin_maestro} facturas sin proveedor_maestro_id asignado")
        else:
            logger.info("✅ Todas las facturas tienen proveedor_maestro_id")


if __name__ == "__main__":
    actualizar_proveedor_maestro_id()

