#!/usr/bin/env python3
"""
Script de Control de Calidad de Facturas
Compara facturas en Google Drive con la base de datos y genera un informe detallado
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.drive_client import DriveClient
from src.db.database import Database
from src.db.models import Factura

load_env()

def normalize_filename(filename):
    """Normalizar nombre de archivo para comparación (sin espacios extras, lowercase)"""
    if not filename:
        return ""
    # Convertir a lowercase, eliminar espacios extras
    normalized = filename.lower().strip()
    # Eliminar extensiones comunes
    for ext in ['.pdf', '.meta.json']:
        if normalized.endswith(ext):
            normalized = normalized[:-len(ext)]
    return normalized.strip()

def get_drive_files(folder_name="Facturas Automatizacion"):
    """Obtener todos los archivos PDF de la carpeta especificada en Google Drive"""
    print(f"\n📁 Obteniendo archivos de Google Drive (carpeta: '{folder_name}')...")
    
    try:
        drive_client = DriveClient()
        base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        if not base_folder_id:
            print("❌ GOOGLE_DRIVE_FOLDER_ID no configurado")
            return None
        
        # Buscar la carpeta "Facturas Automatizacion"
        folder_id = drive_client.get_folder_id_by_name(folder_name, parent_id=base_folder_id)
        
        if not folder_id:
            print(f"⚠️  Carpeta '{folder_name}' no encontrada. Buscando en carpeta base...")
            folder_id = base_folder_id
        
        # Listar todos los PDFs recursivamente
        all_pdfs = drive_client.list_all_pdfs_recursive(folder_id)
        
        print(f"✅ Encontrados {len(all_pdfs)} archivos PDF en Drive")
        
        # Crear diccionario con nombre normalizado como clave
        drive_files = {}
        for pdf in all_pdfs:
            name = pdf.get('name', '')
            normalized = normalize_filename(name)
            if normalized:
                drive_files[normalized] = {
                    'name': name,
                    'id': pdf.get('id'),
                    'folder': pdf.get('folder_name', 'unknown'),
                    'modified': pdf.get('modifiedTime'),
                    'size': pdf.get('size')
                }
        
        return drive_files
        
    except Exception as e:
        print(f"❌ Error obteniendo archivos de Drive: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_db_facturas():
    """Obtener todas las facturas de la base de datos agrupadas por estado"""
    print("\n💾 Obteniendo facturas de la base de datos...")
    
    try:
        db = Database()
        
        with db.get_session() as session:
            # Obtener todas las facturas
            facturas = session.query(Factura).all()
            
            # Agrupar por estado
            facturas_by_state = {
                'procesado': [],
                'revisar': [],
                'error': [],
                'duplicado': [],
                'error_permanente': [],
                'pendiente': [],
                'otros': []
            }
            
            db_facturas = {}
            
            for factura in facturas:
                name = factura.drive_file_name or ''
                normalized = normalize_filename(name)
                
                if normalized:
                    estado = factura.estado or 'otros'
                    if estado not in facturas_by_state:
                        estado = 'otros'
                    
                    factura_info = {
                        'id': factura.id,
                        'name': name,
                        'estado': estado,
                        'proveedor': factura.proveedor_text,
                        'fecha_emision': factura.fecha_emision.isoformat() if factura.fecha_emision else None,
                        'importe_total': float(factura.importe_total) if factura.importe_total else None,
                        'error_msg': factura.error_msg,
                        'drive_file_id': factura.drive_file_id,
                        'folder': factura.drive_folder_name
                    }
                    
                    # Si ya existe una factura con el mismo nombre, agregar a lista de duplicados
                    if normalized in db_facturas:
                        if 'duplicados' not in db_facturas[normalized]:
                            db_facturas[normalized]['duplicados'] = []
                        db_facturas[normalized]['duplicados'].append(factura_info)
                    else:
                        factura_info['duplicados'] = []
                        db_facturas[normalized] = factura_info
                    
                    facturas_by_state[estado].append(factura_info)
            
            print(f"✅ Total facturas en BD: {len(facturas)}")
            print(f"   - Procesadas: {len(facturas_by_state['procesado'])}")
            print(f"   - Por revisar: {len(facturas_by_state['revisar'])}")
            print(f"   - Error: {len(facturas_by_state['error'])}")
            print(f"   - Duplicado: {len(facturas_by_state['duplicado'])}")
            print(f"   - Error permanente: {len(facturas_by_state['error_permanente'])}")
            print(f"   - Pendiente: {len(facturas_by_state['pendiente'])}")
            print(f"   - Otros: {len(facturas_by_state['otros'])}")
            
            return db_facturas, facturas_by_state
            
    except Exception as e:
        print(f"❌ Error obteniendo facturas de BD: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def get_quarantine_files():
    """Obtener archivos en cuarentena"""
    print("\n🚨 Obteniendo archivos en cuarentena...")
    
    try:
        quarantine_path = Path(os.getenv('QUARANTINE_PATH', 'data/quarantine'))
        
        if not quarantine_path.exists():
            print(f"⚠️  Ruta de cuarentena no existe: {quarantine_path}")
            return {}
        
        quarantine_files = {}
        meta_files = list(quarantine_path.rglob('*.meta.json'))
        
        for meta_file in meta_files:
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                
                name = (
                    meta_data.get('drive_file_name') or 
                    meta_data.get('file_info', {}).get('name') or 
                    meta_file.stem.replace('.meta', '')
                )
                
                normalized = normalize_filename(name)
                if normalized:
                    quarantine_files[normalized] = {
                        'name': name,
                        'reason': meta_data.get('reason') or meta_data.get('error'),
                        'decision': meta_data.get('decision'),
                        'quarantined_at': meta_data.get('quarantined_at'),
                        'meta_file': str(meta_file.relative_to(quarantine_path))
                    }
            except Exception as e:
                print(f"⚠️  Error leyendo {meta_file}: {e}")
                continue
        
        print(f"✅ Archivos en cuarentena: {len(quarantine_files)}")
        return quarantine_files
        
    except Exception as e:
        print(f"❌ Error obteniendo archivos de cuarentena: {e}")
        import traceback
        traceback.print_exc()
        return {}

def generate_report(drive_files, db_facturas, facturas_by_state, quarantine_files):
    """Generar informe detallado de control de calidad"""
    
    print("\n" + "="*80)
    print("📊 INFORME DE CONTROL DE CALIDAD")
    print("="*80)
    
    # Estadísticas generales
    print("\n📈 ESTADÍSTICAS GENERALES")
    print("-" * 80)
    print(f"Total archivos PDF en Google Drive: {len(drive_files)}")
    print(f"Total facturas en BD: {len(db_facturas)}")
    print(f"Total archivos en cuarentena: {len(quarantine_files)}")
    
    # Desglose por estado
    print("\n📋 DESGLOSE POR ESTADO (BD)")
    print("-" * 80)
    for estado, facturas in facturas_by_state.items():
        if facturas:
            print(f"  {estado.upper()}: {len(facturas)}")
    
    # Comparación nombre por nombre
    print("\n🔍 COMPARACIÓN NOMBRE POR NOMBRE")
    print("-" * 80)
    
    # Archivos en Drive que NO están en BD
    drive_only = set(drive_files.keys()) - set(db_facturas.keys())
    print(f"\n📥 Archivos en Drive que NO están en BD: {len(drive_only)}")
    if drive_only:
        print("   (Primeros 20)")
        for i, normalized in enumerate(sorted(drive_only)[:20]):
            file_info = drive_files[normalized]
            print(f"   {i+1}. {file_info['name']} (carpeta: {file_info['folder']})")
        if len(drive_only) > 20:
            print(f"   ... y {len(drive_only) - 20} más")
    
    # Facturas en BD que NO están en Drive
    db_only = set(db_facturas.keys()) - set(drive_files.keys())
    print(f"\n💾 Facturas en BD que NO están en Drive: {len(db_only)}")
    if db_only:
        print("   (Primeros 20)")
        for i, normalized in enumerate(sorted(db_only)[:20]):
            factura = db_facturas[normalized]
            print(f"   {i+1}. {factura['name']} (estado: {factura['estado']}, carpeta: {factura['folder']})")
        if len(db_only) > 20:
            print(f"   ... y {len(db_only) - 20} más")
    
    # Archivos coincidentes
    matching = set(drive_files.keys()) & set(db_facturas.keys())
    print(f"\n✅ Archivos coincidentes (Drive ↔ BD): {len(matching)}")
    
    # Archivos en cuarentena que NO están en BD
    quarantine_only = set(quarantine_files.keys()) - set(db_facturas.keys())
    print(f"\n🚨 Archivos en cuarentena que NO están en BD: {len(quarantine_only)}")
    if quarantine_only:
        print("   (Primeros 20)")
        for i, normalized in enumerate(sorted(quarantine_only)[:20]):
            q_file = quarantine_files[normalized]
            print(f"   {i+1}. {q_file['name']} (razón: {q_file.get('reason', 'N/A')[:50]})")
        if len(quarantine_only) > 20:
            print(f"   ... y {len(quarantine_only) - 20} más")
    
    # Facturas duplicadas en BD
    print(f"\n🔄 Facturas duplicadas en BD: {sum(1 for f in db_facturas.values() if f.get('duplicados'))}")
    duplicated = [f for f in db_facturas.values() if f.get('duplicados')]
    if duplicated:
        print("   (Primeros 10)")
        for i, factura in enumerate(duplicated[:10]):
            print(f"   {i+1}. {factura['name']} ({len(factura['duplicados']) + 1} registros)")
    
    # Verificación de suma total
    print("\n🧮 VERIFICACIÓN DE SUMA TOTAL")
    print("-" * 80)
    total_esperado = len(drive_files)
    total_bd = len(db_facturas)
    
    # Facturas procesadas correctamente
    procesadas = len(facturas_by_state['procesado'])
    # Facturas con error o por revisar (en BD)
    con_problemas_bd = (
        len(facturas_by_state['revisar']) + 
        len(facturas_by_state['error']) + 
        len(facturas_by_state['error_permanente'])
    )
    
    # Archivos en cuarentena que NO están procesados en BD
    quarantine_not_in_bd = set(quarantine_files.keys()) - set(db_facturas.keys())
    total_cuarentena_no_procesados = len(quarantine_not_in_bd)
    
    print(f"Total archivos en Drive: {total_esperado}")
    print(f"Facturas procesadas correctamente en BD: {procesadas}")
    print(f"Facturas con problemas en BD (revisar/error): {con_problemas_bd}")
    print(f"Archivos en cuarentena (NO procesados): {total_cuarentena_no_procesados}")
    print(f"\nSuma (procesadas + problemas BD + cuarentena no procesados): {procesadas + con_problemas_bd + total_cuarentena_no_procesados}")
    print(f"Diferencia con Drive: {total_esperado - (procesadas + con_problemas_bd + total_cuarentena_no_procesados)}")
    
    if total_esperado == (procesadas + con_problemas_bd + total_cuarentena_no_procesados):
        print("✅ ¡La suma coincide perfectamente!")
    else:
        diferencia = total_esperado - (procesadas + con_problemas_bd + total_cuarentena_no_procesados)
        if diferencia > 0:
            print(f"⚠️  Faltan {diferencia} archivos por procesar o clasificar")
        else:
            print(f"⚠️  Hay {abs(diferencia)} archivos de más en BD o cuarentena")
    
    # Guardar informe detallado en archivo
    report_file = Path(f"control_calidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'estadisticas': {
            'total_drive': len(drive_files),
            'total_bd': len(db_facturas),
            'total_cuarentena': len(quarantine_files),
            'cuarentena_no_procesados': total_cuarentena_no_procesados,
            'procesadas': procesadas,
            'con_problemas_bd': con_problemas_bd
        },
        'drive_only': [drive_files[n]['name'] for n in sorted(drive_only)],
        'db_only': [db_facturas[n]['name'] for n in sorted(db_only)],
        'matching': len(matching),
        'quarantine_only': [quarantine_files[n]['name'] for n in sorted(quarantine_only)],
        'duplicados': [
            {
                'name': f['name'],
                'count': len(f.get('duplicados', [])) + 1
            }
            for f in db_facturas.values() if f.get('duplicados')
        ]
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Informe detallado guardado en: {report_file}")
    
    return report_data

def main():
    print("="*80)
    print("🔍 CONTROL DE CALIDAD DE FACTURAS")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Obtener archivos de Drive
    drive_files = get_drive_files()
    if drive_files is None:
        print("❌ No se pudieron obtener archivos de Drive")
        return 1
    
    # Obtener facturas de BD
    db_facturas, facturas_by_state = get_db_facturas()
    if db_facturas is None:
        print("❌ No se pudieron obtener facturas de BD")
        return 1
    
    # Obtener archivos en cuarentena
    quarantine_files = get_quarantine_files()
    
    # Generar informe
    report = generate_report(drive_files, db_facturas, facturas_by_state, quarantine_files)
    
    print("\n" + "="*80)
    print("✅ Control de calidad completado")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

