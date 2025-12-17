#!/usr/bin/env python3
"""
Script de migración a proveedores_maestros

Este script:
1. Lee todos_los_proveedores.json
2. Normaliza y agrupa proveedores similares
3. Crea tabla proveedores_maestros
4. Actualiza todas las facturas con nombres canónicos
"""
import sys
import os
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import Database
from src.db.models import ProveedorMaestro, Factura, Base
from src.utils.proveedor_normalizer_v2 import (
    normalizar_nombre_proveedor,
    seleccionar_nombre_canonico,
    calcular_similitud
)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cargar_datos_proveedores() -> List[Dict]:
    """Cargar todos los proveedores del JSON"""
    json_path = os.path.join(os.path.dirname(__file__), '..', 'todos_los_proveedores.json')
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"No se encontró el archivo: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Combinar proveedores de tabla y de campo text
    todos_proveedores = []
    
    # De la tabla
    for prov in data.get('proveedores_de_tabla', []):
        todos_proveedores.append({
            'nombre': prov['nombre'],
            'nif_cif': prov.get('nif_cif'),
            'total_facturas': prov.get('total_facturas', 0),
            'total_importe': float(prov.get('total_importe', 0)),
            'categoria': prov.get('categoria'),
            'fuente': 'tabla'
        })
    
    # Del campo text
    for prov in data.get('proveedores_de_campo_text', []):
        todos_proveedores.append({
            'nombre': prov['nombre'],
            'nif_cif': None,  # No tenemos NIF en proveedor_text
            'total_facturas': prov.get('total_facturas', 0),
            'total_importe': float(prov.get('total_importe', 0)),
            'categoria': None,
            'fuente': 'texto'
        })
    
    logger.info(f"📊 Total de proveedores cargados: {len(todos_proveedores)}")
    return todos_proveedores


def agrupar_proveedores_similares(proveedores: List[Dict], umbral_similitud: float = 92.0) -> List[List[Dict]]:
    """
    Agrupa proveedores similares usando normalización + fuzzy matching
    
    Args:
        proveedores: Lista de proveedores
        umbral_similitud: Score mínimo para considerar match (0-100)
    
    Returns:
        Lista de grupos, cada grupo contiene proveedores similares
    """
    # Normalizar todos los nombres
    proveedores_normalizados = []
    for prov in proveedores:
        nombre_norm = normalizar_nombre_proveedor(prov['nombre'])
        proveedores_normalizados.append({
            **prov,
            'nombre_normalizado': nombre_norm
        })
    
    # Agrupar por matching
    grupos = []
    procesados = set()
    
    for i, prov1 in enumerate(proveedores_normalizados):
        if prov1['nombre'] in procesados:
            continue
        
        grupo = [prov1]
        nombre_norm1 = prov1['nombre_normalizado']
        
        # Buscar matches
        for j, prov2 in enumerate(proveedores_normalizados[i+1:], start=i+1):
            if prov2['nombre'] in procesados:
                continue
            
            nombre_norm2 = prov2['nombre_normalizado']
            
            # CAPA 1: Si tienen el mismo NIF, son el mismo
            if (prov1.get('nif_cif') and prov2.get('nif_cif') and 
                prov1['nif_cif'].strip().upper() == prov2['nif_cif'].strip().upper()):
                grupo.append(prov2)
                procesados.add(prov2['nombre'])
                continue
            
            # CAPA 2: Fuzzy matching
            score = calcular_similitud(nombre_norm1, nombre_norm2)
            
            if score >= umbral_similitud:
                grupo.append(prov2)
                procesados.add(prov2['nombre'])
        
        grupos.append(grupo)
        procesados.add(prov1['nombre'])
    
    logger.info(f"🔍 Grupos de proveedores similares: {len(grupos)}")
    logger.info(f"   - Grupos únicos (1 proveedor): {sum(1 for g in grupos if len(g) == 1)}")
    logger.info(f"   - Grupos con duplicados: {sum(1 for g in grupos if len(g) > 1)}")
    
    return grupos


