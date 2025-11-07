#!/usr/bin/env python3

"""
Generar resumen ejecutivo completo del procesamiento
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.db.database import get_database
from sqlalchemy import text

load_dotenv()

def main():
    print("=" * 80)
    print("📊 RESUMEN EJECUTIVO - PROCESAMIENTO COMPLETO DE FACTURAS")
    print("=" * 80)

    db = get_database()
    
    try:
        with db.get_session() as session:
            # Estadísticas generales
            result = session.execute(text("SELECT COUNT(*) FROM facturas"))
            total_facturas = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE extractor = 'openai'"))
            openai_count = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE extractor = 'tesseract'"))
            tesseract_count = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE extractor = 'protected'"))
            protected_count = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE confianza = 'alta'"))
            alta_confianza = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE confianza = 'media'"))
            media_confianza = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE confianza = 'baja'"))
            baja_confianza = result.fetchone()[0]
            
            result = session.execute(text("SELECT SUM(importe_total) FROM facturas WHERE importe_total IS NOT NULL"))
            total_importe = result.fetchone()[0] or 0
            
            result = session.execute(text("SELECT AVG(importe_total) FROM facturas WHERE importe_total IS NOT NULL"))
            promedio_importe = result.fetchone()[0] or 0
            
            result = session.execute(text("SELECT MIN(importe_total) FROM facturas WHERE importe_total IS NOT NULL"))
            min_importe = result.fetchone()[0] or 0
            
            result = session.execute(text("SELECT MAX(importe_total) FROM facturas WHERE importe_total IS NOT NULL"))
            max_importe = result.fetchone()[0] or 0
            
            result = session.execute(text("SELECT COUNT(DISTINCT proveedor_text) FROM facturas WHERE proveedor_text IS NOT NULL"))
            proveedores_unicos = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE estado = 'procesado'"))
            procesados = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE estado = 'revisar'"))
            revisar = result.fetchone()[0]
            
            result = session.execute(text("SELECT COUNT(*) FROM facturas WHERE estado = 'duplicado'"))
            duplicados = result.fetchone()[0]
            
            # Top proveedores
            result = session.execute(text("""
                SELECT proveedor_text, COUNT(*) as count, SUM(importe_total) as total
                FROM facturas
                WHERE proveedor_text IS NOT NULL
                GROUP BY proveedor_text
                ORDER BY total DESC
                LIMIT 10
            """))
            
            top_proveedores = []
            for row in result:
                top_proveedores.append({
                    'proveedor': row[0],
                    'count': row[1],
                    'total': row[2]
                })
            
            # Estadísticas por extractor
            result = session.execute(text("""
                SELECT extractor, COUNT(*) as count, SUM(importe_total) as total
                FROM facturas
                WHERE importe_total IS NOT NULL
                GROUP BY extractor
                ORDER BY count DESC
            """))
            
            stats_extractor = {}
            for row in result:
                stats_extractor[row[0]] = {
                    'count': row[1],
                    'total': row[2]
                }
            
            # Últimas facturas procesadas
            result = session.execute(text("""
                SELECT proveedor_text, importe_total, confianza, extractor, estado, creado_en
                FROM facturas
                ORDER BY creado_en DESC
                LIMIT 10
            """))
            
            ultimas = []
            for row in result:
                ultimas.append({
                    'proveedor': row[0],
                    'importe': row[1],
                    'confianza': row[2],
                    'extractor': row[3],
                    'estado': row[4],
                    'fecha': row[5]
                })
            
            # Reporte
            print("\n📈 ESTADÍSTICAS GENERALES")
            print("-" * 80)
            print(f"Total facturas almacenadas: {total_facturas}")
            print(f"Estado 'procesado': {procesados}")
            print(f"Estado 'revisar': {revisar}")
            print(f"Duplicados detectados: {duplicados}")
            
            print("\n🤖 EXTRACTORES UTILIZADOS")
            print("-" * 80)
            print(f"OpenAI GPT-4o-mini: {openai_count} facturas")
            print(f"Tesseract (fallback): {tesseract_count} facturas")
            print(f"PDFs protegidos: {protected_count} facturas")
            
            if stats_extractor:
                print("\n   Desglose por extractor:")
                for ext, stats in stats_extractor.items():
                    if stats['total']:
                        print(f"   - {ext}: {stats['count']} facturas, €{stats['total']:.2f}")
            
            print("\n🎚️  NIVEL DE CONFIANZA")
            print("-" * 80)
            print(f"Alta: {alta_confianza} facturas ({alta_confianza/total_facturas*100:.1f}%)")
            print(f"Media: {media_confianza} facturas ({media_confianza/total_facturas*100:.1f}%)")
            print(f"Baja: {baja_confianza} facturas ({baja_confianza/total_facturas*100:.1f}%)")
            
            print("\n💰 ANÁLISIS FINANCIERO")
            print("-" * 80)
            print(f"Importe total: €{total_importe:,.2f}")
            print(f"Importe promedio: €{promedio_importe:,.2f}")
            print(f"Importe mínimo: €{min_importe:,.2f}")
            print(f"Importe máximo: €{max_importe:,.2f}")
            
            print("\n🏢 PROVEEDORES")
            print("-" * 80)
            print(f"Proveedores únicos: {proveedores_unicos}")
            if top_proveedores:
                print("\n   Top 10 proveedores por importe:")
                for i, prov in enumerate(top_proveedores, 1):
                    print(f"   {i}. {prov['proveedor']}: {prov['count']} facturas, €{prov['total']:,.2f}")
            
            print("\n📋 ÚLTIMAS 10 FACTURAS PROCESADAS")
            print("-" * 80)
            for i, fact in enumerate(ultimas, 1):
                fecha_str = fact['fecha'].strftime('%Y-%m-%d %H:%M') if fact['fecha'] else 'N/A'
                importe_str = f"€{fact['importe']:.2f}" if fact['importe'] else 'N/A'
                print(f"{i}. {fact['proveedor'] or 'N/A'}")
                print(f"   💰 {importe_str} | 🎚️  {fact['confianza']} | 🤖 {fact['extractor']} | 📊 {fact['estado']}")
                print(f"   📅 {fecha_str}")
            
            print("\n" + "=" * 80)
            print("✅ RESUMEN EJECUTIVO")
            print("=" * 80)
            print(f"✅ Total facturas procesadas: {total_facturas}")
            print(f"✅ Tasa de éxito OpenAI: {(openai_count/total_facturas*100):.1f}%")
            print(f"✅ Confianza alta: {(alta_confianza/total_facturas*100):.1f}%")
            print(f"✅ Importe total procesado: €{total_importe:,.2f}")
            print(f"✅ Proveedores únicos identificados: {proveedores_unicos}")
            
            if revisar > 0:
                print(f"\n⚠️  {revisar} facturas requieren revisión manual")
            if duplicados > 0:
                print(f"ℹ️  {duplicados} duplicados detectados y gestionados automáticamente")
            
            print("\n" + "=" * 80)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

