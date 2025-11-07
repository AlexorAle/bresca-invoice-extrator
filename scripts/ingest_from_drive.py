#!/usr/bin/env python3
"""
Script para cargar facturas desde Google Drive y generar reporte de lo almacenado
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.drive_client import DriveClient
from src.ocr_extractor import InvoiceExtractor
from src.db.database import Database
from src.pipeline.ingest import process_batch

load_env()

def main():
    """Ejecutar carga completa desde Google Drive"""
    
    print("="*70)
    print("🚀 CARGA COMPLETA DE FACTURAS DESDE GOOGLE DRIVE")
    print("="*70)
    print()
    
    # Configuración
    base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    month_folder_name = 'Julio 2025'
    
    # Inicializar clientes
    print("📡 Conectando a Google Drive...")
    drive_client = DriveClient()
    
    print("🔧 Inicializando extractor OCR...")
    extractor = InvoiceExtractor()
    
    print("💾 Conectando a base de datos...")
    db = Database()
    
    # Buscar carpeta del mes
    print(f"\n🔍 Buscando carpeta '{month_folder_name}'...")
    month_folder_id = drive_client.get_folder_id_by_name(month_folder_name, parent_id=base_folder_id)
    
    if not month_folder_id:
        print(f"❌ Carpeta '{month_folder_name}' no encontrada")
        return
    
    print(f"✅ Carpeta encontrada: {month_folder_id}\n")
    
    # Listar archivos PDF
    print("📋 Listando archivos PDF...")
    pdf_files = drive_client.list_pdf_files(month_folder_id)
    
    # LIMITAR A 10 FACTURAS PARA PRUEBA
    MAX_FACTURAS = 10
    if len(pdf_files) > MAX_FACTURAS:
        print(f"⚠️  Limitando a {MAX_FACTURAS} facturas para prueba (hay {len(pdf_files)} en total)")
        pdf_files = pdf_files[:MAX_FACTURAS]
    
    print(f"✅ Procesando {len(pdf_files)} archivos PDF\n")
    
    if not pdf_files:
        print("⚠️  No hay archivos para procesar")
        return
    
    # Crear directorio temporal
    temp_dir = Path(tempfile.mkdtemp(prefix='invoice_ingest_'))
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
            
            print(f"  [{idx}/{len(pdf_files)}] Descargando: {file_name}...", end=' ')
            
            success = drive_client.download_file(file_id, str(temp_file_path))
            
            if success:
                print("✅")
                # Agregar información adicional para el procesamiento
                file_info['local_path'] = str(temp_file_path)
                file_info['folder_name'] = month_folder_name
                files_to_process.append(file_info)
            else:
                print("❌")
        
        print(f"\n✅ {len(files_to_process)} archivos descargados correctamente\n")
        
        # Procesar batch completo
        print("="*70)
        print("🔄 PROCESANDO FACTURAS...")
        print("="*70)
        print()
        
        stats = process_batch(files_to_process, extractor, db)
        
        # Mostrar estadísticas
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS DE PROCESAMIENTO")
        print("="*70)
        print(f"✅ Exitosos:      {stats.get('exitosos', 0)}")
        print(f"⚠️  Revisar:       {stats.get('revisar', 0)}")
        print(f"🔄 Revisiones:    {stats.get('revisiones', 0)}")
        print(f"📋 Duplicados:    {stats.get('duplicados', 0)}")
        print(f"🚫 Ignorados:     {stats.get('ignorados', 0)}")
        print(f"❌ Errores:       {stats.get('errores', 0)}")
        print(f"⚠️  Validación:    {stats.get('validacion_fallida', 0)}")
        print("="*70)
        
        # Generar reporte de lo almacenado en BD
        print("\n" + "="*70)
        print("📊 CONSULTANDO BASE DE DATOS...")
        print("="*70)
        print()
        
        generate_db_report(db, month_folder_name)
        
    finally:
        # Limpiar directorio temporal
        print(f"\n🧹 Limpiando directorio temporal...")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        print("✅ Limpieza completada")

def generate_db_report(db: Database, folder_name: str):
    """Generar reporte de lo almacenado en la base de datos"""
    
    with db.get_session() as session:
        from src.db.models import Factura
        
        # Consultar facturas del mes
        facturas = session.query(Factura).filter(
            Factura.drive_folder_name == folder_name
        ).order_by(Factura.drive_file_name).all()
        
        print(f"📋 Facturas encontradas en BD para '{folder_name}': {len(facturas)}\n")
        
        if not facturas:
            print("⚠️  No se encontraron facturas en la base de datos")
            return
        
        # Estadísticas generales
        print("="*70)
        print("📈 ESTADÍSTICAS GENERALES")
        print("="*70)
        
        total_importe = sum(float(f.importe_total or 0) for f in facturas if f.importe_total)
        total_base = sum(float(f.base_imponible or 0) for f in facturas if f.base_imponible)
        total_impuestos = sum(float(f.impuestos_total or 0) for f in facturas if f.impuestos_total)
        
        estados = {}
        extractores = {}
        confianza = {}
        
        for f in facturas:
            estados[f.estado] = estados.get(f.estado, 0) + 1
            extractores[f.extractor] = extractores.get(f.extractor, 0) + 1
            if f.confianza:
                confianza[f.confianza] = confianza.get(f.confianza, 0) + 1
        
        print(f"💰 Importe total:       €{total_importe:,.2f}")
        print(f"📊 Base imponible:      €{total_base:,.2f}")
        print(f"💳 Impuestos total:     €{total_impuestos:,.2f}")
        print(f"\n📋 Por estado:")
        for estado, count in sorted(estados.items()):
            print(f"   {estado:15} {count:3} facturas")
        print(f"\n🔧 Por extractor:")
        for ext, count in sorted(extractores.items()):
            print(f"   {ext:20} {count:3} facturas")
        print(f"\n🎯 Por confianza:")
        for conf, count in sorted(confianza.items()):
            print(f"   {conf:15} {count:3} facturas")
        
        # Listar facturas con problemas
        print("\n" + "="*70)
        print("⚠️  FACTURAS CON PROBLEMAS")
        print("="*70)
        
        problemas = [
            f for f in facturas 
            if f.estado in ['error', 'revisar'] or f.confianza == 'baja' or f.importe_total is None
        ]
        
        if problemas:
            print(f"\n⚠️  Encontradas {len(problemas)} facturas con problemas:\n")
            for f in problemas[:20]:  # Mostrar máximo 20
                print(f"  📄 {f.drive_file_name}")
                print(f"     Estado: {f.estado}, Confianza: {f.confianza}, Importe: €{f.importe_total or 'N/A'}")
                if f.error_msg:
                    print(f"     Error: {f.error_msg[:100]}")
                print()
        else:
            print("\n✅ No se encontraron facturas con problemas")
        
        # Tabla resumen
        print("\n" + "="*70)
        print("📋 RESUMEN POR FACTURA (primeras 10)")
        print("="*70)
        print()
        print(f"{'Archivo':<40} {'Proveedor':<25} {'Importe':>12} {'Estado':<12} {'Confianza':<10}")
        print("-"*110)
        
        for f in facturas[:10]:
            proveedor = (f.proveedor_text or 'N/A')[:24]
            importe = f"€{f.importe_total:,.2f}" if f.importe_total else "N/A"
            archivo = f.drive_file_name[:39]
            
            print(f"{archivo:<40} {proveedor:<25} {importe:>12} {f.estado:<12} {f.confianza or 'N/A':<10}")
        
        if len(facturas) > 10:
            print(f"\n... y {len(facturas) - 10} facturas más")
        
        # Verificar integridad
        print("\n" + "="*70)
        print("🔍 VERIFICACIÓN DE INTEGRIDAD")
        print("="*70)
        
        sin_importe = [f for f in facturas if f.importe_total is None]
        sin_proveedor = [f for f in facturas if not f.proveedor_text]
        sin_fecha = [f for f in facturas if not f.fecha_emision]
        
        print(f"📊 Facturas sin importe_total:  {len(sin_importe)}")
        print(f"📊 Facturas sin proveedor:      {len(sin_proveedor)}")
        print(f"📊 Facturas sin fecha_emision:   {len(sin_fecha)}")
        
        if sin_importe:
            print(f"\n⚠️  Archivos sin importe_total:")
            for f in sin_importe[:5]:
                print(f"   - {f.drive_file_name}")

if __name__ == '__main__':
    main()

