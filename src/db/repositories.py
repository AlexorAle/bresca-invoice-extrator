"""
Repositorios para operaciones de base de datos
"""
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from calendar import monthrange
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, extract

from .models import Factura, Proveedor, IngestEvent, SyncState
from .database import Database
from src.logging_conf import get_logger

logger = get_logger(__name__)

class FacturaRepository:
    """Repositorio para operaciones con facturas"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def file_exists(self, drive_file_id: str) -> bool:
        """
        Verificar si un archivo ya fue procesado
        
        Args:
            drive_file_id: ID del archivo en Google Drive
        
        Returns:
            True si el archivo existe, False en caso contrario
        """
        with self.db.get_session() as session:
            count = session.query(Factura).filter(
                Factura.drive_file_id == drive_file_id
            ).count()
            return count > 0
    
    def find_by_file_id(self, drive_file_id: str) -> Optional[dict]:
        """
        Buscar factura por drive_file_id
        
        Args:
            drive_file_id: ID del archivo en Google Drive
        
        Returns:
            Diccionario con datos de la factura, o None si no existe
        """
        with self.db.get_session() as session:
            factura = session.query(Factura).filter(
                Factura.drive_file_id == drive_file_id
            ).first()
            
            if not factura:
                return None
            
            return {
                'id': factura.id,
                'drive_file_id': factura.drive_file_id,
                'drive_file_name': factura.drive_file_name,
                'hash_contenido': factura.hash_contenido,
                'proveedor_text': factura.proveedor_text,
                'numero_factura': factura.numero_factura,
                'importe_total': float(factura.importe_total) if factura.importe_total else None,
                'revision': factura.revision,
                'estado': factura.estado
            }
    
    def find_by_hash(self, hash_contenido: str) -> Optional[dict]:
        """
        Buscar factura por hash_contenido
        
        Args:
            hash_contenido: Hash SHA256 de contenido
        
        Returns:
            Diccionario con datos de la factura, o None si no existe
        """
        if not hash_contenido:
            return None
        
        with self.db.get_session() as session:
            factura = session.query(Factura).filter(
                Factura.hash_contenido == hash_contenido
            ).first()
            
            if not factura:
                return None
            
            return {
                'id': factura.id,
                'drive_file_id': factura.drive_file_id,
                'drive_file_name': factura.drive_file_name,
                'hash_contenido': factura.hash_contenido,
                'proveedor_text': factura.proveedor_text,
                'numero_factura': factura.numero_factura,
                'importe_total': float(factura.importe_total) if factura.importe_total else None,
                'fecha_emision': factura.fecha_emision.isoformat() if factura.fecha_emision else None,
                'revision': factura.revision,
                'estado': factura.estado
            }
    
    def find_by_invoice_number(self, proveedor_text: str, numero_factura: str) -> Optional[dict]:
        """
        Buscar factura por proveedor + número de factura
        
        Args:
            proveedor_text: Nombre del proveedor
            numero_factura: Número de factura
        
        Returns:
            Diccionario con datos de la factura, o None si no existe
        """
        if not proveedor_text or not numero_factura:
            return None
        
        with self.db.get_session() as session:
            # OPTIMIZACIÓN: Buscar primero por proveedor_id si existe
            # Si no, buscar por proveedor_text (compatibilidad)
            proveedor = session.query(Proveedor).filter(
                Proveedor.nombre == proveedor_text
            ).first()
            
            if proveedor:
                # Buscar por proveedor_id (más eficiente)
                factura = session.query(Factura).filter(
                    Factura.proveedor_id == proveedor.id,
                    Factura.numero_factura == numero_factura
                ).first()
            else:
                # Fallback: buscar por proveedor_text (compatibilidad)
                factura = session.query(Factura).filter(
                    Factura.proveedor_text == proveedor_text,
                    Factura.numero_factura == numero_factura
                ).first()
            
            if not factura:
                return None
            
            return {
                'id': factura.id,
                'drive_file_id': factura.drive_file_id,
                'drive_file_name': factura.drive_file_name,
                'hash_contenido': factura.hash_contenido,
                'proveedor_text': factura.proveedor_text,
                'proveedor_id': factura.proveedor_id,  # Agregado para normalización
                'numero_factura': factura.numero_factura,
                'importe_total': float(factura.importe_total) if factura.importe_total else None,
                'fecha_emision': factura.fecha_emision.isoformat() if factura.fecha_emision else None,
                'revision': factura.revision,
                'estado': factura.estado
            }
    
    def upsert_factura(self, factura_data: dict, increment_revision: bool = False) -> int:
        """
        Insertar o actualizar factura (UPSERT pattern)
        
        Args:
            factura_data: Diccionario con datos de la factura
            increment_revision: Si True, incrementa el contador de revision
        
        Returns:
            ID de la factura insertada/actualizada
        """
        with self.db.get_session() as session:
            # NUEVO SISTEMA: Usar proveedores_maestros
            proveedor_text = factura_data.get('proveedor_text')
            proveedor_nif = factura_data.get('proveedor_nif')
            
            if proveedor_text and not factura_data.get('proveedor_maestro_id'):
                try:
                    from src.utils.proveedor_finder import normalizar_y_buscar_proveedor
                    from src.db.models import ProveedorMaestro
                    
                    # Buscar o crear proveedor maestro
                    resultado = normalizar_y_buscar_proveedor(
                        nombre_raw=proveedor_text,
                        nif=proveedor_nif,
                        session=session
                    )
                    
                    # Establecer proveedor_maestro_id
                    factura_data['proveedor_maestro_id'] = resultado['proveedor_maestro_id']
                    factura_data['proveedor_text'] = resultado['nombre_canonico']
                    
                    # También mantener proveedor_id para compatibilidad (buscar en tabla legacy)
                    from src.db.models import Proveedor
                    proveedor_legacy = session.query(Proveedor).filter(
                        Proveedor.nombre == resultado['nombre_canonico']
                    ).first()
                    
                    if proveedor_legacy:
                        factura_data['proveedor_id'] = proveedor_legacy.id
                    else:
                        # Crear en tabla legacy también para compatibilidad
                        proveedor_legacy = Proveedor(
                            nombre=resultado['nombre_canonico'],
                            nif_cif=proveedor_nif.strip().upper() if proveedor_nif and proveedor_nif.strip() else None
                        )
                        session.add(proveedor_legacy)
                        session.flush()
                        factura_data['proveedor_id'] = proveedor_legacy.id
                    
                    logger.debug(
                        f"Proveedor maestro encontrado/creado: {resultado['nombre_canonico']} "
                        f"(método: {resultado['metodo']}, confianza: {resultado['confianza']:.1f}%)"
                    )
                    
                except ImportError:
                    # Fallback al sistema antiguo si no está disponible el nuevo
                    logger.warning("Sistema de proveedores_maestros no disponible, usando sistema legacy")
                    from src.utils.proveedor_normalizer import normalize_proveedor_name
                    from src.db.models import Proveedor
                    
                    nombre_normalizado = normalize_proveedor_name(proveedor_text)
                    proveedor = session.query(Proveedor).filter(
                        Proveedor.nombre == proveedor_text
                    ).first()
                    
                    if not proveedor:
                        proveedor = Proveedor(
                            nombre=proveedor_text,
                            nif_cif=proveedor_nif.strip().upper() if proveedor_nif and proveedor_nif.strip() else None
                        )
                        session.add(proveedor)
                        session.flush()
                    
                    factura_data['proveedor_id'] = proveedor.id
                    if 'proveedor_text' not in factura_data:
                        factura_data['proveedor_text'] = proveedor_text
            
            # Preparar datos para insert
            stmt = insert(Factura).values(**factura_data)
            
            # On conflict, actualizar todos los campos excepto el ID
            update_dict = {k: v for k, v in factura_data.items() if k != 'id'}
            update_dict['actualizado_en'] = datetime.utcnow()
            
            # Si hay que incrementar revisión, usar función SQL
            if increment_revision:
                from sqlalchemy import func
                update_dict['revision'] = func.coalesce(Factura.revision, 0) + 1
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['drive_file_id'],
                set_=update_dict
            ).returning(Factura.id)
            
            result = session.execute(stmt)
            factura_id = result.scalar()
            
            logger.info(
                f"Factura upsert exitoso: {factura_data.get('drive_file_name')}",
                extra={
                    'drive_file_id': factura_data.get('drive_file_id'),
                    'increment_revision': increment_revision,
                    'proveedor_id': factura_data.get('proveedor_id')
                }
            )
            
            return factura_id
    
    def get_facturas_by_month(self, month: str) -> List[dict]:
        """
        Obtener facturas de un mes específico
        
        Args:
            month: Nombre del mes (ej: 'agosto')
        
        Returns:
            Lista de diccionarios con datos de facturas
        """
        with self.db.get_session() as session:
            facturas = session.query(Factura).filter(
                Factura.drive_folder_name.ilike(f"%{month}%")
            ).all()
            
            return [
                {
                    'id': f.id,
                    'drive_file_name': f.drive_file_name,
                    'proveedor_text': f.proveedor_text,
                    'numero_factura': f.numero_factura,
                    'fecha_emision': f.fecha_emision.isoformat() if f.fecha_emision else None,
                    'importe_total': float(f.importe_total) if f.importe_total else 0,
                    'confianza': f.confianza,
                    'estado': f.estado
                }
                for f in facturas
            ]
    
    def get_statistics(self) -> dict:
        """
        Obtener estadísticas generales
        
        Returns:
            Diccionario con estadísticas
        """
        with self.db.get_session() as session:
            total_facturas = session.query(func.count(Factura.id)).scalar()
            total_importe = session.query(func.sum(Factura.importe_total)).scalar() or 0
            promedio_importe = session.query(func.avg(Factura.importe_total)).scalar() or 0
            
            # Contar por estado
            estados = session.query(
                Factura.estado,
                func.count(Factura.id)
            ).group_by(Factura.estado).all()
            
            # Contar por confianza
            confianzas = session.query(
                Factura.confianza,
                func.count(Factura.id)
            ).group_by(Factura.confianza).all()
            
            return {
                'total_facturas': total_facturas,
                'total_importe': float(total_importe),
                'promedio_importe': float(promedio_importe),
                'por_estado': {estado: count for estado, count in estados},
                'por_confianza': {conf: count for conf, count in confianzas}
            }
    
    def get_pending_files(self) -> List[str]:
        """
        Obtener lista de drive_file_ids ya procesados
        
        Returns:
            Lista de IDs de archivos procesados
        """
        with self.db.get_session() as session:
            file_ids = session.query(Factura.drive_file_id).all()
            return [fid[0] for fid in file_ids]
    
    def get_all_facturas(self, limit: int = 100) -> List[dict]:
        """
        Obtener todas las facturas (con límite)
        
        Args:
            limit: Número máximo de facturas a retornar
        
        Returns:
            Lista de diccionarios con datos de facturas
        """
        with self.db.get_session() as session:
            facturas = session.query(Factura).order_by(
                Factura.fecha_emision.desc()
            ).limit(limit).all()
            
            return [
                {
                    'id': f.id,
                    'drive_file_name': f.drive_file_name,
                    'drive_folder_name': f.drive_folder_name,
                    'proveedor_text': f.proveedor_text,
                    'numero_factura': f.numero_factura,
                    'fecha_emision': f.fecha_emision.isoformat() if f.fecha_emision else None,
                    'importe_total': float(f.importe_total) if f.importe_total else 0,
                    'base_imponible': float(f.base_imponible) if f.base_imponible else 0,
                    'impuestos_total': float(f.impuestos_total) if f.impuestos_total else 0,
                    'confianza': f.confianza,
                    'estado': f.estado,
                    'extractor': f.extractor
                }
                for f in facturas
            ]
    
    def get_last_modified_time(self) -> Optional[datetime]:
        """
        Obtener la última fecha de modificación procesada
        
        Returns:
            Timestamp de última modificación, o None si no hay facturas
        """
        with self.db.get_session() as session:
            result = session.query(func.max(Factura.drive_modified_time)).scalar()
            return result
    
    def get_summary_by_month(self, month: int, year: int) -> dict:
        """
        Obtener resumen de facturas de un mes específico
        
        Args:
            month: Mes (1-12)
            year: Año
        
        Returns:
            Diccionario con estadísticas del mes
        """
        with self.db.get_session() as session:
            # Filtrar facturas del mes
            # Usar fecha_emision si existe, sino usar fecha_recepcion como fallback
            start_date = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = date(year, month, last_day)
            
            # Usar func.coalesce para usar fecha_emision o fecha_recepcion como fallback
            fecha_filtro = func.coalesce(Factura.fecha_emision, Factura.fecha_recepcion)
            
            facturas_query = session.query(Factura).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date
            )
            
            total_facturas = facturas_query.count()
            # Contar exitosas: facturas con importe_total > 0 y estado != 'error'
            facturas_exitosas = facturas_query.filter(
                Factura.importe_total.isnot(None),
                Factura.importe_total > 0,
                Factura.estado != 'error'
            ).count()
            # Contar fallidas: facturas con estado == 'error' o sin importe_total
            facturas_fallidas = facturas_query.filter(
                (Factura.estado == 'error') | (Factura.importe_total.is_(None))
            ).count()
            
            importe_total = session.query(func.sum(Factura.importe_total)).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date,
                Factura.importe_total.isnot(None)
            ).scalar() or 0.0
            
            promedio_factura = session.query(func.avg(Factura.importe_total)).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date,
                Factura.importe_total.isnot(None)
            ).scalar() or 0.0
            
            proveedores_activos = session.query(
                func.count(func.distinct(Factura.proveedor_text))
            ).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date,
                Factura.proveedor_text.isnot(None)
            ).scalar() or 0
            
            # Calcular confianza promedio (alta=100%, media=50%, baja=25%)
            confianza_values = session.query(Factura.confianza).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date,
                Factura.confianza.isnot(None)
            ).all()
            
            if confianza_values:
                confianza_map = {'alta': 100.0, 'media': 50.0, 'baja': 25.0}
                confianza_promedio = sum(
                    confianza_map.get(c[0], 0) for c in confianza_values
                ) / len(confianza_values)
            else:
                confianza_promedio = 0.0
            
            return {
                'total_facturas': total_facturas,
                'facturas_exitosas': facturas_exitosas,
                'facturas_fallidas': facturas_fallidas,
                'importe_total': float(importe_total),
                'promedio_factura': float(promedio_factura),
                'proveedores_activos': proveedores_activos,
                'confianza_extraccion': confianza_promedio
            }
    
    def get_facturas_by_day(self, month: int, year: int) -> List[dict]:
        """
        Obtener facturas agrupadas por día del mes
        
        Args:
            month: Mes (1-12)
            year: Año
        
        Returns:
            Lista de diccionarios con datos por día
        """
        with self.db.get_session() as session:
            start_date = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = date(year, month, last_day)
            
            # Usar fecha_emision si existe, sino usar fecha_recepcion
            fecha_filtro = func.coalesce(Factura.fecha_emision, Factura.fecha_recepcion)
            
            # Agrupar por día usando extract para PostgreSQL
            results = session.query(
                extract('day', fecha_filtro).label('dia'),
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.importe_total).label('importe_total'),
                func.sum(Factura.impuestos_total).label('importe_iva')
            ).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date,
                (Factura.fecha_emision.isnot(None) | Factura.fecha_recepcion.isnot(None))
            ).group_by(
                extract('day', fecha_filtro)
            ).order_by('dia').all()
            
            # Crear diccionario con todos los días del mes
            days_dict = {i: {'dia': i, 'cantidad': 0, 'importe_total': 0.0, 'importe_iva': 0.0} 
                        for i in range(1, last_day + 1)}
            
            # Llenar con datos reales
            for r in results:
                dia = int(r.dia)
                days_dict[dia] = {
                    'dia': dia,
                    'cantidad': int(r.cantidad),
                    'importe_total': float(r.importe_total or 0.0),
                    'importe_iva': float(r.importe_iva or 0.0)
                }
            
            return list(days_dict.values())
    
    def get_all_facturas_by_month(self, month: int, year: int) -> List[dict]:
        """
        Obtener todas las facturas del mes
        
        Args:
            month: Mes (1-12)
            year: Año
        
        Returns:
            Lista de diccionarios con todas las facturas del mes
        """
        with self.db.get_session() as session:
            start_date = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = date(year, month, last_day)
            
            # Usar fecha_emision si existe, sino usar fecha_recepcion
            fecha_filtro = func.coalesce(Factura.fecha_emision, Factura.fecha_recepcion)
            
            facturas = session.query(Factura).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date
            ).order_by(
                fecha_filtro.desc(),
                Factura.creado_en.desc()
            ).all()
            
            return [
                {
                    'id': f.id,
                    'proveedor_nombre': f.proveedor_text,
                    'categoria': f.drive_folder_name,  # Nombre de la carpeta = categoría
                    'fecha_emision': f.fecha_emision.isoformat() if f.fecha_emision else None,
                    'impuestos_total': float(f.impuestos_total) if f.impuestos_total else 0.0,
                    'importe_total': float(f.importe_total) if f.importe_total else 0.0
                }
                for f in facturas
            ]
    
    def get_facturas_pendientes_by_month(self, month: int, year: int) -> List[dict]:
        """
        Obtener solo las facturas pendientes del mes (estado 'error' o sin importe_total)
        
        Args:
            month: Mes (1-12)
            year: Año
        
        Returns:
            Lista de diccionarios con las facturas pendientes del mes
        """
        with self.db.get_session() as session:
            start_date = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = date(year, month, last_day)
            
            # Usar fecha_emision si existe, sino usar fecha_recepcion
            fecha_filtro = func.coalesce(Factura.fecha_emision, Factura.fecha_recepcion)
            
            # Filtrar solo facturas pendientes: estado == 'error' o importe_total is None
            facturas = session.query(Factura).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date,
                (Factura.estado == 'error') | (Factura.importe_total.is_(None))
            ).order_by(
                fecha_filtro.desc(),
                Factura.creado_en.desc()
            ).all()
            
            return [
                {
                    'id': f.id,
                    'proveedor_nombre': f.proveedor_text,
                    'categoria': f.drive_folder_name,  # Nombre de la carpeta = categoría
                    'fecha_emision': f.fecha_emision.isoformat() if f.fecha_emision else None,
                    'estado': f.estado,
                    'motivo_error': f.motivo_rechazo if hasattr(f, 'motivo_rechazo') else None,
                    'impuestos_total': float(f.impuestos_total) if f.impuestos_total else 0.0,
                    'importe_total': float(f.importe_total) if f.importe_total else 0.0
                }
                for f in facturas
            ]
    
    def get_recent_facturas(self, month: int, year: int, limit: int = 5) -> List[dict]:
        """
        Obtener facturas recientes del mes
        
        Args:
            month: Mes (1-12)
            year: Año
            limit: Límite de facturas a retornar
        
        Returns:
            Lista de diccionarios con facturas recientes
        """
        with self.db.get_session() as session:
            start_date = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = date(year, month, last_day)
            
            # Usar fecha_emision si existe, sino usar fecha_recepcion
            fecha_filtro = func.coalesce(Factura.fecha_emision, Factura.fecha_recepcion)
            
            facturas = session.query(Factura).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date
            ).order_by(
                fecha_filtro.desc(),
                Factura.creado_en.desc()
            ).limit(limit).all()
            
            return [
                {
                    'id': f.id,
                    'numero_factura': f.numero_factura,
                    'proveedor_nombre': f.proveedor_text,
                    'fecha_emision': f.fecha_emision,
                    'importe_base': float(f.base_imponible) if f.base_imponible else None,
                    'importe_iva': float(f.impuestos_total) if f.impuestos_total else None,
                    'importe_total': float(f.importe_total) if f.importe_total else None
                }
                for f in facturas
            ]
    
    def get_categories_breakdown(self, month: int, year: int) -> List[dict]:
        """
        Obtener desglose por categorías (proveedores)
        
        Args:
            month: Mes (1-12)
            year: Año
        
        Returns:
            Lista de diccionarios con datos por categoría
        """
        with self.db.get_session() as session:
            start_date = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = date(year, month, last_day)
            
            # Usar fecha_emision si existe, sino usar fecha_recepcion
            fecha_filtro = func.coalesce(Factura.fecha_emision, Factura.fecha_recepcion)
            
            # OPTIMIZACIÓN: Usar proveedor_id con JOIN para mejor rendimiento
            # Fallback a proveedor_text si proveedor_id es NULL (compatibilidad)
            results = session.query(
                func.coalesce(Proveedor.nombre, Factura.proveedor_text, 'Sin proveedor').label('categoria'),
                func.count(Factura.id).label('cantidad'),
                func.sum(Factura.importe_total).label('importe_total')
            ).outerjoin(
                Proveedor, Factura.proveedor_id == Proveedor.id
            ).filter(
                fecha_filtro >= start_date,
                fecha_filtro <= end_date,
                (Factura.proveedor_id.isnot(None) | Factura.proveedor_text.isnot(None))
            ).group_by(
                Proveedor.nombre, Factura.proveedor_text
            ).order_by(
                func.sum(Factura.importe_total).desc()
            ).all()
            
            return [
                {
                    'categoria': r.categoria or 'Sin proveedor',
                    'cantidad': int(r.cantidad),
                    'importe_total': float(r.importe_total or 0.0)
                }
                for r in results
            ]
    
    def get_facturas_para_reprocesar(
        self,
        estado: str = 'revisar',
        max_dias: int = 30,
        limite: int = 50,
        max_attempts: int = 3
    ) -> List[dict]:
        """
        Obtener facturas que requieren reprocesamiento
        
        Args:
            estado: Estado de facturas a buscar (default: 'revisar')
            max_dias: Solo facturas de últimos N días
            limite: Máximo de facturas a retornar
            max_attempts: Máximo de intentos permitidos
        
        Returns:
            Lista de facturas con drive_file_id y metadata necesaria
        """
        with self.db.get_session() as session:
            # Calcular fecha límite
            fecha_limite = datetime.utcnow() - timedelta(days=max_dias)
            
            # Patrones de error de alta prioridad (bugs conocidos)
            high_priority_patterns = [
                'tipo inválido',
                'formato inválido',
                'parsing failed',
                'Validación de negocio falló'
            ]
            
            # Query base: facturas en estado, últimos N días, intentos < máximo
            base_query = session.query(Factura).filter(
                Factura.estado == estado,
                Factura.actualizado_en >= fecha_limite,
                Factura.reprocess_attempts < max_attempts
            )
            
            # Obtener todas las facturas que cumplen criterios
            facturas = base_query.order_by(
                Factura.actualizado_en.desc()
            ).limit(limite * 2).all()  # Obtener más para priorizar
            
            # Priorizar por error_msg
            def get_priority(factura):
                error_msg = (factura.error_msg or '').lower()
                for pattern in high_priority_patterns:
                    if pattern.lower() in error_msg:
                        return 0  # Alta prioridad
                return 1  # Baja prioridad
            
            # Ordenar por prioridad y luego por fecha
            facturas_priorizadas = sorted(facturas, key=lambda f: (get_priority(f), f.actualizado_en), reverse=True)
            
            # Limitar resultado
            facturas_priorizadas = facturas_priorizadas[:limite]
            
            return [
                {
                    'id': f.id,
                    'drive_file_id': f.drive_file_id,
                    'drive_file_name': f.drive_file_name,
                    'drive_folder_name': f.drive_folder_name,
                    'estado': f.estado,
                    'error_msg': f.error_msg,
                    'reprocess_attempts': f.reprocess_attempts or 0,
                    'actualizado_en': f.actualizado_en
                }
                for f in facturas_priorizadas
            ]
    
    def increment_reprocess_attempts(
        self,
        factura_id: int,
        reason: str,
        max_attempts: int = 3
    ) -> bool:
        """
        Incrementar contador de intentos de reprocesamiento
        
        Args:
            factura_id: ID de la factura
            reason: Razón del reprocesamiento
            max_attempts: Máximo de intentos permitidos
        
        Returns:
            True si se alcanzó el máximo (cambió a error_permanente), False en caso contrario
        """
        with self.db.get_session() as session:
            factura = session.query(Factura).filter(
                Factura.id == factura_id
            ).first()
            
            if not factura:
                logger.warning(f"Factura {factura_id} no encontrada para incrementar intentos")
                return False
            
            # Incrementar contador
            factura.reprocess_attempts = (factura.reprocess_attempts or 0) + 1
            factura.reprocessed_at = datetime.utcnow()
            factura.reprocess_reason = reason
            
            # Si alcanza máximo, cambiar a error_permanente
            if factura.reprocess_attempts >= max_attempts:
                factura.estado = 'error_permanente'
                factura.error_msg = (factura.error_msg or '') + f' | Máximo de intentos de reprocesamiento alcanzado ({max_attempts})'
                logger.warning(
                    f"Factura {factura_id} alcanzó máximo de intentos, marcada como error_permanente",
                    extra={'drive_file_id': factura.drive_file_id}
                )
                return True
            
            return False
    
    def cleanup_stuck_pending_invoices(self, hours: int = 24) -> int:
        """
        Cambiar facturas en estado 'pendiente' > X horas a 'error'
        
        Args:
            hours: Horas antes de marcar como error (default: 24)
        
        Returns:
            Número de facturas actualizadas
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self.db.get_session() as session:
            facturas = session.query(Factura).filter(
                Factura.estado == 'pendiente',
                Factura.actualizado_en < cutoff_time
            ).all()
            
            count = len(facturas)
            
            for factura in facturas:
                factura.estado = 'error'
                factura.error_msg = f'Factura en pendiente > {hours}h, marcada como error'
                factura.actualizado_en = datetime.utcnow()
            
            if count > 0:
                session.commit()
                logger.info(f"Limpieza de facturas pendientes: {count} facturas marcadas como error")
            
            return count
    
    def get_facturas_en_cuarentena_para_reprocesar(
        self,
        max_dias: int = 30,
        limite: int = 50
    ) -> List[dict]:
        """
        Obtener facturas en cuarentena (estado 'error' o 'revisar') que fueron modificadas en Drive
        
        Args:
            max_dias: Solo facturas de últimos N días
            limite: Máximo de facturas a retornar
        
        Returns:
            Lista de facturas con drive_file_id y metadata necesaria
        """
        with self.db.get_session() as session:
            # Calcular fecha límite
            fecha_limite = datetime.utcnow() - timedelta(days=max_dias)
            
            # Query: facturas en estado problemático, últimos N días
            facturas = session.query(Factura).filter(
                Factura.estado.in_(['error', 'revisar']),
                Factura.actualizado_en >= fecha_limite,
                Factura.deleted_from_drive == False
            ).order_by(
                Factura.actualizado_en.desc()
            ).limit(limite).all()
            
            return [
                {
                    'id': f.id,
                    'drive_file_id': f.drive_file_id,
                    'drive_file_name': f.drive_file_name,
                    'drive_folder_name': f.drive_folder_name,
                    'estado': f.estado,
                    'error_msg': f.error_msg,
                    'reprocess_attempts': f.reprocess_attempts or 0,
                    'actualizado_en': f.actualizado_en,
                    'drive_modified_time': f.drive_modified_time
                }
                for f in facturas
            ]

