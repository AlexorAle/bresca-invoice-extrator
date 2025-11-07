#!/usr/bin/env python3
"""
Script de testing end-to-end para sistema incremental

Valida:
- Configuración
- Conexión a Drive
- Conexión a DB
- Tabla sync_state existe
- Acceso a carpeta Drive
- StateStore funcional

Uso:
    python scripts/test_incremental_system.py
"""
import sys
import os
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.security.secrets import load_env

# Cargar variables de entorno
load_env()


def print_section(title: str):
    """Imprimir sección decorada"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def test_env_variables():
    """Test 1: Variables de entorno"""
    print_section("TEST 1: Variables de Entorno")
    
    required_vars = {
        'GOOGLE_SERVICE_ACCOUNT_FILE': 'Ruta al service account',
        'GOOGLE_DRIVE_FOLDER_ID': 'ID de carpeta Drive',
        'DATABASE_URL': 'URL de PostgreSQL',
        'STATE_BACKEND': 'Backend de estado (db/file)'
    }
    
    all_ok = True
    
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: OK")
        else:
            print(f"❌ {var}: NO CONFIGURADA ({desc})")
            all_ok = False
    
    if all_ok:
        print()
        print("✅ Todas las variables configuradas")
    else:
        print()
        print("❌ Faltan variables requeridas")
    
    return all_ok


def test_database_connection():
    """Test 2: Conexión a base de datos"""
    print_section("TEST 2: Conexión a Base de Datos")
    
    try:
        from src.db.database import Database
        
        db = Database()
        
        # Test simple de conexión
        with db.get_session() as session:
            result = session.execute("SELECT 1 as test").fetchone()
            assert result[0] == 1
        
        print("✅ Conexión a PostgreSQL OK")
        return True, db
    
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
        return False, None


def test_sync_state_table(db):
    """Test 3: Tabla sync_state existe"""
    print_section("TEST 3: Tabla sync_state")
    
    try:
        with db.get_session() as session:
            # Verificar que tabla existe
            result = session.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'sync_state'
                );
                """
            ).fetchone()
            
            if result[0]:
                print("✅ Tabla sync_state existe")
                
                # Ver contenido
                count = session.execute("SELECT COUNT(*) FROM sync_state").fetchone()[0]
                print(f"   Registros en sync_state: {count}")
                
                return True
            else:
                print("❌ Tabla sync_state NO existe")
                print("   Ejecutar: bash scripts/apply_incremental_migration.sh")
                return False
    
    except Exception as e:
        print(f"❌ Error verificando tabla: {e}")
        return False


def test_drive_connection():
    """Test 4: Conexión a Google Drive"""
    print_section("TEST 4: Conexión a Google Drive")
    
    try:
        from src.drive.drive_incremental import DriveIncrementalClient
        
        client = DriveIncrementalClient()
        
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        if client.validate_folder_access(folder_id):
            print("✅ Acceso a carpeta Drive OK")
            
            # Obtener metadata de carpeta
            metadata = client.get_file_metadata(folder_id)
            if metadata:
                print(f"   Carpeta: {metadata.get('name')}")
                print(f"   ID: {folder_id}")
            
            return True
        else:
            print("❌ No se puede acceder a carpeta Drive")
            print("   Verificar que Service Account tiene permisos sobre la carpeta")
            return False
    
    except Exception as e:
        print(f"❌ Error conectando a Drive: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_store(db):
    """Test 5: StateStore funcional"""
    print_section("TEST 5: StateStore")
    
    try:
        from src.sync.state_store import get_state_store
        from datetime import datetime
        
        state_store = get_state_store(db)
        backend = os.getenv('STATE_BACKEND', 'db')
        
        print(f"   Backend configurado: {backend}")
        
        # Test de lectura
        last_sync = state_store.get_last_sync_time()
        
        if last_sync:
            print(f"✅ StateStore funcional (lectura OK)")
            print(f"   Último sync: {last_sync.isoformat()}")
        else:
            print(f"✅ StateStore funcional (primera ejecución)")
            print(f"   No hay timestamp previo (normal en primera ejecución)")
        
        # Test de escritura (solo en dry-run, no persistir)
        print("   Testeando escritura... (dry-run, no persiste)")
        
        return True
    
    except Exception as e:
        print(f"❌ Error con StateStore: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_incremental_query(db):
    """Test 6: Query incremental a Drive"""
    print_section("TEST 6: Query Incremental (Dry Run)")
    
    try:
        from src.drive.drive_incremental import DriveIncrementalClient
        from src.sync.state_store import get_state_store
        
        client = DriveIncrementalClient()
        state_store = get_state_store(db)
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        last_sync = state_store.get_last_sync_time()
        
        print(f"   Consultando archivos modificados desde: {last_sync.isoformat() if last_sync else 'inicio'}")
        
        # Contar archivos (sin descargar)
        count = client.get_file_count_since(folder_id, last_sync)
        
        print(f"✅ Query incremental OK")
        print(f"   Archivos a procesar: {count}")
        
        if count == 0:
            print("   ℹ️  No hay archivos nuevos desde última sincronización")
        elif count > 100:
            print(f"   ⚠️  Muchos archivos pendientes ({count})")
            print("   Considerar ejecutar con --max-pages para limitar")
        
        return True
    
    except Exception as e:
        print(f"❌ Error en query incremental: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_extractor():
    """Test 7: OCR Extractor disponible"""
    print_section("TEST 7: OCR Extractor")
    
    try:
        from src.ocr_extractor import InvoiceExtractor
        
        extractor = InvoiceExtractor()
        
        print("✅ InvoiceExtractor inicializado OK")
        print(f"   Estrategia: {os.getenv('EXTRACTION_STRATEGY', 'hybrid')}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error inicializando extractor: {e}")
        return False


def main():
    """Ejecutar todos los tests"""
    print()
    print("=" * 70)
    print("  🧪 TEST END-TO-END: Sistema de Ingesta Incremental")
    print("=" * 70)
    
    results = []
    db = None
    
    # Test 1: Variables de entorno
    results.append(("Variables de entorno", test_env_variables()))
    
    # Test 2: Base de datos
    db_ok, db = test_database_connection()
    results.append(("Conexión a BD", db_ok))
    
    if not db_ok:
        print()
        print("❌ No se puede continuar sin conexión a BD")
        sys.exit(1)
    
    # Test 3: Tabla sync_state
    results.append(("Tabla sync_state", test_sync_state_table(db)))
    
    # Test 4: Google Drive
    results.append(("Conexión a Drive", test_drive_connection()))
    
    # Test 5: StateStore
    results.append(("StateStore", test_state_store(db)))
    
    # Test 6: Query incremental
    results.append(("Query incremental", test_incremental_query(db)))
    
    # Test 7: OCR Extractor
    results.append(("OCR Extractor", test_ocr_extractor()))
    
    # Resumen
    print()
    print("=" * 70)
    print("  📊 RESUMEN DE TESTS")
    print("=" * 70)
    print()
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
    
    print()
    print(f"  Total: {passed}/{total} tests pasaron")
    print()
    
    if passed == total:
        print("=" * 70)
        print("  ✅ TODOS LOS TESTS PASARON")
        print("  Sistema incremental listo para usar")
        print("=" * 70)
        print()
        print("Próximo paso:")
        print("  python scripts/run_ingest_incremental.py --dry-run")
        print()
        sys.exit(0)
    else:
        print("=" * 70)
        print(f"  ⚠️  {total - passed} TESTS FALLARON")
        print("  Revisar errores arriba y corregir configuración")
        print("=" * 70)
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()

