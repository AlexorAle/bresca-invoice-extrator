#!/usr/bin/env python3

"""
Script para procesar 10 facturas y comparar resultados de OpenAI con BD
"""

import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.security.secrets import load_env, validate_secrets
from src.logging_conf import get_logger
from src.db.database import get_database
from src.drive_client import DriveClient
from src.ocr_extractor import InvoiceExtractor
from src.pipeline.ingest import process_batch
from sqlalchemy import text

load_env()
validate_secrets()

logger = get_logger(__name__)

def main():
    print("🎯 PROCESAMIENTO DE 10 FACTURAS - VERIFICACIÓN COMPLETA")
    print("=" * 80)

    # Almacenar resultados de OpenAI antes de guardar en BD
    openai_results = {}

    try:
        # Inicializar componentes
        print("\n🔧 Inicializando componentes...")
        db = get_database()
        db.init_db()
        drive_client = DriveClient()
        extractor = InvoiceExtractor()
        print("✅ Componentes inicializados")

        # Obtener carpeta base
        import os
        base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        if not base_folder_id:
            print("❌ GOOGLE_DRIVE_FOLDER_ID no configurado")
            return

        # Listar todos los PDFs
        print("\n🔍 Buscando facturas en Google Drive...")
        all_files = drive_client.list_all_pdfs_recursive(base_folder_id)

        if not all_files:
            print("❌ No se encontraron archivos PDF")
            return

        # Limitar a las primeras 10
        files_to_process = all_files[:10]
        print(f"\n📋 Seleccionadas {len(files_to_process)} facturas:")
        for i, f in enumerate(files_to_process, 1):
            print(f"  {i}. {f.get('name', 'Unknown')}")

        # Descargar archivos
        print("\n⬇️  Descargando archivos...")
        temp_path = Path(os.getenv('TEMP_PATH', 'temp'))
        temp_path.mkdir(parents=True, exist_ok=True)

        downloaded_files = []
        for i, file_info in enumerate(files_to_process, 1):
            file_id = file_info['id']
            file_name = file_info['name']
            
            from src.pipeline.validate import sanitize_filename
            safe_name = sanitize_filename(file_name)
            local_path = temp_path / safe_name

            try:
                success = drive_client.download_file(file_id, str(local_path))
                if success:
                    file_info['local_path'] = str(local_path)
                    downloaded_files.append(file_info)
                    print(f"  ✅ {i}/{len(files_to_process)}: {file_name}")
                else:
                    print(f"  ❌ {i}/{len(files_to_process)}: {file_name} (error descarga)")
            except Exception as e:
                print(f"  ❌ {i}/{len(files_to_process)}: {file_name} - {str(e)[:50]}")

        if not downloaded_files:
            print("\n❌ No se pudieron descargar archivos")
            return

        print(f"\n✅ {len(downloaded_files)} archivos descargados")

        # Extraer datos con OpenAI ANTES de procesar (para comparación)
        print("\n🤖 Extrayendo datos con OpenAI (antes de guardar en BD)...")
        print("=" * 80)
        for file_info in downloaded_files:
            file_name = file_info['name']
            local_path = file_info['local_path']
            drive_file_id = file_info['id']
            
            print(f"\n📄 {file_name}")
            try:
                result = extractor.extract_invoice_data(local_path)
                openai_results[drive_file_id] = {
                    'file_name': file_name,
                    'nombre_cliente': result.get('nombre_cliente'),
                    'importe_total': result.get('importe_total'),
                    'confianza': result.get('confianza'),
                    'extractor_used': result.get('extractor_used', 'openai')
                }
                print(f"   Cliente: {result.get('nombre_cliente')}")
                print(f"   Importe: {result.get('importe_total')}")
                print(f"   Confianza: {result.get('confianza')}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                openai_results[drive_file_id] = {
                    'file_name': file_name,
                    'error': str(e)
                }

        # Procesar batch (guardar en BD)
        print("\n\n💾 Procesando batch y guardando en BD...")
        print("=" * 80)
        start_time = datetime.utcnow()
        stats = process_batch(downloaded_files, extractor, db)
        duration = (datetime.utcnow() - start_time).total_seconds()

        print(f"\n📊 Estadísticas del procesamiento:")
        print(f"   Total: {stats['total']}")
        print(f"   Exitosos: {stats['exitosos']}")
        print(f"   Fallidos: {stats['fallidos']}")
        print(f"   Duplicados: {stats['duplicados']}")
        print(f"   Ignorados: {stats['ignorados']}")
        print(f"   Duración: {duration:.1f}s")

        # Consultar BD para comparar
        print("\n\n🔍 VERIFICACIÓN EN BASE DE DATOS")
        print("=" * 80)

        bd_results = {}
        try:
            with db.get_session() as session:
                for file_info in downloaded_files:
                    drive_file_id = file_info['id']
                    file_name = file_info['name']
                    
                    result = session.execute(
                        text("""
                            SELECT proveedor_text, importe_total, confianza, extractor, estado, creado_en
                            FROM facturas
                            WHERE drive_file_id = :file_id
                            ORDER BY creado_en DESC
                            LIMIT 1
                        """),
                        {'file_id': drive_file_id}
                    )
                    
                    row = result.fetchone()
                    if row:
                        bd_results[drive_file_id] = {
                            'file_name': file_name,
                            'nombre_cliente': row[0],
                            'importe_total': row[1],
                            'confianza': row[2],
                            'extractor': row[3],
                            'estado': row[4],
                            'creado_en': row[5]
                        }
                    else:
                        bd_results[drive_file_id] = {
                            'file_name': file_name,
                            'error': 'No encontrada en BD'
                        }
        except Exception as e:
            print(f"❌ Error consultando BD: {e}")
            import traceback
            traceback.print_exc()

        # Comparar resultados
        print("\n\n📊 COMPARACIÓN: OpenAI vs Base de Datos")
        print("=" * 80)

        matches = 0
        mismatches = 0
        not_in_bd = 0

        for drive_file_id in openai_results.keys():
            openai_data = openai_results[drive_file_id]
            bd_data = bd_results.get(drive_file_id, {})
            
            file_name = openai_data['file_name']
            
            print(f"\n📄 {file_name}")
            print("-" * 80)
            
            # OpenAI
            if 'error' in openai_data:
                print(f"   🤖 OpenAI: ❌ Error - {openai_data['error']}")
            else:
                print(f"   🤖 OpenAI:")
                print(f"      Cliente: {openai_data.get('nombre_cliente')}")
                print(f"      Importe: {openai_data.get('importe_total')}")
                print(f"      Confianza: {openai_data.get('confianza')}")
            
            # BD
            if 'error' in bd_data:
                print(f"   💾 BD: ❌ {bd_data['error']}")
                not_in_bd += 1
            else:
                print(f"   💾 BD:")
                print(f"      Cliente: {bd_data.get('nombre_cliente')}")
                print(f"      Importe: {bd_data.get('importe_total')}")
                print(f"      Confianza: {bd_data.get('confianza')}")
                print(f"      Extractor: {bd_data.get('extractor')}")
                print(f"      Estado: {bd_data.get('estado')}")
                
                # Comparar
                if 'error' not in openai_data:
                    cliente_match = str(openai_data.get('nombre_cliente', '')).strip() == str(bd_data.get('nombre_cliente', '')).strip()
                    importe_match = abs(float(openai_data.get('importe_total', 0) or 0) - float(bd_data.get('importe_total', 0) or 0)) < 0.01
                    confianza_match = openai_data.get('confianza') == bd_data.get('confianza')
                    
                    if cliente_match and importe_match and confianza_match:
                        print(f"   ✅ COINCIDENCIA PERFECTA")
                        matches += 1
                    else:
                        print(f"   ⚠️  DIFERENCIAS:")
                        if not cliente_match:
                            print(f"      - Cliente: OpenAI='{openai_data.get('nombre_cliente')}' vs BD='{bd_data.get('nombre_cliente')}'")
                        if not importe_match:
                            print(f"      - Importe: OpenAI={openai_data.get('importe_total')} vs BD={bd_data.get('importe_total')}")
                        if not confianza_match:
                            print(f"      - Confianza: OpenAI={openai_data.get('confianza')} vs BD={bd_data.get('confianza')}")
                        mismatches += 1

        # Resumen final
        print("\n\n" + "=" * 80)
        print("📋 RESUMEN EJECUTIVO")
        print("=" * 80)
        print(f"✅ Coincidencias perfectas: {matches}/{len(openai_results)}")
        print(f"⚠️  Diferencias encontradas: {mismatches}")
        print(f"❌ No guardadas en BD: {not_in_bd}")
        print(f"📊 Tasa de éxito: {(matches/len(openai_results)*100):.1f}%")
        
        # Estadísticas BD
        with db.get_session() as session:
            result = session.execute(text("SELECT COUNT(*) FROM facturas"))
            total_bd = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE extractor = 'openai'"))
            openai_bd = result.fetchone()[0]
            
            result = session.execute(text("SELECT SUM(importe_total) FROM facturas WHERE importe_total IS NOT NULL"))
            total_importe = result.fetchone()[0] or 0
            
            print(f"\n💾 Base de Datos:")
            print(f"   Total facturas: {total_bd}")
            print(f"   Por OpenAI: {openai_bd}")
            print(f"   Importe total: €{total_importe:.2f}")

        if matches == len(openai_results) and not_in_bd == 0:
            print("\n✅ ¡TODO CORRECTO! Todos los datos coinciden y están guardados")
        else:
            print("\n⚠️  Requiere revisión")

        # Limpiar archivos temporales
        print("\n🧹 Limpiando archivos temporales...")
        for file_info in downloaded_files:
            local_path = file_info.get('local_path')
            if local_path and Path(local_path).exists():
                try:
                    Path(local_path).unlink()
                except:
                    pass

    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()

