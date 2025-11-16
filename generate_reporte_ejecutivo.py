#!/usr/bin/env python3
"""
Reporte Ejecutivo Completo: Estado de la DB y Ejecución de Jobs
Incluye última factura procesada, estado de jobs, y datos de septiembre
"""

import sys
from pathlib import Path
from datetime import datetime, date
from dotenv import load_dotenv
from calendar import monthrange

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.db.database import get_database
from src.db.repositories import FacturaRepository, EventRepository, SyncStateRepository
from sqlalchemy import text, func, extract

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
    if isinstance(dt, date):
        return dt.strftime('%Y-%m-%d')
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def main():
    print("=" * 100)
    print("📊 REPORTE EJECUTIVO - ESTADO DEL SISTEMA DE EXTRACCIÓN DE FACTURAS")
    print("=" * 100)
    print(f"Fecha del reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    db = get_database()
    
    try:
        factura_repo = FacturaRepository(db)
        event_repo = EventRepository(db)
        sync_repo = SyncStateRepository(db)
        
        with db.get_session() as session:
            # ============================================================
            # 1. ÚLTIMA FACTURA PROCESADA
            # ============================================================
            print("🔍 ÚLTIMA FACTURA PROCESADA")
            print("-" * 100)
            
            result = session.execute(text("""
                SELECT 
                    id, drive_file_name, proveedor_text, numero_factura,
                    fecha_emision, importe_total, confianza, extractor, 
                    estado, creado_en, actualizado_en, drive_modified_time
                FROM facturas
                ORDER BY creado_en DESC
                LIMIT 1
            """))
            
            ultima = result.fetchone()
            if ultima:
                print(f"✅ Última factura procesada encontrada")
                print(f"   📄 Archivo: {ultima[1]}")
                print(f"   🏢 Proveedor: {ultima[2] or 'N/A'}")
                print(f"   🔢 Número: {ultima[3] or 'N/A'}")
                print(f"   📅 Fecha emisión: {format_date(ultima[4])}")
                print(f"   💰 Importe: {format_currency(ultima[5])}")
                print(f"   🎚️  Confianza: {ultima[6] or 'N/A'}")
                print(f"   🤖 Extractor: {ultima[7] or 'N/A'}")
                print(f"   📊 Estado: {ultima[8] or 'N/A'}")
                print(f"   ⏰ Creado en: {format_date(ultima[9])}")
                print(f"   🔄 Actualizado en: {format_date(ultima[10])}")
                if ultima[11]:
                    print(f"   📁 Modificado en Drive: {format_date(ultima[11])}")
            else:
                print("⚠️  No hay facturas procesadas aún")
            
            print()
            
            # ============================================================
            # 2. ESTADO DE EJECUCIÓN DE JOBS
            # ============================================================
            print("⚙️  ESTADO DE EJECUCIÓN DE JOBS")
            print("-" * 100)
            
            # Último evento de ingest
            result = session.execute(text("""
                SELECT etapa, nivel, detalle, ts, drive_file_id
                FROM ingest_events
                ORDER BY ts DESC
                LIMIT 5
            """))
            
            ultimos_eventos = result.fetchall()
            if ultimos_eventos:
                print("📋 Últimos 5 eventos de procesamiento:")
                for i, evento in enumerate(ultimos_eventos, 1):
                    print(f"   {i}. [{format_date(evento[3])}] {evento[0]} - {evento[1]}")
                    if evento[2]:
                        print(f"      {evento[2][:80]}...")
            else:
                print("⚠️  No hay eventos registrados")
            
            # Estado de sincronización incremental
            last_sync = sync_repo.get_value('last_sync_time')
            if last_sync:
                print(f"\n🔄 Última sincronización incremental: {last_sync}")
            else:
                print("\n⚠️  No hay registro de última sincronización incremental")
            
            # Estadísticas de eventos por etapa
            result = session.execute(text("""
                SELECT etapa, COUNT(*) as count, MAX(ts) as ultimo
                FROM ingest_events
                GROUP BY etapa
                ORDER BY ultimo DESC
            """))
            
            eventos_por_etapa = result.fetchall()
            if eventos_por_etapa:
                print("\n📊 Eventos por etapa:")
                for etapa, count, ultimo in eventos_por_etapa:
                    print(f"   - {etapa}: {count} eventos (último: {format_date(ultimo)})")
            
            print()
            
            # ============================================================
            # 3. DATOS DE SEPTIEMBRE
            # ============================================================
            print("📅 DATOS DE SEPTIEMBRE")
            print("-" * 100)
            
            # Buscar por nombre de carpeta "septiembre"
            facturas_sept_carpeta = factura_repo.get_facturas_by_month('septiembre')
            
            # Buscar por fecha (2024 y 2025)
            september_data_2024 = factura_repo.get_summary_by_month(9, 2024)
            september_data_2025 = factura_repo.get_summary_by_month(9, 2025)
            
            # Mostrar datos por carpeta
            if facturas_sept_carpeta:
                print(f"📁 Facturas en carpeta 'septiembre': {len(facturas_sept_carpeta)}")
                total_carpeta = sum(f.get('importe_total', 0) for f in facturas_sept_carpeta)
                print(f"   💰 Importe total: {format_currency(total_carpeta)}")
                print("\n   📋 Listado de facturas:")
                for i, fact in enumerate(facturas_sept_carpeta[:10], 1):
                    print(f"   {i}. {fact['drive_file_name']}")
                    print(f"      🏢 {fact['proveedor_text'] or 'N/A'} | 💰 {format_currency(fact['importe_total'])}")
                    print(f"      📅 {format_date(fact['fecha_emision'])} | 📊 {fact['estado']}")
                if len(facturas_sept_carpeta) > 10:
                    print(f"   ... y {len(facturas_sept_carpeta) - 10} más")
            else:
                print("⚠️  No hay facturas en carpeta 'septiembre'")
            
            # Mostrar datos por fecha
            print(f"\n📊 Por fecha de emisión:")
            print(f"   Septiembre 2024: {september_data_2024['total_facturas']} facturas, {format_currency(september_data_2024['importe_total'])}")
            print(f"   Septiembre 2025: {september_data_2025['total_facturas']} facturas, {format_currency(september_data_2025['importe_total'])}")
            
            # Resumen combinado
            total_sept = len(facturas_sept_carpeta) or (september_data_2024['total_facturas'] + september_data_2025['total_facturas'])
            if total_sept > 0:
                print(f"\n✅ Total facturas de septiembre: {total_sept}")
            else:
                print("\n⚠️  No hay facturas registradas para septiembre (ni por carpeta ni por fecha)")
            
            print()
            
            # ============================================================
            # 4. ESTADÍSTICAS GENERALES
            # ============================================================
            print("📈 ESTADÍSTICAS GENERALES")
            print("-" * 100)
            
            stats = factura_repo.get_statistics()
            
            print(f"Total facturas en BD: {stats['total_facturas']}")
            print(f"Importe total acumulado: {format_currency(stats['total_importe'])}")
            print(f"Promedio por factura: {format_currency(stats['promedio_importe'])}")
            
            print("\n📊 Por estado:")
            for estado, count in stats['por_estado'].items():
                pct = (count / stats['total_facturas'] * 100) if stats['total_facturas'] > 0 else 0
                print(f"   - {estado}: {count} ({pct:.1f}%)")
            
            print("\n🎚️  Por confianza:")
            for conf, count in stats['por_confianza'].items():
                pct = (count / stats['total_facturas'] * 100) if stats['total_facturas'] > 0 else 0
                print(f"   - {conf}: {count} ({pct:.1f}%)")
            
            # Estadísticas por extractor
            result = session.execute(text("""
                SELECT extractor, COUNT(*) as count, 
                       SUM(importe_total) as total,
                       AVG(CASE WHEN confianza = 'alta' THEN 100 
                                WHEN confianza = 'media' THEN 50 
                                WHEN confianza = 'baja' THEN 25 
                                ELSE 0 END) as confianza_promedio
                FROM facturas
                WHERE extractor IS NOT NULL
                GROUP BY extractor
                ORDER BY count DESC
            """))
            
            extractores = result.fetchall()
            if extractores:
                print("\n🤖 Por extractor:")
                for ext, count, total, conf in extractores:
                    print(f"   - {ext}: {count} facturas, {format_currency(total)}, confianza {conf:.1f}%")
            
            print()
            
            # ============================================================
            # 5. ACTIVIDAD RECIENTE
            # ============================================================
            print("🕐 ACTIVIDAD RECIENTE (Últimas 24 horas)")
            print("-" * 100)
            
            result = session.execute(text("""
                SELECT COUNT(*) 
                FROM facturas
                WHERE creado_en >= NOW() - INTERVAL '24 hours'
            """))
            facturas_24h = result.fetchone()[0]
            
            result = session.execute(text("""
                SELECT COUNT(*) 
                FROM ingest_events
                WHERE ts >= NOW() - INTERVAL '24 hours'
            """))
            eventos_24h = result.fetchone()[0]
            
            print(f"📄 Facturas procesadas (24h): {facturas_24h}")
            print(f"📋 Eventos registrados (24h): {eventos_24h}")
            
            # Facturas procesadas hoy
            result = session.execute(text("""
                SELECT COUNT(*) 
                FROM facturas
                WHERE DATE(creado_en) = CURRENT_DATE
            """))
            facturas_hoy = result.fetchone()[0]
            print(f"📅 Facturas procesadas hoy: {facturas_hoy}")
            
            print()
            
            # ============================================================
            # 6. TOP PROVEEDORES
            # ============================================================
            print("🏢 TOP 10 PROVEEDORES POR IMPORTE")
            print("-" * 100)
            
            result = session.execute(text("""
                SELECT proveedor_text, COUNT(*) as count, SUM(importe_total) as total
                FROM facturas
                WHERE proveedor_text IS NOT NULL AND importe_total IS NOT NULL
                GROUP BY proveedor_text
                ORDER BY total DESC
                LIMIT 10
            """))
            
            top_proveedores = result.fetchall()
            if top_proveedores:
                for i, (prov, count, total) in enumerate(top_proveedores, 1):
                    print(f"   {i}. {prov}: {count} facturas, {format_currency(total)}")
            else:
                print("   ⚠️  No hay datos de proveedores")
            
            print()
            
            # ============================================================
            # RESUMEN EJECUTIVO
            # ============================================================
            print("=" * 100)
            print("✅ RESUMEN EJECUTIVO")
            print("=" * 100)
            
            if ultima:
                print(f"✅ Última factura procesada: {ultima[1]} ({format_date(ultima[9])})")
            else:
                print("⚠️  No hay facturas procesadas")
            
            print(f"✅ Total facturas en BD: {stats['total_facturas']}")
            print(f"✅ Importe total acumulado: {format_currency(stats['total_importe'])}")
            print(f"✅ Facturas procesadas hoy: {facturas_hoy}")
            print(f"✅ Facturas procesadas (24h): {facturas_24h}")
            
            # Calcular total de septiembre
            total_sept_final = len(facturas_sept_carpeta) if facturas_sept_carpeta else 0
            if total_sept_final == 0:
                total_sept_final = september_data_2024['total_facturas'] + september_data_2025['total_facturas']
            
            if total_sept_final > 0:
                importe_sept = sum(f.get('importe_total', 0) for f in facturas_sept_carpeta) if facturas_sept_carpeta else 0
                if importe_sept == 0:
                    importe_sept = september_data_2024['importe_total'] + september_data_2025['importe_total']
                print(f"✅ Facturas de septiembre: {total_sept_final} ({format_currency(importe_sept)})")
            else:
                print("⚠️  No hay facturas de septiembre")
            
            # Verificar si hay jobs corriendo (eventos recientes)
            if eventos_24h > 0:
                print(f"✅ Sistema activo: {eventos_24h} eventos en las últimas 24h")
            else:
                print("⚠️  No hay actividad reciente (últimas 24h)")
            
            # Verificar facturas pendientes de revisión
            if 'revisar' in stats['por_estado']:
                revisar_count = stats['por_estado']['revisar']
                if revisar_count > 0:
                    print(f"⚠️  {revisar_count} facturas requieren revisión manual")
            
            if 'error' in stats['por_estado']:
                error_count = stats['por_estado']['error']
                if error_count > 0:
                    print(f"❌ {error_count} facturas con errores")
            
            print()
            print("=" * 100)
            
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

