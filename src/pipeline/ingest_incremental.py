"""
Pipeline de ingesta incremental desde Google Drive
Procesa solo archivos nuevos o modificados desde la última sincronización
"""
import os
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.drive.drive_incremental import DriveIncrementalClient
from src.sync.state_store import get_state_store
from src.ocr_extractor import InvoiceExtractor
from src.db.database import Database
from src.db.repositories import FacturaRepository, EventRepository
from src.pipeline.ingest import process_batch
from src.logging_conf import get_logger

logger = get_logger(__name__)


class IncrementalIngestStats:
    """Clase para trackear estadísticas de la ejecución"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.drive_items_listed_total = 0
        self.drive_pages_fetched_total = 0
        self.invoices_processed_ok_total = 0
        self.invoices_duplicate_total = 0
        self.invoices_revision_total = 0
        self.invoices_error_total = 0
        self.invoices_ignored_total = 0
        self.invoices_review_total = 0
        self.last_sync_time_before = None
        self.last_sync_time_after = None
        self.max_modified_time_processed = None
        self.files_downloaded = 0
        self.download_errors = 0
        self.batch_errors = 0
        
    def to_dict(self) -> Dict:
        """Convertir a diccionario"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': round(duration, 2),
            'drive_items_listed_total': self.drive_items_listed_total,
            'drive_pages_fetched_total': self.drive_pages_fetched_total,
            'files_downloaded': self.files_downloaded,
            'download_errors': self.download_errors,
            'batch_errors': self.batch_errors,
            'invoices_processed_ok_total': self.invoices_processed_ok_total,
            'invoices_duplicate_total': self.invoices_duplicate_total,
            'invoices_revision_total': self.invoices_revision_total,
            'invoices_ignored_total': self.invoices_ignored_total,
            'invoices_review_total': self.invoices_review_total,
            'invoices_error_total': self.invoices_error_total,
            'last_sync_time_before': self.last_sync_time_before.isoformat() if self.last_sync_time_before else None,
            'last_sync_time_after': self.last_sync_time_after.isoformat() if self.last_sync_time_after else None,
            'max_modified_time_processed': self.max_modified_time_processed.isoformat() if self.max_modified_time_processed else None
        }
    
    def update_from_batch_stats(self, batch_stats: Dict):
        """Actualizar estadísticas desde resultado de batch"""
        self.invoices_processed_ok_total += batch_stats.get('exitosos', 0)
        self.invoices_duplicate_total += batch_stats.get('duplicados', 0)
        self.invoices_revision_total += batch_stats.get('revisiones', 0)
        self.invoices_ignored_total += batch_stats.get('ignorados', 0)
        self.invoices_review_total += batch_stats.get('revisar', 0)
        self.invoices_error_total += batch_stats.get('fallidos', 0)