def crear_tabla_proveedores_maestros(db: Database):
    """Crear la tabla proveedores_maestros si no existe"""
    from sqlalchemy import inspect
    
    engine = db.engine
    
    # Verificar si la tabla ya existe
    inspector = inspect(engine)
    if 'proveedores_maestros' in inspector.get_table_names():
        logger.info("✅ Tabla proveedores_maestros ya existe")
        return
    
    # Crear tabla
    logger.info("📋 Creando tabla proveedores_maestros...")
    ProveedorMaestro.__table__.create(engine, checkfirst=True)
    logger.info("✅ Tabla proveedores_maestros creada")


def migrar_proveedores(db: Database, grupos: List[List[Dict]], dry_run: bool = True) -> Dict:
    """
    Migrar proveedores a tabla maestra
    
    Returns:
        Diccionario con estadísticas de migración
    """
    stats = {
        'total_grupos': len(grupos),
        'total_proveedores_maestros': 0,
        'total_facturas': 0,
        'total_importe': 0.0,
        'proveedores_creados': [],
        'errores': []
    }
    
    if dry_run:
        logger.info("🔍 DRY RUN: No se realizarán cambios en la BD")
        logger.info("💡 Ejecuta con --apply para aplicar los cambios")
    
    with db.get_session() as session:
        for idx, grupo in enumerate(grupos, 1):
            try:
                # Seleccionar nombre canónico
                nombre_canonico, nif_cif = seleccionar_nombre_canonico(grupo)
                
                # Calcular totales del grupo
                total_facturas = sum(p.get('total_facturas', 0) for p in grupo)
                total_importe = sum(p.get('total_importe', 0) for p in grupo)
                
                # Obtener categoría (si alguno la tiene)
                categoria = None
                for p in grupo:
                    if p.get('categoria'):
                        categoria = p['categoria']
                        break
                
                # Nombres alternativos
                nombres_alternativos = [p['nombre'] for p in grupo if p['nombre'] != nombre_canonico]
                
                if dry_run:
                    logger.info(f"\n📦 Grupo {idx}/{len(grupos)}: {nombre_canonico}")
                    logger.info(f"   Variaciones: {len(grupo)}")
                    logger.info(f"   Facturas: {total_facturas}, Importe: {total_importe:.2f}€")
                    if nombres_alternativos:
                        logger.info(f"   Alternativos: {', '.join(nombres_alternativos[:3])}...")
                else:
                    # Buscar si ya existe
                    proveedor_existente = session.query(ProveedorMaestro).filter(
                        ProveedorMaestro.nombre_canonico == nombre_canonico
                    ).first()
                    
                    if proveedor_existente:
                        # Actualizar
                        proveedor_existente.total_facturas += total_facturas
                        # Convertir a Decimal para evitar error de tipos
                        from decimal import Decimal
                        proveedor_existente.total_importe = Decimal(str(proveedor_existente.total_importe)) + Decimal(str(total_importe))
                        # Agregar nombres alternativos nuevos
                        for alt in nombres_alternativos:
                            if alt not in proveedor_existente.nombres_alternativos:
                                proveedor_existente.nombres_alternativos.append(alt)
                        if nif_cif and not proveedor_existente.nif_cif:
                            proveedor_existente.nif_cif = nif_cif
                        if categoria and not proveedor_existente.categoria:
                            proveedor_existente.categoria = categoria
                        proveedor_maestro = proveedor_existente
                    else:
                        # Crear nuevo
                        from decimal import Decimal
                        proveedor_maestro = ProveedorMaestro(
                            nombre_canonico=nombre_canonico,
                            nif_cif=nif_cif,
                            nombres_alternativos=nombres_alternativos,
                            total_facturas=total_facturas,
                            total_importe=Decimal(str(total_importe)),
                            categoria=categoria,
                            activo=True
                        )
                        session.add(proveedor_maestro)
                    
                    session.flush()
                    stats['proveedores_creados'].append({
                        'id': proveedor_maestro.id,
                        'nombre': nombre_canonico,
                        'variaciones': len(grupo)
                    })
                
                stats['total_proveedores_maestros'] += 1
                stats['total_facturas'] += total_facturas
                stats['total_importe'] += total_importe
                
            except Exception as e:
                error_msg = f"Error procesando grupo {idx}: {e}"
                logger.error(error_msg)
                stats['errores'].append(error_msg)
        
        if not dry_run:
            session.commit()
            logger.info(f"✅ {stats['total_proveedores_maestros']} proveedores maestros creados/actualizados")
    
    return stats


