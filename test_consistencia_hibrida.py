#!/usr/bin/env python3
"""
Prueba de consistencia - 10 lecturas de la misma factura
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from security.secrets import load_env
from ocr_extractor import InvoiceExtractor
from logging_conf import get_logger

load_env()
logger = get_logger(__name__)

def test_consistencia():
    """Probar extracción 10 veces y verificar consistencia"""
    
    pdf_path = Path(__file__).parent / 'temp' / 'Iberdrola Junio 2025.pdf'
    
    if not pdf_path.exists():
        print(f"❌ Error: Archivo no encontrado: {pdf_path}")
        return
    
    print("\n" + "="*70)
    print("🧪 PRUEBA DE CONSISTENCIA - ARQUITECTURA HÍBRIDA MEJORADA")
    print("="*70)
    print(f"Archivo: {pdf_path.name}")
    print(f"Iteraciones: 10")
    print(f"Inicio: {datetime.now().strftime('%H:%M:%S')}\n")
    
    extractor = InvoiceExtractor()
    
    resultados = []
    importes = []
    extractores = []
    confianzas = []
    
    for i in range(1, 11):
        print(f"📋 Lectura {i}/10...", end=' ', flush=True)
        
        inicio = datetime.now()
        result = extractor.extract_invoice_data(str(pdf_path))
        duracion = (datetime.now() - inicio).total_seconds()
        
        importe = result.get('importe_total')
        extractor_num = result.get('extractor_numeros')
        confianza = result.get('confianza')
        
        importes.append(importe)
        extractores.append(extractor_num)
        confianzas.append(confianza)
        
        resultados.append({
            'iteracion': i,
            'importe_total': importe,
            'base_imponible': result.get('base_imponible'),
            'impuestos_total': result.get('impuestos_total'),
            'iva_porcentaje': result.get('iva_porcentaje'),
            'proveedor_text': result.get('proveedor_text'),
            'numero_factura': result.get('numero_factura'),
            'fecha_emision': result.get('fecha_emision'),
            'confianza': confianza,
            'extractor_numeros': extractor_num,
            'extractor_texto': result.get('extractor_texto'),
            'duracion_segundos': round(duracion, 2)
        })
        
        print(f"✓ €{importe if importe else 'None'} ({duracion:.1f}s)")
    
    # Análisis de resultados
    print("\n" + "="*70)
    print("📊 ANÁLISIS DE CONSISTENCIA")
    print("="*70)
    
    # Importes únicos
    importes_unicos = list(set([str(i) for i in importes]))
    contador_importes = Counter([str(i) for i in importes])
    
    print(f"\n🔢 IMPORTES EXTRAÍDOS:")
    for importe_str, count in contador_importes.most_common():
        porcentaje = (count / 10) * 100
        print(f"   €{importe_str}: {count}/10 veces ({porcentaje:.0f}%)")
    
    # Consistencia
    if len(importes_unicos) == 1:
        print(f"\n✅ CONSISTENCIA: 100% - Todas las lecturas dieron el mismo importe")
    else:
        print(f"\n⚠️  INCONSISTENCIA: {len(importes_unicos)} valores diferentes detectados")
    
    # Extractores usados
    contador_extractores = Counter(extractores)
    print(f"\n⚙️  EXTRACTORES USADOS:")
    for ext, count in contador_extractores.most_common():
        porcentaje = (count / 10) * 100
        print(f"   {ext}: {count}/10 veces ({porcentaje:.0f}%)")
    
    # Confianza
    contador_confianza = Counter(confianzas)
    print(f"\n📈 NIVEL DE CONFIANZA:")
    for conf, count in contador_confianza.most_common():
        porcentaje = (count / 10) * 100
        print(f"   {conf}: {count}/10 veces ({porcentaje:.0f}%)")
    
    # Estadísticas de tiempo
    duraciones = [r['duracion_segundos'] for r in resultados]
    print(f"\n⏱️  TIEMPO DE PROCESAMIENTO:")
    print(f"   Promedio: {sum(duraciones)/len(duraciones):.1f}s")
    print(f"   Mínimo:   {min(duraciones):.1f}s")
    print(f"   Máximo:   {max(duraciones):.1f}s")
    
    # Otros campos
    print(f"\n📝 OTROS CAMPOS:")
    proveedores = [r['proveedor_text'] for r in resultados]
    facturas = [r['numero_factura'] for r in resultados]
    fechas = [r['fecha_emision'] for r in resultados]
    
    print(f"   Proveedor:    {len(set(proveedores))} valor(es) único(s)")
    print(f"   Nº Factura:   {len(set(facturas))} valor(es) único(s)")
    print(f"   Fecha:        {len(set(fechas))} valor(es) único(s)")
    
    # Guardar resultados
    output_file = Path(__file__).parent / f"consistencia_hibrida_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'resumen': {
                'total_iteraciones': 10,
                'importes_unicos': len(importes_unicos),
                'consistencia_porcentaje': (contador_importes.most_common(1)[0][1] / 10) * 100,
                'importe_mas_comun': contador_importes.most_common(1)[0][0],
                'duracion_promedio': round(sum(duraciones)/len(duraciones), 2)
            },
            'detalle': resultados
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Resultados guardados en: {output_file.name}")
    
    # Conclusión
    print("\n" + "="*70)
    print("🎯 CONCLUSIÓN")
    print("="*70)
    
    if len(importes_unicos) == 1:
        print(f"✅ Sistema CONSISTENTE: Todas las lecturas dieron €{importes[0]}")
        print(f"✅ Extractor principal: {contador_extractores.most_common(1)[0][0]}")
        print(f"✅ Confianza predominante: {contador_confianza.most_common(1)[0][0]}")
        print(f"✅ Tiempo promedio: {sum(duraciones)/len(duraciones):.1f}s por factura")
    else:
        print(f"⚠️  Sistema INCONSISTENTE: Detectados {len(importes_unicos)} valores diferentes")
        print(f"⚠️  Valor más común: €{contador_importes.most_common(1)[0][0]} ({contador_importes.most_common(1)[0][1]}/10 veces)")
    
    print("="*70 + "\n")

if __name__ == '__main__':
    test_consistencia()


