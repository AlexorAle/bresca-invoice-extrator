#!/usr/bin/env python3
"""
Script para dry-run con búsqueda recursiva
"""
import sys
import os
from pathlib import Path
from collections import defaultdict

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env
from src.drive_client import DriveClient

load_env()

def main():
    """Ejecutar dry-run recursivo"""
    
    print("="*70)
    print("🔍 DRY-RUN: BÚSQUEDA RECURSIVA EN TODAS LAS SUBCARPETAS")
    print("="*70)
    print()
    
    # Configuración
    base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    if not base_folder_id:
        print("❌ ERROR: GOOGLE_DRIVE_FOLDER_ID no configurado")
        return 1
    
    print(f"📁 Carpeta base configurada: {base_folder_id}")
    print()
    
    # Inicializar cliente Drive
    print("📡 Conectando a Google Drive...")
    try:
        drive_client = DriveClient()
        print("✅ Conectado correctamente")
        print()
    except Exception as e:
        print(f"❌ Error conectando a Drive: {e}")
        return 1
    
    # Listar todos los PDFs recursivamente
    print("🔍 Buscando TODOS los PDFs recursivamente en todas las subcarpetas...")
    print("   (Esto puede tomar unos minutos si hay muchas carpetas)")
    print()
    
    try:
        all_files = drive_client.list_all_pdfs_recursive(base_folder_id)
        
        total = len(all_files)
        print(f"📊 TOTAL DE ARCHIVOS ENCONTRADOS: {total}")
        print()
        
        if total == 0:
            print("⚠️  No se encontraron archivos PDF")
            return 0
        
        # Agrupar por carpeta
        by_folder = defaultdict(list)
        for file_info in all_files:
            folder = file_info.get('folder_name', 'unknown')
            by_folder[folder].append(file_info)
        
        print("📁 DISTRIBUCIÓN POR CARPETA:")
        print()
        for folder, files in sorted(by_folder.items()):
            print(f"   {folder}: {len(files)} archivos")
        print()
        
        # Mostrar primeros archivos
        print("📋 PRIMEROS 20 ARCHIVOS ENCONTRADOS:")
        print()
        for i, file_info in enumerate(all_files[:20], 1):
            name = file_info.get('name', 'Unknown')
            folder = file_info.get('folder_name', 'unknown')
            print(f"   {i:3}. {name[:60]:60} (carpeta: {folder})")
        
        if total > 20:
            print(f"   ... y {total - 20} archivos más")
        
        print()
        print("="*70)
        print(f"✅ DRY-RUN COMPLETADO: {total} archivos detectados")
        print("="*70)
        
        # Verificar carpetas 2024 y 2025
        folders_2024 = [f for f in by_folder.keys() if '2024' in f.lower()]
        folders_2025 = [f for f in by_folder.keys() if '2025' in f.lower()]
        
        if folders_2024 or folders_2025:
            print()
            print("✅ CARPETAS 2024 Y 2025 DETECTADAS:")
            if folders_2024:
                for f in folders_2024:
                    print(f"   - {f}: {len(by_folder[f])} archivos")
            if folders_2025:
                for f in folders_2025:
                    print(f"   - {f}: {len(by_folder[f])} archivos")
        
        # Resumen por año
        print()
        print("📊 RESUMEN POR AÑO:")
        total_2024 = sum(len(by_folder[f]) for f in by_folder.keys() if '2024' in f.lower())
        total_2025 = sum(len(by_folder[f]) for f in by_folder.keys() if '2025' in f.lower())
        print(f"   Facturas 2024: {total_2024} archivos")
        print(f"   Facturas 2025: {total_2025} archivos")
        print(f"   Total: {total} archivos")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error listando archivos: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

