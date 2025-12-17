#!/usr/bin/env python3
"""
Script para normalizar nombres de proveedores y fusionar duplicados

Este script:
1. Lee todos los proveedores de la BD
2. Normaliza los nombres
3. Agrupa proveedores con nombres similares
4. Fusiona los duplicados manteniendo el nombre canónico
5. Actualiza todas las referencias en la tabla facturas
"""
import sys
import os
from collections import defaultdict
from typing import Dict, List, Tuple

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import Database
from src.db.models import Proveedor, Factura
from src.utils.proveedor_normalizer import normalize_proveedor_name, get_canonical_name
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_and_merge_proveedores(dry_run: bool = True):
    """
    Normaliza y fusiona proveedores duplicados
    
    Args:
        dry_run: Si True, solo muestra lo que haría sin modificar la BD
    """
    db = Database()
    
    with db.get_session() as session:
        # 1. Leer todos los proveedores
        proveedores = session.query(Proveedor).all()
        logger.info(f"📊 Total de proveedores en BD: {len(proveedores)}")
        
        # 2. Agrupar por nombre normalizado
        grupos: Dict[str, List[Tuple[int, str]]] = defaultdict(list)
        
        for prov in proveedores:
            nombre_norm = normalize_proveedor_name(prov.nombre)
            grupos[nombre_norm].append((prov.id, prov.nombre))
        
        # 3. Identificar duplicados
        duplicados = {k: v for k, v in grupos.items() if len(v) > 1}
        
        if not duplicados:
            logger.info("✅ No se encontraron proveedores duplicados")
            return
        
        logger.info(f"🔍 Se encontraron {len(duplicados)} grupos de proveedores duplicados")
        print("\n" + "="*80)
        print("RESUMEN DE DUPLICADOS")
        print("="*80)
        
        total_facturas_afectadas = 0
        
        for nombre_norm, provs in sorted(duplicados.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n📦 Grupo: {nombre_norm}")
            print(f"   Variaciones: {len(provs)}")
            
            # Contar facturas por cada proveedor
            for prov_id, prov_nombre in provs:
                count_facturas = session.query(Factura).filter(
                    Factura.proveedor_id == prov_id
                ).count()
                print(f"   - ID {prov_id}: '{prov_nombre}' ({count_facturas} facturas)")
                total_facturas_afectadas += count_facturas
            
            # Obtener nombre canónico
            nombres = [prov[1] for prov in provs]
            nombre_canonico = get_canonical_name(nombres)
            print(f"   ✅ Nombre canónico seleccionado: '{nombre_canonico}'")
        
        print("\n" + "="*80)
        print(f"📊 TOTALES:")
        print(f"   - Grupos duplicados: {len(duplicados)}")
        print(f"   - Proveedores totales en duplicados: {sum(len(v) for v in duplicados.values())}")
        print(f"   - Proveedores que se eliminarán: {sum(len(v) - 1 for v in duplicados.values())}")
        print(f"   - Facturas afectadas: {total_facturas_afectadas}")
        print("="*80 + "\n")
        
        if dry_run:
            logger.info("🔍 DRY RUN: No se realizaron cambios en la BD")
            logger.info("💡 Ejecuta con --apply para aplicar los cambios")
            return
        
        # 4. Fusionar proveedores
        logger.info("🔄 Iniciando fusión de proveedores...")
        
        fusiones_exitosas = 0
        
        for nombre_norm, provs in duplicados.items():
            # Obtener nombre canónico
            nombres = [prov[1] for prov in provs]
            nombre_canonico = get_canonical_name(nombres)
            
            # Encontrar el proveedor con el nombre canónico (o el primero si no existe)
            proveedor_principal = None
            for prov_id, prov_nombre in provs:
                if prov_nombre == nombre_canonico:
                    proveedor_principal = prov_id
                    break
            
            if not proveedor_principal:
                proveedor_principal = provs[0][0]
            
            # IDs de proveedores a fusionar (todos menos el principal)
            ids_a_fusionar = [prov[0] for prov in provs if prov[0] != proveedor_principal]
            
            if not ids_a_fusionar:
                continue
            
            try:
                # Actualizar todas las facturas para que apunten al proveedor principal
                session.query(Factura).filter(
                    Factura.proveedor_id.in_(ids_a_fusionar)
                ).update(
                    {Factura.proveedor_id: proveedor_principal},
                    synchronize_session=False
                )
                
                # Eliminar proveedores duplicados
                session.query(Proveedor).filter(
                    Proveedor.id.in_(ids_a_fusionar)
                ).delete(synchronize_session=False)
                
                # Actualizar el nombre del proveedor principal al canónico
                session.query(Proveedor).filter(
                    Proveedor.id == proveedor_principal
                ).update(
                    {Proveedor.nombre: nombre_canonico},
                    synchronize_session=False
                )
                
                session.commit()
                fusiones_exitosas += 1
                logger.info(f"✅ Fusionados {len(ids_a_fusionar)} proveedores en '{nombre_canonico}' (ID {proveedor_principal})")
                
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Error fusionando grupo '{nombre_norm}': {e}")
        
        logger.info(f"\n🎉 Proceso completado:")
        logger.info(f"   - Grupos fusionados: {fusiones_exitosas}/{len(duplicados)}")
        logger.info(f"   - Proveedores eliminados: {sum(len(v) - 1 for v in duplicados.values())}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Normalizar y fusionar proveedores duplicados')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios (sin esto, solo muestra)')
    args = parser.parse_args()
    
    normalize_and_merge_proveedores(dry_run=not args.apply)

