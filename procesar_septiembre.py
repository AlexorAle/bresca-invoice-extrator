#!/usr/bin/env python3
"""
Script para procesar todas las facturas de la carpeta "Septiembre" en Google Drive
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env, validate_secrets
from src.drive_client import DriveClient
from src.ocr_extractor import InvoiceExtractor
from src.db.database import get_database
from src.pipeline.ingest import process_batch
from src.logging_conf import get_logger

load_env()
validate_secrets()

logger = get_logger(__name__)

def main():
    """Procesar todas las facturas de la carpeta Septiembre"""
    
    print("="*80)
    print("🚀 PROCESAMIENTO DE FACTURAS DE SEPTIEMBRE")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configuración
    base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    month_folder_name = 'Septiembre'  # Nombre exacto de la carpeta en Drive
    
    if not base_folder_id:
        print("❌ ERROR: GOOGLE_DRIVE_FOLDER_ID no configurado en .env")
        return 1
    
    try:
        # Inicializar clientes
        print("📡 Conectando a Google Drive...")
        drive_client = DriveClient()
        
        print("🔧 Inicializando extractor OCR...")
        extractor = InvoiceExtractor()
        
        print("💾 Conectando a base de datos...")
        db = get_database()
        db.init_db()
        
        # Buscar carpeta del mes
        print(f"\n🔍 Buscando carpeta '{month_folder_name}'...")
        month_folder_id = drive_client.get_folder_id_by_name(month_folder_name, parent_id=base_folder_id)
        
        if not month_folder_id:
            print(f"❌ Carpeta '{month_folder_name}' no encontrada")
            print(f"   Intentando búsqueda alternativa...")
            # Intentar con minúsculas
            month_folder_id = drive_client.get_folder_id_by_name(month_folder_name.lower(), parent_id=base_folder_id)
            if not month_folder_id:
                print(f"❌ Carpeta '{month_folder_name}' no encontrada (ni en mayúsculas ni minúsculas)")
                return 1
        
        print(f"✅ Carpeta encontrada: {month_folder_id}\n")
        
        # Listar archivos PDF
        print("📋 Listando archivos PDF en la carpeta...")
        pdf_files = drive_client.list_pdf_files(month_folder_id)
        
        if not pdf_files:
            print("⚠️  No se encontraron archivos PDF en la carpeta")
            return 0
        
        print(f"✅ Encontrados {len(pdf_files)} archivos PDF\n")
        
        # Crear directorio temporal
        temp_dir = Path(tempfile.mkdtemp(prefix='invoice_septiembre_'))
        print(f"📁 Directorio temporal: {temp_dir}\n")
        
        try:
            # Preparar lista de archivos para procesar
            files_to_process = []
            
            print("📥 Descargando archivos desde Google Drive...")
            for idx, file_info in enumerate(pdf_files, 1):
                file_id = file_info['id']
                file_name = file_info['name']
                
                # Descargar archivo
                temp_file_path = temp_dir / file_name
                
                print(f"  [{idx}/{len(pdf_files)}] Descargando: {file_name}...", end=' ', flush=True)
                
                success = drive_client.download_file(file_id, str(temp_file_path))
                
                if success:
                    print("✅")
                    # Agregar información adicional para el procesamiento
                    file_info['local_path'] = str(temp_file_path)
                    file_info['folder_name'] = month_folder_name
                    files_to_process.append(file_info)
                else:
                    print("❌ Error descargando")
            
            print(f"\n✅ {len(files_to_process)} archivos descargados correctamente\n")
            
            if not files_to_process:
                print("⚠️  No hay archivos para procesar")
                return 0
            
            # Procesar batch completo
            print("="*80)
            print("🔄 PROCESANDO FACTURAS...")
            print("="*80)
            print()
            
            stats = process_batch(files_to_process, extractor, db)
            
            # Mostrar estadísticas
            print("\n" + "="*80)
            print("📊 ESTADÍSTICAS DE PROCESAMIENTO")
            print("="*80)
            print(f"✅ Exitosos:      {stats.get('exitosos', 0)}")
            print(f"⚠️  Revisar:       {stats.get('revisar', 0)}")
            print(f"🔄 Revisiones:    {stats.get('revisiones', 0)}")
            print(f"📋 Duplicados:    {stats.get('duplicados', 0)}")
            print(f"🚫 Ignorados:     {stats.get('ignorados', 0)}")
            print(f"❌ Errores:       {stats.get('errores', 0)}")
            print(f"⏱️  Tiempo total:  {stats.get('tiempo_total_ms', 0) / 1000:.2f}s")
            print()
            
            # Resumen final
            total_procesadas = stats.get('exitosos', 0) + stats.get('revisar', 0)
            print("="*80)
            if total_procesadas > 0:
                print(f"✅ PROCESAMIENTO COMPLETADO: {total_procesadas} facturas procesadas")
            else:
                print("⚠️  No se procesaron facturas nuevas (posiblemente todas eran duplicados)")
            print("="*80)
            
            return 0 if total_procesadas > 0 else 1
            
        finally:
            # Limpiar directorio temporal
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                print(f"\n🧹 Directorio temporal eliminado: {temp_dir}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    exit(main())