class EventRepository:
    """Repositorio para eventos de auditoría"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def insert_event(
        self,
        drive_file_id: str,
        etapa: str,
        nivel: str,
        detalle: str = None,
        hash_contenido: str = None,
        decision: str = None
    ):
        """
        Insertar evento de auditoría
        
        Args:
            drive_file_id: ID del archivo en Google Drive
            etapa: Etapa del proceso (download, extract, validate, etc.)
            nivel: Nivel del evento (INFO, WARNING, ERROR)
            detalle: Detalles adicionales del evento
            hash_contenido: Hash de contenido de la factura (para detección de duplicados)
            decision: Decisión tomada (insert, duplicate, review, etc.)
        """
        with self.db.get_session() as session:
            event = IngestEvent(
                drive_file_id=drive_file_id,
                etapa=etapa,
                nivel=nivel,
                detalle=detalle,
                hash_contenido=hash_contenido,
                decision=decision,
                ts=datetime.utcnow()
            )
            session.add(event)
            
            logger.debug(
                f"Evento registrado: {etapa} - {nivel}",
                extra={
                    'drive_file_id': drive_file_id,
                    'etapa': etapa,
                    'decision': decision
                }
            )
    
    def get_events_by_file(self, drive_file_id: str) -> List[dict]:
        """
        Obtener eventos de un archivo específico
        
        Args:
            drive_file_id: ID del archivo en Google Drive
        
        Returns:
            Lista de eventos
        """
        with self.db.get_session() as session:
            events = session.query(IngestEvent).filter(
                IngestEvent.drive_file_id == drive_file_id
            ).order_by(IngestEvent.ts.desc()).all()
            
            return [
                {
                    'id': e.id,
                    'etapa': e.etapa,
                    'nivel': e.nivel,
                    'detalle': e.detalle,
                    'ts': e.ts.isoformat()
                }
                for e in events
            ]

class ProveedorRepository:
    """Repositorio para proveedores"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def find_or_create(self, nombre: str) -> int:
        """
        Buscar proveedor por nombre o crearlo si no existe
        
        Args:
            nombre: Nombre del proveedor
        
        Returns:
            ID del proveedor
        """
        with self.db.get_session() as session:
            proveedor = session.query(Proveedor).filter(
                Proveedor.nombre == nombre
            ).first()
            
            if proveedor:
                return proveedor.id
            
            # Crear nuevo proveedor
            nuevo_proveedor = Proveedor(nombre=nombre)
            session.add(nuevo_proveedor)
            session.flush()
            
            logger.info(f"Nuevo proveedor creado: {nombre}")
            
            return nuevo_proveedor.id

class SyncStateRepository:
    """Repositorio para el estado de sincronización incremental"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_value(self, key: str) -> Optional[str]:
        """
        Obtener valor de estado por clave
        
        Args:
            key: Clave del estado
        
        Returns:
            Valor del estado, o None si no existe
        """
        with self.db.get_session() as session:
            state = session.query(SyncState).filter(
                SyncState.key == key
            ).first()
            
            if state:
                return state.value
            return None
    
    def set_value(self, key: str, value: str):
        """
        Establecer valor de estado (upsert)
        
        Args:
            key: Clave del estado
            value: Valor a guardar
        """
        with self.db.get_session() as session:
            state = session.query(SyncState).filter(
                SyncState.key == key
            ).first()
            
            if state:
                state.value = value
                state.updated_at = datetime.utcnow()
            else:
                state = SyncState(key=key, value=value)
                session.add(state)
            
            logger.debug(f"Estado actualizado: {key} = {value}")
    
    def delete_value(self, key: str):
        """
        Eliminar valor de estado
        
        Args:
            key: Clave del estado a eliminar
        """
        with self.db.get_session() as session:
            session.query(SyncState).filter(
                SyncState.key == key
            ).delete()
            
            logger.debug(f"Estado eliminado: {key}")
