"""
Pipeline de ingestión de facturas
"""
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import time

from src.db.database import Database
from src.db.repositories import FacturaRepository, EventRepository
from src.ocr_extractor import InvoiceExtractor
from src.parser_normalizer import create_factura_dto
from src.pipeline.validate import validate_business_rules, validate_file_integrity
from src.pdf_utils import validate_pdf, cleanup_temp_file
from src.logging_conf import get_logger
from src.pipeline.duplicate_manager import DuplicateManager, DuplicateDecision

logger = get_logger(__name__)

def process_batch(files_list: List[dict], extractor: InvoiceExtractor, db: Database) -> dict:
    """
    Procesar un lote de archivos de facturas con detección de duplicados
    
    Args:
        files_list: Lista de diccionarios con info de archivos (debe incluir 'local_path')
        extractor: Instancia de InvoiceExtractor
        db: Instancia de Database
    
    Returns:
        Diccionario con estadísticas del procesamiento
    """
    stats = {
        'total': len(files_list),
        'exitosos': 0,
        'fallidos': 0,
        'duplicados': 0,
        'ignorados': 0,
        'revisiones': 0,
        'revisar': 0,
        'validacion_fallida': 0,
        'inicio': datetime.utcnow().isoformat(),
        'archivos_procesados': []
    }
    
    factura_repo = FacturaRepository(db)
    event_repo = EventRepository(db)
    duplicate_manager = DuplicateManager()
    
    logger.info(f"Iniciando procesamiento batch de {stats['total']} archivos con detección de duplicados")
    
    for idx, file_info in enumerate(files_list, 1):
        start_time = time.time()
        
        drive_file_id = file_info.get('id')
        file_name = file_info.get('name', 'unknown')
        local_path = file_info.get('local_path')
        
        logger.info(
            f"Procesando {idx}/{stats['total']}: {file_name}",
            extra={'drive_file_id': drive_file_id}
        )
        
        try:
            # Registrar inicio de procesamiento
            event_repo.insert_event(drive_file_id, 'ingest_start', 'INFO', f'Iniciando procesamiento de {file_name}')
            
            # Validar tamaño antes de procesar (si está disponible en metadata)
            file_size = file_info.get('size')
            if file_size is not None:
                try:
                    file_size = int(file_size)
                    max_size_mb = int(os.getenv('MAX_PDF_SIZE_MB', '50'))
                    file_size_mb = file_size / (1024 * 1024)
                    
                    if file_size_mb > max_size_mb:
                        error_msg = f"Archivo excede tamaño máximo permitido: {file_size_mb:.2f} MB > {max_size_mb} MB"
                        logger.warning(f"Rechazado por tamaño: {file_name} - {error_msg}")
                        event_repo.insert_event(
                            drive_file_id,
                            'file_rejected_size',
                            'WARNING',
                            error_msg
                        )
                        stats['fallidos'] += 1
                        stats['archivos_procesados'].append({
                            'file_name': file_name,
                            'status': 'rejected_size',
                            'error': error_msg
                        })
                        continue
                except (ValueError, TypeError):
                    pass  # Si no se puede parsear, continuar (no bloquear)
            
            # Validar archivo
            # Convertir tamaño a int si viene como string desde Drive API
            expected_size = file_info.get('size')
            if expected_size is not None:
                try:
                    expected_size = int(expected_size)
                except (ValueError, TypeError):
                    expected_size = None
            
            if not validate_file_integrity(local_path, expected_size=expected_size):
                raise ValueError(f"Archivo inválido o corrupto: {file_name}")
            
            # Extraer datos con OCR (arquitectura híbrida)
            logger.info(f"Extrayendo datos: {file_name}", extra={'drive_file_id': drive_file_id})
            
            # Espera de 3 segundos entre facturas para evitar rate limiting de OpenAI
            if idx > 1:  # No esperar antes de la primera factura
                time.sleep(3)
            
            raw_data = extractor.extract_invoice_data(local_path)
            
            # Determinar extractor usado (OpenAI GPT-4o-mini como primario)
            extractor_used = raw_data.get('extractor_used', 'hybrid')
            if extractor_used == 'hybrid':
                # Determinar por confianza
                if raw_data.get('confianza') in ['alta', 'media']:
                    extractor_used = 'openai'  # OpenAI GPT-4o-mini
                else:
                    extractor_used = 'tesseract'  # Fallback a Tesseract
            elif raw_data.get('confianza') in ['alta', 'media']:
                extractor_used = 'openai'  # OpenAI GPT-4o-mini
            else:
                extractor_used = 'tesseract'  # Tesseract fallback
            
            # Crear metadatos
            metadata = {
                'drive_file_id': drive_file_id,
                'drive_file_name': file_name,
                'drive_folder_name': file_info.get('folder_name', 'unknown'),
                'drive_modified_time': file_info.get('modifiedTime'),
                'extractor': extractor_used,
                'processed_at': datetime.utcnow().isoformat()
            }
            
            # Crear DTO (incluye cálculo automático de hash_contenido)
            factura_dto = create_factura_dto(raw_data, metadata)
            
            # ====================================================================
            # VALIDACIÓN CRÍTICA: Proveedor/Emisor es OBLIGATORIO
            # ====================================================================
            if not factura_dto.get('proveedor_text') or not factura_dto.get('proveedor_text').strip():
                error_msg = "Nombre del proveedor/emisor no encontrado en la factura"
                logger.error(f"Factura sin proveedor: {file_name} - {error_msg}", extra={'drive_file_id': drive_file_id})
                
                # Marcar como error y mover a cuarentena
                factura_dto['estado'] = 'error'
                factura_dto['error_msg'] = error_msg
                
                # Mover a cuarentena (usar REVIEW como decisión para archivos problemáticos)
                duplicate_manager.move_to_quarantine(file_info, DuplicateDecision.REVIEW, factura_dto, error_msg)
                
                # Registrar evento
                event_repo.insert_event(
                    drive_file_id,
                    'ingest_error',
                    'ERROR',
                    error_msg
                )
                
                stats['fallidos'] += 1
                stats['archivos_procesados'].append({
                    'file_name': file_name,
                    'status': 'failed',
                    'reason': error_msg,
                    'elapsed_ms': int((time.time() - start_time) * 1000)
                })
                
                # Continuar con siguiente archivo
                continue
            
            # ====================================================================
            # VALIDACIÓN CRÍTICA: Importe Total debe existir (puede ser negativo)
            # ====================================================================
            importe_total = factura_dto.get('importe_total')
            if importe_total is None:
                error_msg = f"importe_total es NULL (debe tener un valor, puede ser positivo o negativo)"
                logger.error(f"Factura con importe_total NULL: {file_name} - {error_msg}", extra={'drive_file_id': drive_file_id})
                
                # Marcar como error y mover a cuarentena
                factura_dto['estado'] = 'error'
                factura_dto['error_msg'] = error_msg
                
                # Mover a cuarentena
                duplicate_manager.move_to_quarantine(file_info, DuplicateDecision.REVIEW, factura_dto, error_msg)
                
                # Registrar evento
                event_repo.insert_event(
                    drive_file_id,
                    'ingest_error',
                    'ERROR',
                    error_msg
                )
                
                stats['fallidos'] += 1
                stats['archivos_procesados'].append({
                    'file_name': file_name,
                    'status': 'failed',
                    'reason': error_msg,
                    'elapsed_ms': int((time.time() - start_time) * 1000)
                })
                
                # Continuar con siguiente archivo
                continue
            
            # ====================================================================
            # DETECCIÓN DE DUPLICADOS
            # ====================================================================
            hash_contenido = factura_dto.get('hash_contenido')
            
            # Buscar facturas existentes
            existing_by_file_id = factura_repo.find_by_file_id(drive_file_id)
            existing_by_hash = factura_repo.find_by_hash(hash_contenido) if hash_contenido else None
            existing_by_number = factura_repo.find_by_invoice_number(
                factura_dto.get('proveedor_text'),
                factura_dto.get('numero_factura')
            )
            
            # Decidir acción basándose en duplicados
            decision, reason = duplicate_manager.decide_action(
                factura_dto,
                existing_by_file_id,
                existing_by_hash,
                existing_by_number
            )
            
            logger.info(
                f"Decisión de duplicado: {decision.value} - {reason}",
                extra={
                    'drive_file_id': drive_file_id,
                    'decision': decision.value,
                    'hash': hash_contenido[:16] if hash_contenido else None
                }
            )
            
            # Registrar evento de decisión
            event_repo.insert_event(
                drive_file_id,
                'duplicate_check',
                'INFO' if decision == DuplicateDecision.INSERT else 'WARNING',
                reason,
                hash_contenido=hash_contenido,
                decision=decision.value
            )
            
            # Aplicar decisión
            if decision == DuplicateDecision.IGNORE:
                # Archivo ya procesado sin cambios, ignorar
                stats['ignorados'] += 1
                stats['archivos_procesados'].append({
                    'file_name': file_name,
                    'status': 'ignored',
                    'reason': reason,
                    'elapsed_ms': int((time.time() - start_time) * 1000)
                })
                continue
            
            elif decision == DuplicateDecision.DUPLICATE:
                # Duplicado detectado, marcar y mover a cuarentena
                stats['duplicados'] += 1
                factura_dto['estado'] = 'duplicado'
                factura_dto['error_msg'] = reason
                
                # Mover a cuarentena
                duplicate_manager.move_to_quarantine(file_info, decision, factura_dto, reason)
                
                # No insertar en BD (ya existe)
                stats['archivos_procesados'].append({
                    'file_name': file_name,
                    'status': 'duplicate',
                    'reason': reason,
                    'elapsed_ms': int((time.time() - start_time) * 1000)
                })
                continue
            
            elif decision == DuplicateDecision.REVIEW:
                # Posible conflicto, marcar para revisión
                stats['revisar'] += 1
                factura_dto['estado'] = 'revisar'
                factura_dto['error_msg'] = reason
                
                # Mover a cuarentena de revisión
                duplicate_manager.move_to_quarantine(file_info, decision, factura_dto, reason)
                
                # Guardar en pending
                save_to_pending_queue(factura_dto)
            
            elif decision == DuplicateDecision.UPDATE_REVISION:
                # Archivo modificado, incrementar revisión
                stats['revisiones'] += 1
                factura_dto['estado'] = 'procesado'
                
                event_repo.insert_event(
                    drive_file_id,
                    'revision_created',
                    'INFO',
                    f'Nueva revisión detectada: {reason}',
                    hash_contenido=hash_contenido
                )
            
            # Validar reglas de negocio (solo para INSERT y UPDATE_REVISION)
            if decision in [DuplicateDecision.INSERT, DuplicateDecision.UPDATE_REVISION]:
                if not validate_business_rules(factura_dto):
                    stats['validacion_fallida'] += 1
                    factura_dto['estado'] = 'revisar'
                    factura_dto['error_msg'] = factura_dto.get('error_msg', '') + ' | Validación de negocio falló'
                    
                    event_repo.insert_event(
                        drive_file_id,
                        'validation',
                        'WARNING',
                        'Validación de negocio falló, marcado para revisión'
                    )
                    
                    # Guardar en pending para revisión manual
                    save_to_pending_queue(factura_dto)
            
            # Insertar/actualizar en BD
            increment_revision = (decision == DuplicateDecision.UPDATE_REVISION)
            factura_id = factura_repo.upsert_factura(factura_dto, increment_revision=increment_revision)
            
            # Calcular tiempo de procesamiento
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            # Registrar éxito
            event_repo.insert_event(
                drive_file_id,
                'ingest_complete',
                'INFO',
                f'Procesamiento exitoso en {elapsed_ms}ms, ID: {factura_id}'
            )
            
            stats['exitosos'] += 1
            stats['archivos_procesados'].append({
                'file_name': file_name,
                'status': 'success',
                'elapsed_ms': elapsed_ms,
                'factura_id': factura_id
            })
            
            logger.info(
                f"Factura procesada exitosamente: {file_name}",
                extra={'drive_file_id': drive_file_id, 'elapsed_ms': elapsed_ms}
            )
        
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            logger.error(
                f"Error procesando {file_name}: {e}",
                extra={'drive_file_id': drive_file_id},
                exc_info=True
            )
            
            # Registrar error
            event_repo.insert_event(
                drive_file_id,
                'ingest_error',
                'ERROR',
                f'Error: {str(e)}'
            )
            
            # Manejar fallo
            handle_failure(file_info, e)
            
            stats['fallidos'] += 1
            stats['archivos_procesados'].append({
                'file_name': file_name,
                'status': 'failed',
                'error': str(e),
                'elapsed_ms': elapsed_ms
            })
        
        finally:
            # Limpiar archivo temporal
            if local_path and os.path.exists(local_path):
                cleanup_temp_file(local_path)
    
    # Finalizar stats
    stats['fin'] = datetime.utcnow().isoformat()
    stats['duracion_total_s'] = (
        datetime.fromisoformat(stats['fin']) - 
        datetime.fromisoformat(stats['inicio'])
    ).total_seconds()
    
    logger.info(
        f"Batch completado: {stats['exitosos']} exitosos, "
        f"{stats['fallidos']} fallidos, {stats['validacion_fallida']} con validación fallida"
    )
    
    return stats

