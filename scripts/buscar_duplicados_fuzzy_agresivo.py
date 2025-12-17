#!/usr/bin/env python3
"""
Búsqueda agresiva de duplicados usando fuzzy matching
Encuentra y fusiona proveedores que el algoritmo normal no detectó
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import Database
from src.db.models import ProveedorMaestro, Factura
from rapidfuzz import fuzz
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def buscar_y_fusionar_duplicados(umbral: float = 92.0, dry_run: bool = True):
    """
    Buscar duplicados usando fuzzy matching agresivo y fusionarlos
    
    Args:
        umbral: Score mínimo de similitud para considerar duplicado (0-100)
        dry_run: Si True, solo muestra lo que haría
    """
    db = Database()
    
    with db.get_session() as session:
        todos = session.query(ProveedorMaestro).filter(
            ProveedorMaestro.activo == True
        ).all()
        
        logger.info(f"📊 Analizando {len(todos)} proveedores maestros...")
        
        fusiones_encontradas = []
        procesados = set()
        
        for i, p1 in enumerate(todos):
            if p1.id in procesados:
                continue
            
            nombre1 = p1.nombre_canonico.upper()
            grupo = [p1]
            
            for j, p2 in enumerate(todos[i+1:], start=i+1):
                if p2.id in procesados:
                    continue
                
                nombre2 = p2.nombre_canonico.upper()
                
                # Calcular similitud con múltiples métodos
                score1 = fuzz.token_set_ratio(nombre1, nombre2)
                score2 = fuzz.token_sort_ratio(nombre1, nombre2)
                score3 = fuzz.WRatio(nombre1, nombre2)
                
                score_final = max(score1, score2, score3)
                
                if score_final >= umbral:
                    grupo.append(p2)
                    procesados.add(p2.id)
            
            if len(grupo) > 1:
                # Seleccionar el proveedor principal (el que tiene más facturas)
                grupo_ordenado = sorted(grupo, key=lambda x: x.total_facturas, reverse=True)
                maestro_objetivo = grupo_ordenado[0]
                
                fusiones_encontradas.append({
                    'objetivo': maestro_objetivo,
                    'variantes': grupo_ordenado[1:],
                    'score': score_final
                })
                procesados.add(p1.id)
        
        logger.info(f"🔍 Encontrados {len(fusiones_encontradas)} grupos de duplicados")
        
        if not fusiones_encontradas:
            logger.info("✅ No se encontraron duplicados adicionales")
            return
        
        # Mostrar y ejecutar fusiones
        total_fusionados = 0
        for fusion in fusiones_encontradas:
            variantes = fusion['variantes']
            total_fusionados += len(variantes)
            objetivo = fusion['objetivo']
            variantes = fusion['variantes']
            
            logger.info(f"\n📦 Fusionar {len(variantes)} proveedores → '{objetivo.nombre_canonico}'")
            logger.info(f"   Objetivo: {objetivo.total_facturas} facturas, {objetivo.total_importe}€")
            
            for variante in variantes:
                logger.info(f"   - '{variante.nombre_canonico}' ({variante.total_facturas} facturas, {variante.total_importe}€)")
                
                if not dry_run:
                    try:
                        # Reasignar facturas
                        facturas_actualizadas = session.query(Factura).filter(
                            Factura.proveedor_maestro_id == variante.id
                        ).update({
                            'proveedor_maestro_id': objetivo.id,
                            'proveedor_text': objetivo.nombre_canonico
                        }, synchronize_session=False)
                        
                        # Actualizar también por proveedor_text
                        session.query(Factura).filter(
                            Factura.proveedor_text == variante.nombre_canonico,
                            Factura.proveedor_maestro_id.is_(None)
                        ).update({
                            'proveedor_maestro_id': objetivo.id,
                            'proveedor_text': objetivo.nombre_canonico
                        }, synchronize_session=False)
                        
                        # Sumar contadores
                        objetivo.total_facturas += variante.total_facturas
                        objetivo.total_importe = Decimal(str(objetivo.total_importe)) + Decimal(str(variante.total_importe))
                        
                        # Agregar a nombres alternativos
                        if variante.nombre_canonico not in objetivo.nombres_alternativos:
                            objetivo.nombres_alternativos.append(variante.nombre_canonico)
                        
                        # Eliminar variante
                        variante.activo = False
                        session.delete(variante)
                        
                        session.flush()
                        
                        logger.info(f"      ✅ Fusionado ({facturas_actualizadas} facturas actualizadas)")
                        total_fusionados += 1
                        
                    except Exception as e:
                        logger.error(f"      ❌ Error: {e}")
                        session.rollback()
        
        if not dry_run:
            session.commit()
            logger.info(f"\n✅ Total fusionados: {total_fusionados} proveedores")
        else:
            logger.info(f"\n🔍 DRY RUN: {total_fusionados} proveedores se fusionarían")
            logger.info("💡 Ejecuta con --apply para aplicar los cambios")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Buscar y fusionar duplicados con fuzzy matching agresivo')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios')
    parser.add_argument('--umbral', type=float, default=92.0, help='Umbral de similitud (default: 92.0)')
    args = parser.parse_args()
    
    buscar_y_fusionar_duplicados(umbral=args.umbral, dry_run=not args.apply)

