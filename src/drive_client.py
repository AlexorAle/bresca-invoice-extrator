"""
Cliente de Google Drive para listar y descargar archivos PDF
"""
import os
import io
from typing import List, Dict, Optional
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from tenacity import retry, stop_after_attempt, wait_exponential

from src.logging_conf import get_logger

logger = get_logger(__name__)

class DriveClient:
    """Cliente para interactuar con Google Drive API"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, service_account_file: str = None):
        """
        Inicializar cliente de Google Drive
        
        Args:
            service_account_file: Ruta al archivo de service account JSON
        """
        self.service_account_file = service_account_file or os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        
        if not self.service_account_file:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE no configurado")
        
        if not Path(self.service_account_file).exists():
            raise FileNotFoundError(f"Archivo de service account no encontrado: {self.service_account_file}")
        
        # Autenticar
        self.credentials = service_account.Credentials.from_service_account_file(
            self.service_account_file,
            scopes=self.SCOPES
        )
        
        # Construir servicio
        self.service = build('drive', 'v3', credentials=self.credentials)
        
        logger.info("Cliente de Google Drive inicializado correctamente")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_folder_id_by_name(self, folder_name: str, parent_id: str = None) -> Optional[str]:
        """
        Buscar ID de carpeta por nombre
        
        Args:
            folder_name: Nombre de la carpeta a buscar
            parent_id: ID de la carpeta padre (opcional)
        
        Returns:
            ID de la carpeta o None si no se encuentra
        """
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=10
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                logger.info(f"Carpeta '{folder_name}' encontrada: {folder_id}")
                return folder_id
            
            logger.warning(f"Carpeta '{folder_name}' no encontrada")
            return None
        
        except Exception as e:
            logger.error(f"Error buscando carpeta '{folder_name}': {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def list_pdf_files(self, folder_id: str) -> List[dict]:
        """
        Listar archivos PDF en una carpeta
        
        Args:
            folder_id: ID de la carpeta en Google Drive
        
        Returns:
            Lista de diccionarios con información de archivos
        """
        try:
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            
            files = []
            page_token = None
            
            while True:
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, modifiedTime, size, parents)',
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                files.extend(results.get('files', []))
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Encontrados {len(files)} archivos PDF en carpeta {folder_id}")
            
            return files
        
        except Exception as e:
            logger.error(f"Error listando archivos en carpeta {folder_id}: {e}")
            raise
    
    def validate_file_size(self, file_size: int, max_size_mb: int = None) -> tuple:
        """
        Validar tamaño de archivo antes de descargar
        
        Args:
            file_size: Tamaño del archivo en bytes
            max_size_mb: Tamaño máximo permitido en MB (default desde env)
        
        Returns:
            Tuple (is_valid, error_message)
        """
        if max_size_mb is None:
            max_size_mb = int(os.getenv('MAX_PDF_SIZE_MB', '50'))
        
        if file_size is None:
            # Si no hay información de tamaño, permitir (puede ser archivo sin metadata)
            return True, None
        
        try:
            file_size_mb = file_size / (1024 * 1024)  # Convertir bytes a MB
            
            if file_size_mb > max_size_mb:
                error_msg = f"Archivo excede tamaño máximo permitido: {file_size_mb:.2f} MB > {max_size_mb} MB"
                logger.warning(error_msg)
                return False, error_msg
            
            return True, None
        
        except (TypeError, ValueError) as e:
            logger.warning(f"Error validando tamaño de archivo: {e}")
            # Si hay error parseando, permitir (no bloquear por error de validación)
            return True, None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def download_file(self, file_id: str, dest_path: str, file_size: int = None) -> bool:
        """
        Descargar archivo de Google Drive
        
        Args:
            file_id: ID del archivo en Google Drive
            dest_path: Ruta de destino local
            file_size: Tamaño del archivo en bytes (opcional, para validación)
        
        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        # Validar tamaño antes de descargar
        if file_size is not None:
            is_valid, error_msg = self.validate_file_size(file_size)
            if not is_valid:
                logger.error(f"No se descargará archivo {file_id}: {error_msg}")
                return False
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            # Asegurar que el directorio existe
            dest_dir = Path(dest_path).parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Descargar
            fh = io.FileIO(dest_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.debug(f"Descarga {progress}%: {dest_path}")
            
            fh.close()
            
            logger.info(f"Archivo descargado: {dest_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error descargando archivo {file_id}: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_file_by_id(self, file_id: str) -> Optional[dict]:
        """
        Obtener metadata de archivo por ID (para reprocesamiento)
        
        Args:
            file_id: drive_file_id de la factura
        
        Returns:
            Diccionario con metadata del archivo (compatible con process_batch)
            o None si no se encuentra
        """
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, modifiedTime, parents'
            ).execute()
            
            # Obtener nombre de carpeta si es posible
            folder_name = None
            parents = file_metadata.get('parents', [])
            if parents:
                try:
                    parent_metadata = self.service.files().get(
                        fileId=parents[0],
                        fields='name'
                    ).execute()
                    folder_name = parent_metadata.get('name')
                except Exception:
                    pass  # Si no se puede obtener, dejar como None
            
            result = {
                'id': file_metadata.get('id'),
                'name': file_metadata.get('name'),
                'mimeType': file_metadata.get('mimeType'),
                'size': file_metadata.get('size'),
                'modifiedTime': file_metadata.get('modifiedTime'),
                'folder_name': folder_name or 'unknown'
            }
            
            logger.debug(f"Metadata obtenida para archivo {file_id}: {result.get('name')}")
            return result
        
        except Exception as e:
            logger.error(f"Error obteniendo metadata de archivo {file_id}: {e}")
            return None
    
    def get_files_from_months(self, months: List[str], base_folder_id: str = None) -> Dict[str, List[dict]]:
        """
        Obtener archivos PDF de múltiples carpetas de meses
        
        Args:
            months: Lista de nombres de meses (ej: ['agosto', 'septiembre'])
            base_folder_id: ID de la carpeta base (si no se proporciona, busca por nombre)
        
        Returns:
            Diccionario {mes: [archivos]}
        """
        files_by_month = {}
        
        for month in months:
            month_clean = month.strip().lower()
            
            try:
                # Buscar carpeta del mes
                folder_id = self.get_folder_id_by_name(month_clean, parent_id=base_folder_id)
                
                if not folder_id:
                    logger.warning(f"Carpeta de mes '{month_clean}' no encontrada")
                    files_by_month[month_clean] = []
                    continue
                
                # Listar archivos PDF
                files = self.list_pdf_files(folder_id)
                
                # Agregar nombre de carpeta a metadatos
                for file in files:
                    file['folder_name'] = month_clean
                
                files_by_month[month_clean] = files
                
                logger.info(f"Mes '{month_clean}': {len(files)} archivos encontrados")
            
            except Exception as e:
                logger.error(f"Error procesando mes '{month_clean}': {e}")
                files_by_month[month_clean] = []
        
        return files_by_month
    
    def list_all_pdfs_recursive(self, base_folder_id: str, current_path: str = "") -> List[dict]:
        """
        Listar TODOS los archivos PDF dentro de todas las carpetas RECURSIVAMENTE
        (sin depender del nombre de las carpetas)
        
        Este método busca recursivamente todos los PDFs dentro de la carpeta base
        y todas sus subcarpetas anidadas, sin importar la profundidad.
        
        Args:
            base_folder_id: ID de la carpeta base en Google Drive
            current_path: Ruta actual para logging (usado internamente en recursión)
        
        Returns:
            Lista plana de diccionarios con información de todos los PDFs encontrados
        """
        all_pdfs = []
        
        try:
            if not current_path:
                logger.info(f"Iniciando búsqueda recursiva de PDFs en carpeta base: {base_folder_id}")
            else:
                logger.debug(f"Buscando en: {current_path}")
            
            # 1. Buscar PDFs directamente en esta carpeta
            try:
                pdfs_in_folder = self.list_pdf_files(base_folder_id)
                for pdf in pdfs_in_folder:
                    pdf['folder_name'] = current_path if current_path else 'root'
                    pdf['parent_folder_id'] = base_folder_id
                all_pdfs.extend(pdfs_in_folder)
                
                if pdfs_in_folder:
                    path_display = current_path if current_path else 'carpeta base'
                    logger.info(f"{path_display}: {len(pdfs_in_folder)} PDFs encontrados")
            except Exception as e:
                logger.warning(f"Error listando PDFs de carpeta {current_path or 'base'}: {e}")
            
            # 2. Listar todas las subcarpetas dentro de esta carpeta
            folders_query = f"'{base_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            folders = []
            page_token = None
            
            while True:
                results = self.service.files().list(
                    q=folders_query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name)',
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                folders.extend(results.get('files', []))
                page_token = results.get('nextPageToken')
                
                if not page_token:
                    break
            
            if not current_path:
                logger.info(f"Encontradas {len(folders)} carpetas en el primer nivel")
            
            # 3. Para cada subcarpeta, buscar recursivamente
            for folder in folders:
                folder_id = folder['id']
                folder_name = folder['name']
                
                # Construir ruta completa para logging
                new_path = f"{current_path}/{folder_name}" if current_path else folder_name
                
                try:
                    # Llamada recursiva para buscar en esta subcarpeta
                    subfolder_pdfs = self.list_all_pdfs_recursive(folder_id, new_path)
                    
                    # Agregar PDFs encontrados en subcarpetas
                    all_pdfs.extend(subfolder_pdfs)
                    
                except Exception as e:
                    logger.warning(f"Error buscando recursivamente en carpeta '{new_path}' ({folder_id}): {e}")
                    continue
            
            if not current_path:
                logger.info(f"Total de PDFs encontrados (recursivo): {len(all_pdfs)}")
            
            return all_pdfs
        
        except Exception as e:
            logger.error(f"Error en búsqueda recursiva de PDFs en {current_path or 'carpeta base'}: {e}", exc_info=True)
            return []
    
    def get_file_metadata(self, file_id: str) -> Optional[dict]:
        """
        Obtener metadatos de un archivo
        
        Args:
            file_id: ID del archivo en Google Drive
        
        Returns:
            Diccionario con metadatos del archivo
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, modifiedTime, createdTime, parents'
            ).execute()
            
            return file
        
        except Exception as e:
            logger.error(f"Error obteniendo metadatos de archivo {file_id}: {e}")
            return None
