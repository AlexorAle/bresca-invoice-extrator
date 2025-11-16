"""
Búsqueda incremental de archivos modificados en Google Drive
"""
import os
import time
from typing import List, Dict, Optional, Iterator
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from googleapiclient.errors import HttpError

from src.drive_client import DriveClient
from src.logging_conf import get_logger

logger = get_logger(__name__, component="backend")


class DriveIncrementalClient(DriveClient):
    """Cliente extendido para búsquedas incrementales en Google Drive"""
    
    def __init__(self, service_account_file: str = None):
        """
        Inicializar cliente incremental
        
        Args:
            service_account_file: Ruta al archivo de service account JSON
        """
        super().__init__(service_account_file)
        
        # Configuración desde env
        self.page_size = int(os.getenv('DRIVE_PAGE_SIZE', '100'))
        self.retry_max = int(os.getenv('DRIVE_RETRY_MAX', '5'))
        self.retry_base_ms = int(os.getenv('DRIVE_RETRY_BASE_MS', '500'))
        self.sync_window_minutes = int(os.getenv('SYNC_WINDOW_MINUTES', '1440'))  # 24h por defecto
        self.process_all_files = os.getenv('PROCESS_ALL_FILES', 'false').lower() == 'true'
        
        logger.info(
            f"DriveIncrementalClient inicializado: "
            f"page_size={self.page_size}, retry_max={self.retry_max}, "
            f"sync_window={self.sync_window_minutes}min, "
            f"process_all_files={self.process_all_files}"
        )
    
    def _build_incremental_query(
        self,
        folder_id: str,
        since_time: datetime,
        mime_type: str = 'application/pdf'
    ) -> str:
        """
        Construir query para archivos modificados desde un timestamp
        
        Args:
            folder_id: ID de la carpeta objetivo
            since_time: Timestamp desde el cual buscar cambios
            mime_type: Tipo MIME de archivos a buscar
        
        Returns:
            Query string para Drive API
        """
        # TEMPORAL: Si PROCESS_ALL_FILES está activo, no filtrar por fecha
        if self.process_all_files:
            query = (
                f"'{folder_id}' in parents and "
                f"mimeType = '{mime_type}' and "
                f"trashed = false"
            )
            logger.info("MODO TEMPORAL: Procesando TODOS los archivos sin restricciones de fecha")
        else:
            # Lógica original activa cuando PROCESS_ALL_FILES=false
            # Formatear timestamp en RFC 3339
            since_time_str = since_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            query = (
                f"'{folder_id}' in parents and "
                f"mimeType = '{mime_type}' and "
                f"modifiedTime > '{since_time_str}' and "
                f"trashed = false"
            )
        
        logger.debug(f"Query incremental: {query}")
        
        return query
    
    def _calculate_adjusted_since_time(self, since_time: Optional[datetime]) -> datetime:
        """
        Calcular timestamp ajustado con ventana de seguridad
        
        Args:
            since_time: Timestamp original, o None para primera ejecución
        
        Returns:
            Timestamp ajustado con buffer de seguridad
        """
        if since_time is None:
            # Primera ejecución: usar ventana completa hacia atrás
            adjusted = datetime.utcnow() - timedelta(minutes=self.sync_window_minutes)
            logger.info(
                f"Primera sincronización: buscando desde {adjusted.isoformat()} "
                f"({self.sync_window_minutes} minutos atrás)"
            )
            return adjusted
        
        # Restar ventana de seguridad para no perder cambios por desfase de relojes
        adjusted = since_time - timedelta(minutes=self.sync_window_minutes)
        
        logger.info(
            f"Sincronización incremental: desde {since_time.isoformat()} "
            f"ajustado a {adjusted.isoformat()} (buffer de {self.sync_window_minutes}min)"
        )
        
        return adjusted
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((HttpError, ConnectionError)),
        reraise=True
    )
    def _execute_list_request(
        self,
        query: str,
        page_token: Optional[str] = None,
        order_by: str = 'modifiedTime asc, name asc'
    ) -> Dict:
        """
        Ejecutar request de listado con reintentos
        
        Args:
            query: Query string
            page_token: Token de paginación (opcional)
            order_by: Orden de resultados
        
        Returns:
            Respuesta de Drive API
        """
        try:
            request_params = {
                'q': query,
                'spaces': 'drive',
                'fields': 'nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)',
                'pageSize': self.page_size,
                'orderBy': order_by
            }
            
            if page_token:
                request_params['pageToken'] = page_token
            
            logger.debug(f"Ejecutando request Drive API: pageToken={page_token}")
            
            result = self.service.files().list(**request_params).execute()
            
            return result
        
        except HttpError as e:
            # 429 = Rate limit exceeded
            if e.resp.status == 429:
                logger.warning(f"Rate limit excedido (429), reintentando...")
                raise
            
            # 5xx = Server error
            if 500 <= e.resp.status < 600:
                logger.warning(f"Error de servidor Drive ({e.resp.status}), reintentando...")
                raise
            
            # Otros errores, no reintentar
            logger.error(f"Error HTTP no recuperable: {e.resp.status} - {e}")
            raise
        
        except Exception as e:
            logger.error(f"Error ejecutando request Drive: {e}")
            raise
    
    def _get_all_subfolders(self, parent_folder_id: str) -> List[str]:
        """
        Obtener todas las subcarpetas recursivamente desde una carpeta padre
        
        Args:
            parent_folder_id: ID de la carpeta padre
        
        Returns:
            Lista de IDs de subcarpetas (incluyendo la carpeta padre)
        """
        folder_ids = [parent_folder_id]  # Incluir la carpeta raíz
        
        try:
            # Obtener subcarpetas directas
            query = (
                f"'{parent_folder_id}' in parents and "
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"trashed = false"
            )
            
            page_token = None
            while True:
                result = self.service.files().list(
                    q=query,
                    fields='nextPageToken, files(id, name)',
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                subfolders = result.get('files', [])
                for subfolder in subfolders:
                    folder_ids.append(subfolder['id'])
                    logger.debug(f"Subcarpeta encontrada: {subfolder['name']} ({subfolder['id']})")
                
                page_token = result.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Total de carpetas a buscar: {len(folder_ids)} (1 raíz + {len(folder_ids)-1} subcarpetas)")
            return folder_ids
        
        except Exception as e:
            logger.warning(f"Error obteniendo subcarpetas, usando solo carpeta raíz: {e}")
            return [parent_folder_id]
    
    def list_modified_since(
        self,
        folder_id: str,
        since_time: Optional[datetime] = None,
        max_pages: Optional[int] = None
    ) -> Iterator[List[Dict]]:
        """
        Listar archivos modificados desde un timestamp (con paginación)
        Busca recursivamente en la carpeta raíz y todas sus subcarpetas
        
        Args:
            folder_id: ID de la carpeta objetivo
            since_time: Timestamp desde el cual buscar (None = primera ejecución)
            max_pages: Máximo de páginas a procesar (None = sin límite)
        
        Yields:
            Listas de archivos (una página a la vez)
        """
        # Calcular tiempo ajustado
        adjusted_since = self._calculate_adjusted_since_time(since_time)
        
        # Obtener todas las subcarpetas (incluyendo la raíz)
        all_folder_ids = self._get_all_subfolders(folder_id)
        
        # TEMPORAL: Si PROCESS_ALL_FILES está activo, no filtrar por fecha
        if self.process_all_files:
            # Construir query sin restricción de fecha
            if len(all_folder_ids) == 1:
                query = (
                    f"'{folder_id}' in parents and "
                    f"mimeType = 'application/pdf' and "
                    f"trashed = false"
                )
            else:
                folder_conditions = " or ".join([f"'{fid}' in parents" for fid in all_folder_ids])
                query = (
                    f"({folder_conditions}) and "
                    f"mimeType = 'application/pdf' and "
                    f"trashed = false"
                )
            logger.info("MODO TEMPORAL: Procesando TODOS los archivos sin restricciones de fecha")
        else:
            # Lógica original activa cuando PROCESS_ALL_FILES=false
            # Construir query que busque en todas las carpetas
            # Usar operador OR para buscar en múltiples carpetas
            since_time_str = adjusted_since.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            # Si hay muchas subcarpetas, usar una query más eficiente
            if len(all_folder_ids) == 1:
                # Solo carpeta raíz, usar query simple
                query = self._build_incremental_query(folder_id, adjusted_since)
            else:
                # Múltiples carpetas: construir query con OR
                folder_conditions = " or ".join([f"'{fid}' in parents" for fid in all_folder_ids])
                query = (
                    f"({folder_conditions}) and "
                    f"mimeType = 'application/pdf' and "
                    f"modifiedTime > '{since_time_str}' and "
                    f"trashed = false"
                )
        
        logger.info(
            f"Iniciando búsqueda incremental en {len(all_folder_ids)} carpetas "
            f"desde {adjusted_since.isoformat()}"
        )
        
        # Iterar páginas
        page_token = None
        page_count = 0
        total_files = 0
        
        while True:
            try:
                # Ejecutar request con reintentos
                result = self._execute_list_request(query, page_token)
                
                files = result.get('files', [])
                page_count += 1
                total_files += len(files)
                
                logger.info(
                    f"Página {page_count}: {len(files)} archivos encontrados "
                    f"(total acumulado: {total_files})"
                )
                
                # Yield página
                if files:
                    yield files
                
                # Verificar si hay más páginas
                page_token = result.get('nextPageToken')
                
                if not page_token:
                    logger.info(f"Búsqueda completada: {total_files} archivos en {page_count} páginas")
                    break
                
                # Verificar límite de páginas
                if max_pages and page_count >= max_pages:
                    logger.warning(
                        f"Límite de páginas alcanzado ({max_pages}), "
                        f"puede haber más archivos sin procesar"
                    )
                    break
                
                # Pequeña pausa entre páginas para no saturar API
                time.sleep(0.1)
            
            except Exception as e:
                logger.error(
                    f"Error en página {page_count + 1} de búsqueda incremental: {e}",
                    exc_info=True
                )
                raise
    
    def get_file_count_since(
        self,
        folder_id: str,
        since_time: Optional[datetime] = None
    ) -> int:
        """
        Contar archivos modificados desde un timestamp (sin descargarlos)
        Busca recursivamente en la carpeta raíz y todas sus subcarpetas
        
        Args:
            folder_id: ID de la carpeta objetivo
            since_time: Timestamp desde el cual contar
        
        Returns:
            Número total de archivos modificados
        """
        adjusted_since = self._calculate_adjusted_since_time(since_time)
        
        # Obtener todas las subcarpetas (incluyendo la raíz)
        all_folder_ids = self._get_all_subfolders(folder_id)
        
        # Construir query que busque en todas las carpetas
        since_time_str = adjusted_since.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        if len(all_folder_ids) == 1:
            query = self._build_incremental_query(folder_id, adjusted_since)
        else:
            folder_conditions = " or ".join([f"'{fid}' in parents" for fid in all_folder_ids])
            query = (
                f"({folder_conditions}) and "
                f"mimeType = 'application/pdf' and "
                f"modifiedTime > '{since_time_str}' and "
                f"trashed = false"
            )
        
        page_token = None
        total_count = 0
        
        logger.info(f"Contando archivos modificados desde {adjusted_since.isoformat()} en {len(all_folder_ids)} carpetas")
        
        while True:
            result = self._execute_list_request(query, page_token)
            
            files = result.get('files', [])
            total_count += len(files)
            
            page_token = result.get('nextPageToken')
            if not page_token:
                break
            
            time.sleep(0.1)
        
        logger.info(f"Total de archivos modificados: {total_count}")
        
        return total_count
    
    def validate_folder_access(self, folder_id: str) -> bool:
        """
        Validar que se tiene acceso a la carpeta
        
        Args:
            folder_id: ID de la carpeta a validar
        
        Returns:
            True si se tiene acceso, False en caso contrario
        """
        try:
            metadata = self.get_file_metadata(folder_id)
            
            if not metadata:
                logger.error(f"No se pudo obtener metadata de carpeta {folder_id}")
                return False
            
            mime_type = metadata.get('mimeType')
            if mime_type != 'application/vnd.google-apps.folder':
                logger.error(f"El ID {folder_id} no corresponde a una carpeta (tipo: {mime_type})")
                return False
            
            logger.info(f"Acceso validado a carpeta: {metadata.get('name')} ({folder_id})")
            return True
        
        except Exception as e:
            logger.error(f"Error validando acceso a carpeta {folder_id}: {e}")
            return False

