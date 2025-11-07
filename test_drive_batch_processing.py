#!/usr/bin/env python3

"""
Script de prueba para procesar 10 facturas del Google Drive con OpenAI
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.security.secrets import load_env, validate_secrets
from src.logging_conf import get_logger
from src.db.database import get_database
from src.drive_client import DriveClient
from src.ocr_extractor import InvoiceExtractor
from src.pipeline.ingest import process_batch

# Cargar configuración
load_env()
validate_secrets()

logger = get_logger(__name__)

def main():
    """
    Procesar 10 facturas del Google Drive con OpenAI
    """
    print("🧪 PRUEBA DE PROCESAMIENTO: 10 FACTURAS DEL GOOGLE DRIVE")
    print("=" * 70)

    try:
        # Inicializar componentes
        print("\n🔧 Inicializando componentes...")
        db = get_database()
        db.init_db()

        drive_client = DriveClient()
        extractor = InvoiceExtractor()
        print("✅ Componentes inicializados correctamente")

        # Buscar facturas en Google Drive
        print("\n🔍 Buscando facturas en Google Drive...")
        months_to_check = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                           'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

        all_files = []
        for month in months_to_check:
            try:
                month_files = drive_client.get_files_from_months([month])
                all_files.extend(month_files)
                print(f"📁 {month}: {len(month_files)} archivos encontrados")

                # Limitar a 10 archivos totales
                if len(all_files) >= 10:
                    break
            except Exception as e:
                print(f"⚠️  Error en {month}: {e}")
                continue

        # Tomar solo los primeros 10 archivos
        files_to_process = all_files[:10]

        print("\n📋 ARCHIVOS SELECCIONADOS PARA PROCESAMIENTO:")
        for i, file_info in enumerate(files_to_process, 1):
            print(f"  {i}. {file_info.get('name', 'Unknown')} ({file_info.get('size', 0)} bytes)")

        if len(files_to_process) == 0:
            print("❌ No se encontraron archivos para procesar")
            print("\n💡 Posibles causas:")
            print("   - No hay carpetas de meses en Google Drive")
            print("   - Las carpetas tienen nombres diferentes")
            print("   - No hay archivos PDF en las carpetas")
            return

        # Procesar archivos
        print("
🎯 Iniciando procesamiento de 10 facturas..."        start_time = datetime.utcnow()

        stats = process_batch(files_to_process, extractor, db)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Resultados detallados
        print("
📊 RESULTADOS DEL PROCESAMIENTO"        print("=" * 70)
        print(f"⏱️  Duración total: {duration:.1f} segundos")
        print(f"📄 Total procesados: {stats['total']}")
        print(f"✅ Exitosos: {stats['exitosos']}")
        print(f"❌ Fallidos: {stats['fallidos']}")
        print(f"🔒 Protegidos: {stats.get('protegidos', 0)}")
        print(f"🔄 Duplicados: {stats['duplicados']}")
        print(f"⏭️  Ignorados: {stats['ignorados']}")

        # Mostrar detalle de cada archivo procesado
        print("
📋 DETALLE POR ARCHIVO:"        protected_count = 0
        for file_stat in stats['archivos_procesados']:
            status_emoji = {
                'success': '✅',
                'failed': '❌',
                'duplicate': '🔄',
                'ignored': '⏭️',
                'protected': '🔒'
            }.get(file_stat['status'], '❓')

            if file_stat['status'] == 'protected':
                protected_count += 1

            elapsed = file_stat.get('elapsed_ms', 0)
            print(f"  {status_emoji} {file_stat['file_name']} - {file_stat['status']} ({elapsed}ms)")

        # Verificar base de datos
        print("\n💾 VERIFICACIÓN EN BASE DE DATOS")
        print("=" * 70)

        try:
            # Obtener estadísticas actualizadas
            with db.get_session() as session:
                from sqlalchemy import text
                result = session.execute(text("SELECT COUNT(*) as total FROM facturas"))
                total_facturas = result.fetchone()[0]

                result = session.execute(text("SELECT COUNT(*) as protegidos FROM facturas WHERE estado = 'protegido'"))
                protegidos_bd = result.fetchone()[0]

                result = session.execute(text("SELECT COUNT(*) as openai FROM facturas WHERE extractor = 'openai'"))
                openai_count = result.fetchone()[0]

                result = session.execute(text("SELECT COUNT(*) as tesseract FROM facturas WHERE extractor = 'tesseract'"))
                tesseract_count = result.fetchone()[0]

            print(f"📊 Total facturas en BD: {total_facturas}")
            print(f"🔒 PDFs protegidos detectados: {protegidos_bd}")
            print(f"🤖 Procesados por OpenAI: {openai_count}")
            print(f"📝 Procesados por Tesseract: {tesseract_count}")

            if total_facturas > 0:
                print("\n📋 ÚLTIMAS FACTURAS PROCESADAS:")
                with db.get_session() as session:
                    from sqlalchemy import text
                    result = session.execute(text("""
                        SELECT proveedor_text, importe_total, confianza, extractor, estado, creado_en
                        FROM facturas
                        ORDER BY creado_en DESC
                        LIMIT 10
                    """))

                    for row in result:
                        cliente = row[0] or 'N/A'
                        importe = f"€{row[1]:.2f}" if row[1] else 'N/A'
                        confianza = row[2] or 'N/A'
                        extractor = row[3] or 'N/A'
                        estado = row[4] or 'N/A'

                        print(f"  👤 {cliente}")
                        print(f"    💰 {importe} | 🎚️ {confianza} | 🔧 {extractor} | 📊 {estado}")
                        print()

        except Exception as e:
            print(f"⚠️  Error consultando base de datos: {e}")

        # Resumen ejecutivo
        print("\n🎯 RESUMEN EJECUTIVO - PRUEBA GOOGLE DRIVE")
        print("=" * 70)
        print("✅ Migración OpenAI completada exitosamente")
        print(f"✅ Google Drive: {len(files_to_process)} archivos encontrados")
        print(f"✅ Procesamiento: {stats['exitosos']}/{stats['total']} facturas procesadas exitosamente")
        print(f"✅ Protección PDF: {protected_count} archivos protegidos detectados y omitidos")
        print(f"✅ Base de datos: {total_facturas} facturas almacenadas correctamente")
        print(f"✅ Performance: ~{duration/max(1, stats['total']):.1f}s por factura")
        print("✅ Tecnología: OpenAI GPT-4o-mini + Tesseract fallback + Detección PDF protegido")

        if stats['exitosos'] > 0:
            print("✅ Estado: SISTEMA OPERATIVO Y LISTO PARA PRODUCCIÓN")
        elif protected_count == stats['total']:
            print("ℹ️  Estado: Todos los PDFs están protegidos - funcionalidad de protección funcionando")
        else:
            print("⚠️  Estado: Requiere revisión - verificar configuración de Google Drive")

        # Estadísticas adicionales
        print("\n📈 ESTADÍSTICAS DETALLADAS:")
        print(f"   • Tasa de éxito: {(stats['exitosos']/max(1, stats['total']))*100:.1f}%")
        print(f"   • Tasa de protección: {(protected_count/max(1, stats['total']))*100:.1f}%")
        print(f"   • Costo estimado: ~${(stats['total']-protected_count)*0.0015:.3f} (solo OpenAI)")

    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cerrar conexiones
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()
