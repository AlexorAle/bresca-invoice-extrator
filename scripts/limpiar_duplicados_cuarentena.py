#!/usr/bin/env python3
"""
Script para limpiar duplicados en cuarentena
Elimina archivos duplicados dejando solo UN registro por factura
"""
import sys
import os
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env

load_env()

def main():
    quarantine_path = Path(os.getenv('QUARANTINE_PATH', 'data/quarantine'))
    duplicates_by_name = defaultdict(list)
    
    print("="*70)
    print("🧹 LIMPIEZA DE DUPLICADOS EN CUARENTENA")
    print("="*70)
    print(f"\n📂 Ruta de cuarentena: {quarantine_path}")
    
    if not quarantine_path.exists():
        print(f"❌ La ruta de cuarentena no existe: {quarantine_path}")
        return
    
    # Paso 1: Analizar todos los archivos
    print("\n🔍 Paso 1: Analizando archivos en cuarentena...")
    total_files = 0
    
    for meta_file in quarantine_path.rglob("*.meta.json"):
        total_files += 1
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            file_info = meta_data.get('file_info', {})
            nombre = (
                meta_data.get('drive_file_name') or 
                file_info.get('name') or 
                meta_file.stem.replace('.meta', '').split('_', 2)[-1] if '_' in meta_file.stem else meta_file.stem.replace('.meta', '')
            )
            
            if nombre and nombre != 'unknown':
                # Buscar el PDF correspondiente
                pdf_file = meta_file.with_suffix('.pdf')
                if not pdf_file.exists():
                    # Intentar encontrar el PDF con el mismo nombre base
                    pdf_name = meta_file.stem.replace('.meta', '') + '.pdf'
                    pdf_file = meta_file.parent / pdf_name
                
                # Obtener timestamp para ordenar (más reciente primero)
                quarantined_at = meta_data.get('quarantined_at') or meta_data.get('timestamp')
                timestamp = None
                if quarantined_at:
                    try:
                        if isinstance(quarantined_at, str):
                            timestamp = datetime.fromisoformat(quarantined_at.replace('Z', '+00:00'))
                        else:
                            timestamp = quarantined_at
                    except:
                        pass
                
                # Si no hay timestamp, usar la fecha de modificación del archivo
                if timestamp is None:
                    timestamp = datetime.fromtimestamp(meta_file.stat().st_mtime)
                
                duplicates_by_name[nombre].append({
                    'meta_file': meta_file,
                    'pdf_file': pdf_file if pdf_file.exists() else None,
                    'quarantined_at': quarantined_at,
                    'timestamp': timestamp,
                    'size': meta_file.stat().st_size
                })
        except Exception as e:
            print(f"⚠️  Error procesando {meta_file}: {e}")
            continue
    
    print(f"✅ Analizados {total_files} archivos .meta.json")
    
    # Paso 2: Identificar duplicados
    duplicates_to_clean = {nombre: files for nombre, files in duplicates_by_name.items() if len(files) > 1}
    
    print(f"\n📊 Resumen:")
    print(f"  - Total nombres únicos: {len(duplicates_by_name)}")
    print(f"  - Total archivos: {sum(len(files) for files in duplicates_by_name.values())}")
    print(f"  - Nombres con duplicados: {len(duplicates_to_clean)}")
    
    total_to_delete = sum(len(files) - 1 for files in duplicates_to_clean.values())
    print(f"  - Archivos duplicados a eliminar: {total_to_delete}")
    
    if total_to_delete == 0:
        print("\n✅ No hay duplicados para eliminar")
        return
    
    # Paso 3: Mostrar qué se va a eliminar
    print(f"\n📋 Top 10 duplicados a limpiar:")
    for nombre, files in sorted(duplicates_to_clean.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"  - {nombre}: {len(files)} archivos (eliminar {len(files) - 1})")
    
    # Paso 4: Confirmar y eliminar
    print(f"\n⚠️  Se eliminarán {total_to_delete} archivos duplicados")
    print("   (Se mantendrá el archivo más reciente de cada grupo)")
    
    # Ordenar cada grupo por timestamp (más reciente primero) y mantener solo el primero
    deleted_count = 0
    deleted_files = []
    
    for nombre, files in duplicates_to_clean.items():
        # Ordenar por timestamp (más reciente primero)
        files_sorted = sorted(files, key=lambda x: x['timestamp'], reverse=True)
        
        # Mantener el primero (más reciente), eliminar el resto
        to_keep = files_sorted[0]
        to_delete = files_sorted[1:]
        
        for file_info in to_delete:
            try:
                # Eliminar .meta.json
                if file_info['meta_file'].exists():
                    file_info['meta_file'].unlink()
                    deleted_files.append(str(file_info['meta_file']))
                    deleted_count += 1
                
                # Eliminar .pdf si existe
                if file_info['pdf_file'] and file_info['pdf_file'].exists():
                    file_info['pdf_file'].unlink()
                    deleted_files.append(str(file_info['pdf_file']))
                    deleted_count += 1
                
                print(f"  🗑️  Eliminado: {file_info['meta_file'].name}")
            except Exception as e:
                print(f"  ⚠️  Error eliminando {file_info['meta_file']}: {e}")
    
    print(f"\n✅ Limpieza completada:")
    print(f"  - Archivos eliminados: {deleted_count}")
    print(f"  - Archivos mantenidos: {len(duplicates_by_name)} (uno por cada nombre único)")
    
    # Verificar resultado
    remaining_files = sum(1 for _ in quarantine_path.rglob("*.meta.json"))
    print(f"  - Archivos restantes en cuarentena: {remaining_files}")

if __name__ == "__main__":
    main()

