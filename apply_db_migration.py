#!/usr/bin/env python3

"""
Script para aplicar migración de base de datos
Ejecutar con permisos de administrador si es necesario
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.db.database import get_database
from sqlalchemy import text, inspect

load_dotenv()

print("🔄 Aplicando migración de base de datos...")
print("=" * 60)

try:
    db = get_database()
    
    with db.get_session() as session:
        # Verificar si existe la columna
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('facturas')]
        
        if 'drive_modified_time' in columns:
            print("✅ Columna drive_modified_time ya existe")
        else:
            print("❌ Columna drive_modified_time NO existe")
            print("⚠️  Intentando agregar...")
            print("   (Si falla, ejecutar manualmente con permisos de administrador)")
            
            try:
                session.execute(text("ALTER TABLE facturas ADD COLUMN drive_modified_time TIMESTAMP"))
                session.commit()
                print("✅ Columna drive_modified_time agregada exitosamente")
            except Exception as e:
                print(f"❌ Error: {e}")
                print("\n💡 SOLUCIÓN MANUAL:")
                print("   Ejecutar como administrador de PostgreSQL:")
                print("   sudo -u postgres psql -d negocio_db -c \"ALTER TABLE facturas ADD COLUMN drive_modified_time TIMESTAMP;\"")
                print("   sudo -u postgres psql -d negocio_db -c \"CREATE INDEX idx_facturas_drive_modified ON facturas (drive_modified_time);\"")
                sys.exit(1)
        
        # Verificar/crar índice
        indexes = [idx['name'] for idx in inspector.get_indexes('facturas')]
        if 'idx_facturas_drive_modified' in indexes:
            print("✅ Índice idx_facturas_drive_modified ya existe")
        else:
            try:
                session.execute(text("CREATE INDEX idx_facturas_drive_modified ON facturas (drive_modified_time)"))
                session.commit()
                print("✅ Índice idx_facturas_drive_modified creado")
            except Exception as e:
                print(f"⚠️  Índice no creado: {e} (puede continuar)")
    
    print("\n✅ Migración completada")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

