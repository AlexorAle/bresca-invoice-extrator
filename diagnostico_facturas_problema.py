#!/usr/bin/env python3
"""
Diagnóstico de facturas: Listar todas las facturas con problemas y sus carpetas de origen
"""

import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.db.database import get_database
from src.db.repositories import FacturaRepository, EventRepository
from sqlalchemy import text

load_dotenv()

def format_currency(amount):
    """Formatear importe como moneda"""
    if amount is None:
        return "N/A"
    return f"€{float(amount):,.2f}"

def format_date(dt):
    """Formatear fecha/hora"""
    if dt is None:
        return "N/A"
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)

def main():
    print("=" * 100)
    print("🔍 DIAGNÓSTICO DE FACTURAS - PROBLEMAS Y CARPETAS DE ORIGEN")
    print("=" * 100)
    print(f"Fecha del reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    db = get_database()
    
    try:
        factura_repo = FacturaRepository(db)
        event_repo = EventRepository(db)
        
        with db.get_session() as session:
            # ============================================================
            # 1. TODAS LAS CARPETAS Y SUS FACTURAS
            # ============================================================
            print("📁 CARPETAS EN LA BASE DE DATOS")
            print("-" * 100)
            
            result = session.execute(text("""
                SELECT 
                    drive_folder_name,
                    COUNT(*) as total,
                    COUNT(CASE WHEN estado = 'error' THEN 1 END) as errores,
                    COUNT(CASE WHEN estado = 'revisar' THEN 1 END) as revisar,
                    COUNT(CASE WHEN estado = 'procesado' THEN 1 END) as procesadas,
                    SUM(importe_total) as importe_total
                FROM facturas
                GROUP BY drive_folder_name
                ORDER BY drive_folder_name
            """))
            
            carpetas = result.fetchall()
            if carpetas:
                print(f"Total de carpetas encontradas: {len(carpetas)}\n")
                for carpeta, total, errores, revisar, procesadas, importe in carpetas:
                    print(f"📂 {carpeta or '(sin carpeta)'}")
                    print(f"   Total facturas: {total}")
                    print(f"   ✅ Procesadas: {procesadas}")
                    print(f"   ⚠️  Revisar: {revisar}")
                    print(f"   ❌ Errores: {errores}")
                    print(f"   💰 Importe total: {format_currency(importe)}")
                    print()
            else:
                print("⚠️  No se encontraron carpetas")
            
            print()
            
            # ============================================================
            # 2. FACTURAS CON PROBLEMAS
            # ============================================================
            print("⚠️  FACTURAS CON PROBLEMAS")
            print("-" * 100)
            
            # Facturas con estado 'error'
            result = session.execute(text("""
                SELECT 
                    id, drive_file_name, drive_folder_name, proveedor_text,
                    numero_factura, importe_total, estado, error_msg,
                    creado_en, extractor, confianza
                FROM facturas
                WHERE estado = 'error'
                ORDER BY creado_en DESC
            """))
            
            facturas_error = result.fetchall()
            if facturas_error:
                print(f"❌ FACTURAS CON ERROR ({len(facturas_error)}):")
                print()
                for f in facturas_error:
                    print(f"   ID: {f[0]}")
                    print(f"   📄 Archivo: {f[1]}")
                    print(f"   📁 Carpeta: {f[2] or 'N/A'}")
                    print(f"   🏢 Proveedor: {f[3] or 'N/A'}")
                    print(f"   🔢 Número: {f[4] or 'N/A'}")
                    print(f"   💰 Importe: {format_currency(f[5])}")
                    print(f"   📊 Estado: {f[6]}")
                    print(f"   ❌ Error: {f[7] or 'N/A'}")
                    print(f"   ⏰ Creado: {format_date(f[8])}")
                    print(f"   🤖 Extractor: {f[9] or 'N/A'}")
                    print(f"   🎚️  Confianza: {f[10] or 'N/A'}")
                    print()
            else:
                print("✅ No hay facturas con estado 'error'")
            
            print()
            
            # Facturas con estado 'revisar'
            result = session.execute(text("""
                SELECT 
                    id, drive_file_name, drive_folder_name, proveedor_text,
                    numero_factura, importe_total, estado, error_msg,
                    creado_en, extractor, confianza
                FROM facturas
                WHERE estado = 'revisar'
                ORDER BY drive_folder_name, creado_en DESC
            """))
            
            facturas_revisar = result.fetchall()
            if facturas_revisar:
                print(f"⚠️  FACTURAS QUE REQUIEREN REVISIÓN ({len(facturas_revisar)}):")
                print()
                
                # Agrupar por carpeta
                por_carpeta = {}
                for f in facturas_revisar:
                    carpeta = f[2] or '(sin carpeta)'
                    if carpeta not in por_carpeta:
                        por_carpeta[carpeta] = []
                    por_carpeta[carpeta].append(f)
                
                for carpeta, facturas in sorted(por_carpeta.items()):
                    print(f"   📂 CARPETA: {carpeta} ({len(facturas)} facturas)")
                    for f in facturas[:5]:  # Mostrar primeras 5 de cada carpeta
                        print(f"      - {f[1]}")
                        print(f"        🏢 {f[3] or 'N/A'} | 💰 {format_currency(f[5])} | 📅 {format_date(f[8])}")
                    if len(facturas) > 5:
                        print(f"      ... y {len(facturas) - 5} más")
                    print()
            else:
                print("✅ No hay facturas que requieran revisión")
            
            print()
            
            # ============================================================
            # 3. BÚSQUEDA ESPECÍFICA DE SEPTIEMBRE
            # ============================================================
            print("🔍 BÚSQUEDA ESPECÍFICA: SEPTIEMBRE")
            print("-" * 100)
            
            # Buscar por nombre de carpeta (case insensitive)
            result = session.execute(text("""
                SELECT 
                    id, drive_file_name, drive_folder_name, proveedor_text,
                    numero_factura, importe_total, estado, fecha_emision,
                    creado_en
                FROM facturas
                WHERE LOWER(drive_folder_name) LIKE '%septiembre%'
                   OR LOWER(drive_folder_name) LIKE '%sept%'
                ORDER BY drive_folder_name, creado_en DESC
            """))
            
            facturas_sept = result.fetchall()
            if facturas_sept:
                print(f"✅ Facturas encontradas con 'septiembre' en nombre de carpeta: {len(facturas_sept)}")
                print()
                
                # Agrupar por carpeta exacta
                por_carpeta_sept = {}
                for f in facturas_sept:
                    carpeta = f[2] or '(sin carpeta)'
                    if carpeta not in por_carpeta_sept:
                        por_carpeta_sept[carpeta] = []
                    por_carpeta_sept[carpeta].append(f)
                
                for carpeta, facturas in sorted(por_carpeta_sept.items()):
                    print(f"   📂 {carpeta}: {len(facturas)} facturas")
                    total_carpeta = sum(float(f[5] or 0) for f in facturas)
                    print(f"      💰 Importe total: {format_currency(total_carpeta)}")
                    print()
                    for f in facturas[:10]:  # Mostrar primeras 10
                        print(f"      - {f[1]}")
                        print(f"        🏢 {f[3] or 'N/A'} | 💰 {format_currency(f[5])} | 📅 {format_date(f[7])}")
                    if len(facturas) > 10:
                        print(f"      ... y {len(facturas) - 10} más")
                    print()
            else:
                print("⚠️  No se encontraron facturas con 'septiembre' en el nombre de carpeta")
            
            # Buscar por fecha de emisión en septiembre
            result = session.execute(text("""
                SELECT 
                    id, drive_file_name, drive_folder_name, proveedor_text,
                    numero_factura, importe_total, estado, fecha_emision,
                    creado_en
                FROM facturas
                WHERE EXTRACT(MONTH FROM fecha_emision) = 9
                   OR (fecha_emision IS NULL AND EXTRACT(MONTH FROM fecha_recepcion) = 9)
                ORDER BY fecha_emision DESC, creado_en DESC
            """))
            
            facturas_sept_fecha = result.fetchall()
            if facturas_sept_fecha:
                print(f"\n✅ Facturas con fecha de emisión en septiembre: {len(facturas_sept_fecha)}")
                print()
                for f in facturas_sept_fecha[:10]:
                    print(f"   - {f[1]}")
                    print(f"     📁 Carpeta: {f[2] or 'N/A'} | 📅 Fecha: {format_date(f[7])}")
                    print(f"     🏢 {f[3] or 'N/A'} | 💰 {format_currency(f[5])}")
                if len(facturas_sept_fecha) > 10:
                    print(f"   ... y {len(facturas_sept_fecha) - 10} más")
            else:
                print("\n⚠️  No se encontraron facturas con fecha de emisión en septiembre")
            
            print()
            
            # ============================================================
            # 4. EVENTOS DE ERROR RECIENTES
            # ============================================================
            print("📋 EVENTOS DE ERROR RECIENTES")
            print("-" * 100)
            
            result = session.execute(text("""
                SELECT etapa, nivel, detalle, ts, drive_file_id
                FROM ingest_events
                WHERE nivel = 'ERROR'
                ORDER BY ts DESC
                LIMIT 20
            """))
            
            eventos_error = result.fetchall()
            if eventos_error:
                print(f"Últimos {len(eventos_error)} eventos de error:\n")
                for evento in eventos_error:
                    print(f"   [{format_date(evento[3])}] {evento[0]} - {evento[1]}")
                    if evento[2]:
                        print(f"      {evento[2][:100]}")
                    print(f"      File ID: {evento[4]}")
                    print()
            else:
                print("✅ No hay eventos de error recientes")
            
            print()
            
            # ============================================================
            # RESUMEN
            # ============================================================
            print("=" * 100)
            print("📊 RESUMEN")
            print("=" * 100)
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas"))
            total = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE estado = 'error'"))
            errores = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE estado = 'revisar'"))
            revisar = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE estado = 'procesado'"))
            procesadas = result.fetchone()[0]
            
            result = session.execute(text("""
                SELECT COUNT(DISTINCT drive_folder_name) 
                FROM facturas 
                WHERE drive_folder_name IS NOT NULL
            """))
            total_carpetas = result.fetchone()[0]
            
            print(f"Total facturas en BD: {total}")
            print(f"✅ Procesadas: {procesadas}")
            print(f"⚠️  Requieren revisión: {revisar}")
            print(f"❌ Con errores: {errores}")
            print(f"📁 Carpetas diferentes: {total_carpetas}")
            
            if facturas_sept:
                print(f"\n✅ Facturas de septiembre encontradas: {len(facturas_sept)}")
            else:
                print(f"\n⚠️  No se encontraron facturas de septiembre en la BD")
                print("   Posibles causas:")
                print("   - Las facturas no se han procesado aún")
                print("   - El nombre de carpeta guardado es diferente")
                print("   - Las facturas están en estado 'error' y no se guardaron")
            
            print()
            print("=" * 100)
            
    except Exception as e:
        print(f"❌ Error generando diagnóstico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