def handle_failure(file_info: dict, error: Exception):
    """
    Manejar fallo de procesamiento (mover a cuarentena)
    
    Args:
        file_info: Información del archivo
        error: Excepción capturada
    """
    try:
        local_path = file_info.get('local_path')
        file_name = file_info.get('name', 'unknown')
        
        if not local_path or not os.path.exists(local_path):
            logger.warning(f"No se puede mover a cuarentena, archivo no existe: {local_path}")
            return
        
        # Ruta de cuarentena
        quarantine_path = Path(os.getenv('QUARANTINE_PATH', 'data/quarantine'))
        quarantine_path.mkdir(parents=True, exist_ok=True)
        
        # Nombre con timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        quarantine_file = quarantine_path / f"{timestamp}_{file_name}"
        
        # Mover archivo
        shutil.move(local_path, quarantine_file)
        
        # Crear archivo de metadatos con el error
        meta_file = quarantine_file.with_suffix('.meta.json')
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump({
                'file_info': file_info,
                'error': str(error),
                'timestamp': timestamp,
                'quarantined_at': datetime.utcnow().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        logger.warning(f"Archivo movido a cuarentena: {quarantine_file}")
    
    except Exception as e:
        logger.error(f"Error moviendo archivo a cuarentena: {e}")

def save_to_pending_queue(factura_dto: dict):
    """
    Guardar factura en cola de pendientes (para revisión manual)
    
    Args:
        factura_dto: DTO de la factura
    """
    try:
        pending_path = Path(os.getenv('PENDING_PATH', 'data/pending'))
        pending_path.mkdir(parents=True, exist_ok=True)
        
        # Nombre de archivo
        drive_file_id = factura_dto.get('drive_file_id', 'unknown')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        pending_file = pending_path / f"{timestamp}_{drive_file_id}.json"
        
        # Guardar JSON
        with open(pending_file, 'w', encoding='utf-8') as f:
            json.dump(factura_dto, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Factura guardada en pending: {pending_file}")
    
    except Exception as e:
        logger.error(f"Error guardando en pending queue: {e}")

def cleanup_old_pending(days: int = 30):
    """
    Limpiar archivos antiguos de la cola de pendientes
    
    Args:
        days: Días de antigüedad para limpiar
    """
    try:
        pending_path = Path(os.getenv('PENDING_PATH', 'data/pending'))
        
        if not pending_path.exists():
            return
        
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        removed_count = 0
        
        for file_path in pending_path.glob('*.json'):
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if file_mtime < cutoff_date:
                file_path.unlink()
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Limpiados {removed_count} archivos pendientes antiguos")
    
    except Exception as e:
        logger.error(f"Error limpiando pending queue: {e}")