def actualizar_facturas(db: Database, grupos: List[List[Dict]], dry_run: bool = True):
    """
    Actualizar todas las facturas con nombres canónicos y proveedor_maestro_id
    """
    logger.info("🔄 Actualizando facturas...")
    
    if dry_run:
        logger.info("🔍 DRY RUN: No se actualizarán facturas")
        return
    
    with db.get_session() as session:
        # Crear mapeo nombre_original -> proveedor_maestro_id
        mapeo = {}
        
        for grupo in grupos:
            nombre_canonico, _ = seleccionar_nombre_canonico(grupo)
            
            # Buscar proveedor maestro
            proveedor_maestro = session.query(ProveedorMaestro).filter(
                ProveedorMaestro.nombre_canonico == nombre_canonico
            ).first()
            
            if not proveedor_maestro:
                logger.warning(f"⚠️ No se encontró proveedor maestro: {nombre_canonico}")
                continue
            
            # Mapear todas las variaciones
            for prov in grupo:
                mapeo[prov['nombre']] = {
                    'proveedor_maestro_id': proveedor_maestro.id,
                    'nombre_canonico': nombre_canonico
                }
        
        # Verificar si la columna proveedor_maestro_id existe
        from sqlalchemy import inspect, text
        inspector = inspect(session.bind)
        columnas = [col['name'] for col in inspector.get_columns('facturas')]
        tiene_columna_maestro = 'proveedor_maestro_id' in columnas
        
        # Actualizar facturas
        facturas_actualizadas = 0
        for nombre_original, datos in mapeo.items():
            if tiene_columna_maestro:
                resultado = session.query(Factura).filter(
                    Factura.proveedor_text == nombre_original
                ).update({
                    'proveedor_text': datos['nombre_canonico'],
                    'proveedor_maestro_id': datos['proveedor_maestro_id']
                }, synchronize_session=False)
            else:
                # Solo actualizar proveedor_text si no existe la columna
                resultado = session.query(Factura).filter(
                    Factura.proveedor_text == nombre_original
                ).update({
                    'proveedor_text': datos['nombre_canonico']
                }, synchronize_session=False)
            
            facturas_actualizadas += resultado
        
        session.commit()
        logger.info(f"✅ {facturas_actualizadas} facturas actualizadas")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrar a proveedores_maestros')
    parser.add_argument('--apply', action='store_true', help='Aplicar cambios (sin esto, solo muestra)')
    parser.add_argument('--umbral', type=float, default=92.0, help='Umbral de similitud (default: 92.0)')
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    try:
        # 1. Cargar datos
        logger.info("📂 Cargando datos de proveedores...")
        proveedores = cargar_datos_proveedores()
        
        # 2. Agrupar similares
        logger.info("🔍 Agrupando proveedores similares...")
        grupos = agrupar_proveedores_similares(proveedores, umbral_similitud=args.umbral)
        
        # 3. Crear tabla
        db = Database()
        crear_tabla_proveedores_maestros(db)
        
        # 4. Migrar proveedores
        logger.info("📋 Migrando proveedores a tabla maestra...")
        stats = migrar_proveedores(db, grupos, dry_run=dry_run)
        
        # 5. Actualizar facturas
        if not dry_run:
            actualizar_facturas(db, grupos, dry_run=False)
        
        # 6. Resumen
        logger.info("\n" + "="*80)
        logger.info("📊 RESUMEN DE MIGRACIÓN")
        logger.info("="*80)
        logger.info(f"Total grupos: {stats['total_grupos']}")
        logger.info(f"Proveedores maestros: {stats['total_proveedores_maestros']}")
        logger.info(f"Total facturas: {stats['total_facturas']}")
        logger.info(f"Total importe: {stats['total_importe']:.2f}€")
        if stats['errores']:
            logger.warning(f"Errores: {len(stats['errores'])}")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

