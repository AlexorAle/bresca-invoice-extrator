#!/usr/bin/env python3
"""
CORRECCIÓN MANUAL + FUZZY REFORZADO PARA LOS GRANDES DUPLICADOS

Fusiona proveedores que sabemos que son el mismo pero el algoritmo no detectó
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import Database
from src.db.models import ProveedorMaestro, Factura
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Lista de fusiones forzadas (las que SÉ que son el mismo proveedor)
# Formato: {nombre_variante: nombre_canonico_final}
# NOTA: Los nombres deben coincidir EXACTAMENTE con los que existen en la BD
FUSIONES_FORZADAS = {
    # SUPERMERCADOS H. MARTIN - Fusionar ANADLUZA a ANDALUZA (el que tiene más facturas: 465 vs 15)
    "ANADLUZA DE SUPERMERCADOS H. MARTIN, S.L.": "ANDALUZA DE SUPERMERCADOS H. MARTIN, S.L.",
    
    # COVERMANAGER / RESTAURANT BOOKING - Fusionar "Restaurant Booking" a "Covermanager Booking"
    # (Restaurant Booking tiene más facturas: 174 vs 27, pero Covermanager es el nombre canónico)
    "Restaurant Booking & Distribution Services S.L.": "Covermanager Booking & Distribution Services S.L.",
    
    # ECOTIENDAS - Error tipográfico: "Biogorila" → "Biogloría"
    "Ecotiendas Biogorila SL. (HERB. LA CENTRAL)": "Ecotiendas Biogloría SL. (HERB. LA CENTRAL)",
    
    # BANCO SABADELL - Solo fusionar "Sabadell Leasing" si es realmente el mismo banco
    # NOTA: "BANSABADELL VIDA" es un producto diferente (seguros de vida), NO fusionar
    # "Sabadell Leasing" podría ser el mismo banco, pero es un producto específico
    # Por ahora NO fusionamos estos porque son productos diferentes del mismo banco
}


def corregir_duplicados_graves(dry_run: bool = True):
    """
    Corregir duplicados críticos usando fusiones forzadas
    """
    db = Database()
    corregidos = 0
    errores = []
    
    with db.get_session() as session:
        # Obtener todos los proveedores maestros
        todos_proveedores = session.query(ProveedorMaestro).filter(
            ProveedorMaestro.activo == True
        ).all()
        
        logger.info(f"📊 Total proveedores maestros a revisar: {len(todos_proveedores)}")
        
        # Crear mapeo nombre -> proveedor
        proveedores_por_nombre = {}
        for pm in todos_proveedores:
            clave = pm.nombre_canonico.strip().upper()
            if clave not in proveedores_por_nombre:
                proveedores_por_nombre[clave] = []
            proveedores_por_nombre[clave].append(pm)
        
        # Procesar fusiones
        for nombre_variante, nombre_canonico in FUSIONES_FORZADAS.items():
            nombre_variante_upper = nombre_variante.strip().upper()
            nombre_canonico_upper = nombre_canonico.strip().upper()
            
            # Buscar proveedor variante
            if nombre_variante_upper not in proveedores_por_nombre:
                continue
            
            proveedores_variante = proveedores_por_nombre[nombre_variante_upper]
            
            # Buscar proveedor canónico objetivo
            if nombre_canonico_upper not in proveedores_por_nombre:
                logger.warning(f"⚠️ No se encontró proveedor canónico: {nombre_canonico}")
                continue
            
            proveedores_canonico = proveedores_por_nombre[nombre_canonico_upper]
            maestro_objetivo = proveedores_canonico[0]  # Tomar el primero
            
            # Fusionar cada variante
            for pm_variante in proveedores_variante:
                if pm_variante.id == maestro_objetivo.id:
                    continue  # Ya es el mismo
                
                try:
                    if dry_run:
                        logger.info(
                            f"🔍 [DRY RUN] Fusionar: '{pm_variante.nombre_canonico}' "
                            f"→ '{maestro_objetivo.nombre_canonico}' "
                            f"({pm_variante.total_facturas} facturas, {pm_variante.total_importe}€)"
                        )
                    else:
                        # Reasignar todas las facturas
                        facturas_actualizadas = session.query(Factura).filter(
                            Factura.proveedor_maestro_id == pm_variante.id
                        ).update({
                            'proveedor_maestro_id': maestro_objetivo.id,
                            'proveedor_text': maestro_objetivo.nombre_canonico
                        }, synchronize_session=False)
                        
                        # Actualizar también facturas que tienen proveedor_text igual
                        session.query(Factura).filter(
                            Factura.proveedor_text == pm_variante.nombre_canonico,
                            Factura.proveedor_maestro_id.is_(None)
                        ).update({
                            'proveedor_maestro_id': maestro_objetivo.id,
                            'proveedor_text': maestro_objetivo.nombre_canonico
                        }, synchronize_session=False)
                        
                        # Sumar contadores
                        maestro_objetivo.total_facturas += pm_variante.total_facturas
                        maestro_objetivo.total_importe = Decimal(str(maestro_objetivo.total_importe)) + Decimal(str(pm_variante.total_importe))
                        
                        # Agregar nombre a alternativos
                        if pm_variante.nombre_canonico not in maestro_objetivo.nombres_alternativos:
                            maestro_objetivo.nombres_alternativos.append(pm_variante.nombre_canonico)
                        
                        # Marcar como inactivo y luego eliminar
                        pm_variante.activo = False
                        session.delete(pm_variante)
                        
                        session.flush()
                        
                        logger.info(
                            f"✅ Fusionado: '{pm_variante.nombre_canonico}' "
                            f"→ '{maestro_objetivo.nombre_canonico}' "
                            f"({facturas_actualizadas} facturas actualizadas)"
                        )
                    
                    corregidos += 1
                    
                except Exception as e:
                    error_msg = f"Error fusionando {pm_variante.nombre_canonico}: {e}"
                    logger.error(error_msg)
                    errores.append(error_msg)
                    session.rollback()
        
        if not dry_run:
            session.commit()
            logger.info(f"\n✅ Corrección completada: {corregidos} proveedores fusionados")
        else:
            logger.info(f"\n🔍 DRY RUN: {corregidos} proveedores se fusionarían")
            logger.info("💡 Ejecuta con --apply para aplicar los cambios")
        
        if errores:
            logger.warning(f"⚠️ Errores: {len(errores)}")
            for error in errores:
                logger.warning(f"   - {error}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Corregir duplicados críticos')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios (sin esto, solo muestra)')
    args = parser.parse_args()
    
    corregir_duplicados_graves(dry_run=not args.apply)

