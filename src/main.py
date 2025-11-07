"""
Script principal de extracción de facturas
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import json

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent))

from security.secrets import load_env, validate_secrets
from logging_conf import get_logger
from db.database import get_database
from db.repositories import FacturaRepository, EventRepository
from drive_client import DriveClient
from ocr_extractor import InvoiceExtractor
from pipeline.ingest import process_batch
from pipeline.validate import sanitize_filename

# Cargar variables de entorno
load_env()
validate_secrets()

logger = get_logger(__name__)

class InvoiceProcessor:
    """Procesador principal de facturas"""
    
    def __init__(self, args):
        """
        Inicializar procesador
        
        Args:
            args: Argumentos de línea de comandos
        """
        self.args = args
        self.temp_path = Path(os.getenv('TEMP_PATH', 'temp'))
        self.backup_path = Path(os.getenv('BACKUP_PATH', 'data/backups'))
        self.months = self._get_months()
        
        # Crear directorios necesarios
        self.temp_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar componentes
        logger.info("Inicializando componentes...")
        
        try:
            self.db = get_database()
            self.db.init_db()
            
            self.drive_client = DriveClient()
            self.openai_api_key = os.getenv('OPENAI_API_KEY')
            self.extractor = InvoiceExtractor(self.openai_api_key)
            
            logger.info("Componentes inicializados correctamente")
        
        except Exception as e:
            logger.error(f"Error inicializando componentes: {e}", exc_info=True)
            raise
    
    def _get_months(self):
        """Obtener lista de meses a procesar"""
        if self.args.months:
            return [m.strip() for m in self.args.months.split(',')]
        
        months_env = os.getenv('MONTHS_TO_SCAN', 'agosto,septiembre,octubre')
        return [m.strip() for m in months_env.split(',')]
    
    def run(self) -> int:
        """
        Ejecutar proceso completo
        
        Returns:
            Exit code (0=éxito, 1=error parcial, 2=error crítico)
        """
        try:
            logger.info("="*60)
            logger.info("Iniciando proceso de extracción de facturas")
            logger.info(f"Meses a procesar: {', '.join(self.months)}")
            logger.info(f"Modo dry-run: {self.args.dry_run}")
            logger.info(f"Modo force: {self.args.force}")
            logger.info("="*60)
            
            # Obtener archivos de Drive (sin depender de nombres de carpetas)
            logger.info("Conectando a Google Drive...")
            base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
            
            if not base_folder_id:
                logger.error("GOOGLE_DRIVE_FOLDER_ID no configurado")
                return 2
            
            # Listar TODOS los PDFs recursivamente (sin depender de nombres de carpetas)
            logger.info("Buscando todos los PDFs en todas las carpetas...")
            all_files = self.drive_client.list_all_pdfs_recursive(base_folder_id)
            
            logger.info(f"Total de archivos encontrados: {len(all_files)}")
            
            if len(all_files) == 0:
                logger.warning("No se encontraron archivos para procesar")
                return 0
            
            if self.args.dry_run:
                logger.info(f"[DRY-RUN] Se procesarían {len(all_files)} archivos")
                logger.info("\nArchivos encontrados:")
                for i, file_info in enumerate(all_files[:20], 1):  # Mostrar primeros 20
                    logger.info(f"  {i}. {file_info.get('name', 'Unknown')} (carpeta: {file_info.get('folder_name', 'unknown')})")
                if len(all_files) > 20:
                    logger.info(f"  ... y {len(all_files) - 20} más")
                return 0
            
            # Descargar todos los archivos
            logger.info(f"\n{'='*60}")
            logger.info(f"Procesando {len(all_files)} archivos encontrados")
            logger.info(f"{'='*60}\n")
            
            downloaded_files = self._download_files(all_files)
            
            if len(downloaded_files) == 0:
                logger.error("No se pudieron descargar archivos")
                return 2
            
            # Procesar batch (el sistema de duplicados se encargará de filtrar los ya procesados)
            logger.info(f"Procesando {len(downloaded_files)} archivos descargados...")
            stats = process_batch(downloaded_files, self.extractor, self.db)
            
            all_stats = [stats]
            
            logger.info(f"Procesamiento completado: {stats['exitosos']} exitosos, {stats['fallidos']} fallidos")
            
            # Resumen final
            self._print_summary(all_stats)
            
            # Backup si hubo procesamiento exitoso
            total_exitosos = sum(s['exitosos'] for s in all_stats)
            if total_exitosos > 0 and not self.args.dry_run:
                self._create_backup()
            
            # Limpiar temporales
            self._cleanup_temp()
            
            # Determinar exit code
            total_fallidos = sum(s['fallidos'] for s in all_stats)
            
            if total_fallidos > 0 and total_exitosos == 0:
                logger.error("Proceso completado con errores críticos")
                return 2
            elif total_fallidos > 0:
                logger.warning("Proceso completado con errores parciales")
                return 1
            else:
                logger.info("Proceso completado exitosamente")
                return 0
        
        except KeyboardInterrupt:
            logger.warning("Proceso interrumpido por usuario")
            self._cleanup_temp()
            return 130
        
        except Exception as e:
            logger.error(f"Error crítico en proceso principal: {e}", exc_info=True)
            self._cleanup_temp()
            return 2
    
    def _filter_processed_files(self, files_by_month):
        """Filtrar archivos ya procesados"""
        repo = FacturaRepository(self.db)
        processed_ids = set(repo.get_pending_files())
        
        filtered = {}
        
        for month, files in files_by_month.items():
            new_files = [f for f in files if f['id'] not in processed_ids]
            filtered[month] = new_files
            
            skipped = len(files) - len(new_files)
            if skipped > 0:
                logger.info(f"Mes '{month}': {skipped} archivos ya procesados (saltados)")
        
        return filtered
    
    def _download_files(self, files):
        """Descargar archivos de Google Drive"""
        downloaded = []
        
        for idx, file_info in enumerate(files, 1):
            file_id = file_info['id']
            file_name = file_info['name']
            
            # Sanitizar nombre
            safe_name = sanitize_filename(file_name)
            local_path = self.temp_path / safe_name
            
            logger.info(f"Descargando {idx}/{len(files)}: {file_name}")
            
            try:
                success = self.drive_client.download_file(file_id, str(local_path))
                
                if success:
                    file_info['local_path'] = str(local_path)
                    downloaded.append(file_info)
                else:
                    logger.warning(f"No se pudo descargar: {file_name}")
            
            except Exception as e:
                logger.error(f"Error descargando {file_name}: {e}")
        
        logger.info(f"Descargados {len(downloaded)}/{len(files)} archivos")
        
        return downloaded
    
    def _print_summary(self, all_stats):
        """Imprimir resumen de procesamiento"""
        if not all_stats:
            return
        
        total_procesados = sum(s['total'] for s in all_stats)
        total_exitosos = sum(s['exitosos'] for s in all_stats)
        total_fallidos = sum(s['fallidos'] for s in all_stats)
        total_validacion_fallida = sum(s['validacion_fallida'] for s in all_stats)
        
        logger.info("\n" + "="*60)
        logger.info("RESUMEN FINAL")
        logger.info("="*60)
        logger.info(f"Total procesados:        {total_procesados}")
        logger.info(f"Exitosos:                {total_exitosos}")
        logger.info(f"Fallidos:                {total_fallidos}")
        logger.info(f"Validación fallida:      {total_validacion_fallida}")
        logger.info("="*60 + "\n")
        
        # Guardar stats en archivo
        stats_file = Path(os.getenv('LOG_PATH', 'logs')).parent / 'last_run_stats.json'
        stats_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'summary': {
                    'total_procesados': total_procesados,
                    'exitosos': total_exitosos,
                    'fallidos': total_fallidos,
                    'validacion_fallida': total_validacion_fallida
                },
                'details': all_stats
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Estadísticas guardadas en: {stats_file}")
    
    def _create_backup(self):
        """Crear backup de la base de datos"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_path / f"facturas_backup_{timestamp}.sql"
            
            # Obtener URL de la BD
            db_url = os.getenv('DATABASE_URL')
            
            # Parsear URL para obtener componentes
            # postgresql://user:pass@host/dbname
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^/]+)/(.+)', db_url)
            
            if match:
                user, password, host, dbname = match.groups()
                
                # Ejecutar pg_dump
                import subprocess
                env = os.environ.copy()
                env['PGPASSWORD'] = password
                
                cmd = [
                    'pg_dump',
                    '-U', user,
                    '-h', host.split(':')[0],  # Remover puerto si existe
                    '-d', dbname,
                    '-f', str(backup_file),
                    '--no-owner',
                    '--no-acl'
                ]
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Backup creado exitosamente: {backup_file}")
                else:
                    logger.warning(f"No se pudo crear backup: {result.stderr}")
            else:
                logger.warning("No se pudo parsear DATABASE_URL para backup")
        
        except Exception as e:
            logger.warning(f"Error creando backup (no crítico): {e}")
    
    def _cleanup_temp(self):
        """Limpiar archivos temporales"""
        try:
            import shutil
            
            if self.temp_path.exists():
                for item in self.temp_path.glob('*'):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                
                logger.info("Archivos temporales limpiados")
        
        except Exception as e:
            logger.warning(f"Error limpiando temporales: {e}")
    
    def show_stats(self):
        """Mostrar estadísticas de la base de datos"""
        repo = FacturaRepository(self.db)
        stats = repo.get_statistics()
        
        print("\n" + "="*60)
        print("ESTADÍSTICAS DE BASE DE DATOS")
        print("="*60)
        print(f"Total facturas:     {stats['total_facturas']}")
        print(f"Importe total:      €{stats['total_importe']:,.2f}")
        print(f"Importe promedio:   €{stats['promedio_importe']:,.2f}")
        print("\nPor estado:")
        for estado, count in stats['por_estado'].items():
            print(f"  {estado:15} {count}")
        print("\nPor confianza:")
        for conf, count in stats['por_confianza'].items():
            print(f"  {conf:15} {count}")
        print("="*60 + "\n")
    
    def close(self):
        """Cerrar conexiones"""
        if hasattr(self, 'db'):
            self.db.close()
        logger.info("Conexiones cerradas")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Extractor automático de facturas desde Google Drive'
    )
    
    parser.add_argument(
        '--months',
        type=str,
        help='Meses a procesar separados por comas (ej: agosto,septiembre)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo simulación (no procesa archivos)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Forzar procesamiento de archivos ya procesados'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Mostrar estadísticas de la base de datos y salir'
    )
    
    args = parser.parse_args()
    
    try:
        processor = InvoiceProcessor(args)
        
        # Si solo se piden stats
        if args.stats:
            processor.show_stats()
            processor.close()
            return 0
        
        # Ejecutar proceso principal
        exit_code = processor.run()
        
        # Mostrar stats al final
        if exit_code == 0:
            processor.show_stats()
        
        processor.close()
        
        return exit_code
    
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        return 2

if __name__ == "__main__":
    sys.exit(main())
