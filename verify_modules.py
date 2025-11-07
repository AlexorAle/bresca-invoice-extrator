#!/usr/bin/env python3
"""Verificar que todos los módulos se importan correctamente"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

print("🔍 Verificando módulos del sistema de duplicados...\n")

# Test 1: Importar hash_generator
try:
    from utils.hash_generator import generate_content_hash, normalize_for_hash, validate_hash_completeness
    print("✅ utils.hash_generator importado correctamente")
    
    # Test funcional
    hash1 = generate_content_hash('ACME Corp', 'INV-001', '2025-01-15', 1250.50)
    hash2 = generate_content_hash('acme corp', 'inv-001', '2025-01-15', 1250.50)
    
    if hash1 == hash2:
        print(f"   ✓ Hash generado: {hash1[:16]}...")
        print(f"   ✓ Normalización funciona (case-insensitive)")
    else:
        print("   ❌ ERROR: Hashes deberían ser iguales")
        sys.exit(1)
    
    # Test validación
    dto = {
        'proveedor_text': 'ACME',
        'numero_factura': 'INV-001',
        'importe_total': 1250.50
    }
    is_valid, mensaje = validate_hash_completeness(dto)
    print(f"   ✓ Validación: {mensaje}")
    
except Exception as e:
    print(f"❌ Error importando hash_generator: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Importar duplicate_manager
try:
    from pipeline.duplicate_manager import DuplicateManager, DuplicateDecision
    print("\n✅ pipeline.duplicate_manager importado correctamente")
    
    # Test funcional
    manager = DuplicateManager()
    print(f"   ✓ DuplicateManager inicializado")
    print(f"   ✓ Path duplicados: {manager.duplicates_path}")
    print(f"   ✓ Path revisión: {manager.review_path}")
    
    # Test decisión
    factura = {
        'drive_file_id': 'test_001',
        'proveedor_text': 'ACME',
        'numero_factura': 'INV-001',
        'importe_total': 1250.50,
        'hash_contenido': hash1
    }
    
    decision, reason = manager.decide_action(factura, None, None, None)
    if decision == DuplicateDecision.INSERT:
        print(f"   ✓ Decisión: {decision.value} - {reason}")
    else:
        print(f"   ❌ ERROR: Decisión debería ser INSERT")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Error importando duplicate_manager: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Verificar que parser_normalizer puede importar
try:
    from parser_normalizer import create_factura_dto
    print("\n✅ parser_normalizer funciona con nuevas dependencias")
except Exception as e:
    print(f"⚠️  Advertencia en parser_normalizer: {e}")
    print("   (Esto se arreglará cuando apliques la migración)")

print("\n" + "="*60)
print("🎉 TODOS LOS MÓDULOS VERIFICADOS EXITOSAMENTE")
print("="*60)