class IncrementalIngestPipeline:
    """Pipeline principal de ingesta incremental"""
    
    def __init__(
        self,
        folder_id: str = None,
        batch_size: int = None,
        sleep_between_batch: int = None,
        max_pages_per_run: int = None,
        advance_strategy: str = None
    ):
        """
        Inicializar pipeline
        
        Args:
            folder_id: ID de carpeta Drive objetivo (por defecto desde env)
            batch_size: Archivos por lote (por defecto desde env)
            sleep_between_batch: Segundos entre lotes (por defecto desde env)
            max_pages_per_run: Límite de páginas Drive por run (por defecto desde env)
            advance_strategy: Estrategia para avanzar last_sync_time (por defecto desde env)
        """
        # Configuración
        self.folder_id = folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.batch_size = batch_size or int(os.getenv('BATCH_SIZE', '10'))
        self.sleep_between_batch = sleep_between_batch or int(os.getenv('SLEEP_BETWEEN_BATCH_SEC', '10'))
        self.max_pages_per_run = max_pages_per_run or int(os.getenv('MAX_PAGES_PER_RUN', '10'))
        self.advance_strategy = advance_strategy or os.getenv('ADVANCE_STRATEGY', 'MAX_OK_TIME')
        
        # Validaciones
        if not self.folder_id:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID no configurado")
        
        # Inicializar componentes
        self.drive_client = DriveIncrementalClient()
        self.db = Database()
        self.state_store = get_state_store(self.db)
        self.extractor = InvoiceExtractor()
        
        # Repositorios
        self.factura_repo = FacturaRepository(self.db)
        self.event_repo = EventRepository(self.db)
        
        # Estadísticas
        self.stats = IncrementalIngestStats()
        
        logger.info(
            f"IncrementalIngestPipeline inicializado: "
            f"folder_id={self.folder_id}, batch_size={self.batch_size}, "
            f"max_pages={self.max_pages_per_run}, advance_strategy={self.advance_strategy}"
        )
    
    def run(self) -> Dict:
        """
        Ejecutar pipeline incremental completo
        
        Returns:
            Diccionario con estadísticas de ejecución
        """
        logger.info("="*70)
        logger.info("INICIANDO INGESTA INCREMENTAL")
        logger.info("="*70)
        
        try:
            # Validar acceso a carpeta
            if not self.drive_client.validate_folder_access(self.folder_id):
                raise ValueError(f"No se puede acceder a carpeta Drive: {self.folder_id}")
            
            # Obtener último timestamp de sincronización
            last_sync_time = self.state_store.get_last_sync_time()
            self.stats.last_sync_time_before = last_sync_time
            
            if last_sync_time:
                logger.info(f"Última sincronización: {last_sync_time.isoformat()}")
            else:
                logger.info("Primera ejecución: no hay timestamp previo")
            
            # Crear directorio temporal para descargas
            temp_dir = Path(tempfile.mkdtemp(prefix='invoice_incremental_'))
            logger.info(f"Directorio temporal: {temp_dir}")
            
            try:
                # Procesar archivos incrementales
                self._process_incremental_files(temp_dir, last_sync_time)
                
                # Avanzar timestamp según estrategia
                self._advance_sync_time()
                
            finally:
                # Limpiar directorio temporal
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.info("Directorio temporal limpiado")
            
            # Finalizar estadísticas
            stats_dict = self.stats.to_dict()
            
            logger.info("="*70)
            logger.info("INGESTA INCREMENTAL COMPLETADA")
            logger.info("="*70)
            logger.info(f"Duración: {stats_dict['duration_seconds']}s")
            logger.info(f"Archivos listados: {stats_dict['drive_items_listed_total']}")
            logger.info(f"Archivos procesados OK: {stats_dict['invoices_processed_ok_total']}")
            logger.info(f"Duplicados: {stats_dict['invoices_duplicate_total']}")
            logger.info(f"Revisiones: {stats_dict['invoices_revision_total']}")
            logger.info(f"Errores: {stats_dict['invoices_error_total']}")
            logger.info(f"Timestamp actualizado: {stats_dict['last_sync_time_after']}")
            
            return stats_dict
        
        except Exception as e:
            logger.error(f"Error crítico en pipeline incremental: {e}", exc_info=True)
            
            # Registrar evento de error
            self.event_repo.insert_event(
                drive_file_id='PIPELINE_ERROR',
                etapa='pipeline_run',
                nivel='ERROR',
                detalle=f'Error crítico: {str(e)}'
            )
            
            raise
    
    def _process_incremental_files(self, temp_dir: Path, since_time: Optional[datetime]):
        """
        Procesar archivos incrementales desde Drive
        
        Args:
            temp_dir: Directorio temporal para descargas
            since_time: Timestamp desde el cual buscar cambios
        """
        logger.info("Consultando archivos modificados desde Drive...")
        
        # Iterar páginas de resultados
        for page_files in self.drive_client.list_modified_since(
            self.folder_id,
            since_time,
            max_pages=self.max_pages_per_run
        ):
            self.stats.drive_pages_fetched_total += 1
            self.stats.drive_items_listed_total += len(page_files)
            
            logger.info(
                f"Página {self.stats.drive_pages_fetched_total}: "
                f"{len(page_files)} archivos encontrados"
            )
            
            # Procesar en lotes
            self._process_files_in_batches(page_files, temp_dir)
        
        logger.info(
            f"Búsqueda completada: {self.stats.drive_items_listed_total} archivos, "
            f"{self.stats.drive_pages_fetched_total} páginas"
        )
    
    def _process_files_in_batches(self, files_list: List[Dict], temp_dir: Path):
        """
        Procesar lista de archivos en lotes
        
        Args:
            files_list: Lista de archivos desde Drive API
            temp_dir: Directorio temporal para descargas
        """
        # Dividir en lotes
        for i in range(0, len(files_list), self.batch_size):
            batch = files_list[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            logger.info(
                f"Procesando lote {batch_num}: "
                f"{len(batch)} archivos (desde {i+1} hasta {i+len(batch)})"
            )
            
            try:
                # Descargar archivos del lote
                downloaded_files = self._download_batch(batch, temp_dir)
                
                if not downloaded_files:
                    logger.warning(f"Lote {batch_num}: no se descargó ningún archivo")
                    continue
                
                # Procesar batch usando pipeline existente
                batch_stats = process_batch(downloaded_files, self.extractor, self.db)
                
                # Actualizar estadísticas
                self.stats.update_from_batch_stats(batch_stats)
                
                # Actualizar max_modified_time procesado exitosamente
                self._update_max_modified_time(downloaded_files, batch_stats)
                
                logger.info(
                    f"Lote {batch_num} completado: "
                    f"{batch_stats.get('exitosos', 0)} OK, "
                    f"{batch_stats.get('fallidos', 0)} errores"
                )
            
            except Exception as e:
                logger.error(f"Error procesando lote {batch_num}: {e}", exc_info=True)
                self.stats.batch_errors += 1
                
                # Continuar con siguiente lote (tolerancia a fallos)
                continue
            
            # Pausa entre lotes
            if i + self.batch_size < len(files_list):
                logger.info(f"Pausa de {self.sleep_between_batch}s entre lotes...")
                time.sleep(self.sleep_between_batch)
    
    def _download_batch(self, batch: List[Dict], temp_dir: Path) -> List[Dict]:
        """
        Descargar lote de archivos desde Drive
        
        Args:
            batch: Lista de metadatos de archivos
            temp_dir: Directorio temporal
        
        Returns:
            Lista de archivos descargados con rutas locales
        """
        downloaded = []
        
        for file_info in batch:
            file_id = file_info['id']
            file_name = file_info['name']
            
            try:
                # Sanitizar nombre de archivo
                safe_name = self._sanitize_filename(file_name)
                local_path = temp_dir / f"{file_id}_{safe_name}"
                
                # Descargar
                logger.info(f"Descargando: {file_name} ({file_id})")
                success = self.drive_client.download_file(file_id, str(local_path))
                
                if success and local_path.exists():
                    # Agregar ruta local a metadatos
                    file_info['local_path'] = str(local_path)
                    file_info['folder_name'] = 'incremental'  # Marcar origen
                    
                    downloaded.append(file_info)
                    self.stats.files_downloaded += 1
                    
                    logger.info(f"Descargado OK: {file_name}")
                else:
                    logger.error(f"Descarga falló: {file_name}")
                    self.stats.download_errors += 1
            
            except Exception as e:
                logger.error(f"Error descargando {file_name}: {e}", exc_info=True)
                self.stats.download_errors += 1
                continue
        
        logger.info(
            f"Descarga completada: {len(downloaded)}/{len(batch)} archivos OK, "
            f"{self.stats.download_errors} errores"
        )
        
        return downloaded
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizar nombre de archivo para filesystem
        
        Args:
            filename: Nombre original
        
        Returns:
            Nombre sanitizado
        """
        # Reemplazar caracteres problemáticos
        sanitized = filename.replace('/', '_').replace('\\', '_')
        sanitized = sanitized.replace('..', '_')
        
        # Limitar longitud
        if len(sanitized) > 200:
            name_parts = sanitized.rsplit('.', 1)
            if len(name_parts) == 2:
                name, ext = name_parts
                sanitized = name[:195] + '.' + ext
            else:
                sanitized = sanitized[:200]
        
        return sanitized
    
    def _update_max_modified_time(self, files_list: List[Dict], batch_stats: Dict):
        """
        Actualizar el máximo modifiedTime de archivos procesados exitosamente
        
        Args:
            files_list: Lista de archivos del batch
            batch_stats: Estadísticas del batch procesado
        """
        # Obtener archivos procesados exitosamente
        successful_files = [
            f for f in batch_stats.get('archivos_procesados', [])
            if f.get('status') == 'success'
        ]
        
        if not successful_files:
            logger.debug("No hay archivos exitosos en este batch para actualizar max_modified_time")
            return
        
        # Mapear por file_name para obtener modifiedTime
        for file_info in files_list:
            file_name = file_info['name']
            
            # Verificar si este archivo fue procesado exitosamente
            if any(sf['file_name'] == file_name for sf in successful_files):
                modified_time_str = file_info.get('modifiedTime')
                
                if modified_time_str:
                    try:
                        # Parsear timestamp (formato RFC 3339)
                        modified_time = datetime.fromisoformat(modified_time_str.replace('Z', '+00:00'))
                        
                        # Actualizar máximo
                        if (self.stats.max_modified_time_processed is None or 
                            modified_time > self.stats.max_modified_time_processed):
                            self.stats.max_modified_time_processed = modified_time
                            logger.debug(f"Nuevo max_modified_time: {modified_time.isoformat()}")
                    
                    except ValueError as e:
                        logger.warning(f"Error parseando modifiedTime '{modified_time_str}': {e}")
    
    def _advance_sync_time(self):
        """
        Avanzar last_sync_time según estrategia configurada
        """
        if self.advance_strategy == 'MAX_OK_TIME':
            # Estrategia recomendada: usar máximo modifiedTime de archivos procesados OK
            if self.stats.max_modified_time_processed:
                new_sync_time = self.stats.max_modified_time_processed
                self.state_store.set_last_sync_time(new_sync_time)
                self.stats.last_sync_time_after = new_sync_time
                
                logger.info(
                    f"Timestamp actualizado (MAX_OK_TIME): {new_sync_time.isoformat()}"
                )
            else:
                logger.warning(
                    "No hay archivos procesados exitosamente, "
                    "last_sync_time NO se actualiza"
                )
                self.stats.last_sync_time_after = self.stats.last_sync_time_before
        
        elif self.advance_strategy == 'CURRENT_TIME':
            # Estrategia alternativa: usar tiempo actual (menos segura)
            new_sync_time = datetime.utcnow()
            self.state_store.set_last_sync_time(new_sync_time)
            self.stats.last_sync_time_after = new_sync_time
            
            logger.info(
                f"Timestamp actualizado (CURRENT_TIME): {new_sync_time.isoformat()}"
            )
        
        else:
            raise ValueError(f"ADVANCE_STRATEGY inválida: {self.advance_strategy}")
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas actuales"""
        return self.stats.to_dict()


def run_incremental_ingest(**kwargs) -> Dict:
    """
    Función helper para ejecutar ingesta incremental
    
    Args:
        **kwargs: Parámetros opcionales para IncrementalIngestPipeline
    
    Returns:
        Diccionario con estadísticas de ejecución
    """
    pipeline = IncrementalIngestPipeline(**kwargs)
    return pipeline.run()

