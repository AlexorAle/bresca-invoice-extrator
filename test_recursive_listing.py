#!/usr/bin/env python3

"""
Script de prueba para verificar el nuevo método list_all_pdfs_recursive
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.security.secrets import load_env, validate_secrets
from src.drive_client import DriveClient

load_env()
validate_secrets()

print("🧪 PRUEBA: list_all_pdfs_recursive")
print("=" * 60)

try:
    drive_client = DriveClient()
    print("✅ Cliente de Google Drive inicializado")

    import os
    base_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    print(f"\n📁 Folder ID Base: {base_folder_id}")

    if not base_folder_id:
        print("❌ GOOGLE_DRIVE_FOLDER_ID no configurado")
        sys.exit(1)

    # Probar el nuevo método
    print("\n🔍 Buscando TODOS los PDFs recursivamente...")
    all_pdfs = drive_client.list_all_pdfs_recursive(base_folder_id)

    print(f"\n📊 RESULTADOS:")
    print(f"Total PDFs encontrados: {len(all_pdfs)}")

    if all_pdfs:
        print("\n📋 Lista de archivos encontrados:")
        for i, pdf in enumerate(all_pdfs[:20], 1):  # Mostrar primeros 20
            name = pdf.get('name', 'Unknown')
            folder = pdf.get('folder_name', 'unknown')
            size = pdf.get('size', 'N/A')
            print(f"  {i}. {name}")
            print(f"     📁 Carpeta: {folder}")
            print(f"     📦 Tamaño: {size} bytes")
            print()

        if len(all_pdfs) > 20:
            print(f"  ... y {len(all_pdfs) - 20} archivos más")

        # Agrupar por carpeta
        print("\n📊 Distribución por carpeta:")
        folders = {}
        for pdf in all_pdfs:
            folder = pdf.get('folder_name', 'unknown')
            folders[folder] = folders.get(folder, 0) + 1

        for folder, count in sorted(folders.items()):
            print(f"  📁 {folder}: {count} archivos")

        print("\n✅ ¡MÉTODO FUNCIONANDO CORRECTAMENTE!")
    else:
        print("\n⚠️  No se encontraron PDFs")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Prueba completada")

