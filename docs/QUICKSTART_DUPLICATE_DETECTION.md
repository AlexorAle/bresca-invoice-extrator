# ⚡ Quickstart - Sistema de Detección de Duplicados

Guía de **5 minutos** para activar y usar el sistema de prevención de duplicados.

---

## 🚀 Paso 1: Aplicar Migración (2 min)

### ⚠️ IMPORTANTE: Solo falta este paso con sudo

```bash
./apply_migration.sh
```

**Lo que hace:**
- Añade columnas `revision` y `drive_modified_time` a tabla `facturas`
- Actualiza constraint de `estado` para incluir 'duplicado'
- Crea índices de rendimiento
- Añade campos en `ingest_events`
- Crea vista `v_duplicate_analysis`

---

## ✅ Paso 2: Verificar Instalación (1 min)

```bash
# Test rápido
python3 test_duplicate_system.py
```

**Salida esperada: 21/21 tests pasados (100%)**

---

## 📊 Paso 3: Verificar Base de Datos (1 min)

```bash
PGPASSWORD='Dagoba50dago-' psql -h localhost -U extractor_user -d negocio_db << 'EOFSQL'
-- Verificar nuevas columnas
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'facturas' 
AND column_name IN ('hash_contenido', 'revision', 'drive_modified_time');

-- Verificar vista de duplicados
SELECT * FROM v_duplicate_analysis LIMIT 5;
EOFSQL
```

---

## 🎯 Paso 4: Usar en Producción (1 min)

### Procesamiento Normal (detección automática)

```bash
source venv/bin/activate
python3 src/main.py --months=octubre
```

**Nuevo output**:
```
INFO: Iniciando procesamiento batch de 50 archivos con detección de duplicados
INFO: Procesando 1/50: factura_001.pdf
INFO: Decisión de duplicado: insert - Nueva factura

INFO: Procesando 2/50: factura_001_copia.pdf
INFO: Decisión de duplicado: duplicate - Duplicado detectado
INFO: Archivo movido a cuarentena: data/quarantine/duplicates/...

Batch completado: 
  - 45 exitosos
  - 3 duplicados     ← NUEVO
  - 2 para revisión  ← NUEVO
```

---

## 🔍 Consultas Útiles

### Ver duplicados detectados

```sql
SELECT * FROM v_duplicate_analysis;
```

### Ver facturas en cuarentena

```sql
SELECT drive_file_name, estado, error_msg, creado_en
FROM facturas 
WHERE estado IN ('duplicado', 'revisar')
ORDER BY creado_en DESC;
```

### Ver eventos de duplicados

```sql
SELECT ts, drive_file_id, decision, detalle
FROM ingest_events
WHERE etapa = 'duplicate_check'
ORDER BY ts DESC
LIMIT 20;
```

---

## 📁 Archivos en Cuarentena

```bash
# Ver duplicados
ls -lh data/quarantine/duplicates/

# Ver metadata
cat data/quarantine/duplicates/*.meta.json | jq .
```

**Ejemplo de metadata**:
```json
{
  "timestamp": "2025-11-02T14:50:00",
  "decision": "duplicate",
  "reason": "Duplicado detectado: mismo contenido que 'factura_original.pdf'",
  "drive_file_id": "abc123",
  "factura_data": {
    "proveedor_text": "ACME Corporation",
    "numero_factura": "INV-2025-001",
    "hash_contenido": "b2d146dd378f07c8..."
  }
}
```

---

## 🧪 Test Manual Rápido

```python
# test_hash.py
from src.utils.hash_generator import generate_content_hash

# Generar hash
hash1 = generate_content_hash(
    proveedor_text='ACME Corp',
    numero_factura='INV-001',
    fecha_emision='2025-01-15',
    importe_total=1250.50
)

print(f"Hash: {hash1}")

# Mismo contenido, diferente formato
hash2 = generate_content_hash(
    proveedor_text='acme corp',  # minúsculas
    numero_factura='inv-001',
    fecha_emision='2025-01-15',
    importe_total=1250.50
)

print(f"¿Iguales? {hash1 == hash2}")  # True
```

---

## 🔧 Casos de Uso Comunes

### 1. Verificar si una factura es duplicado

```python
from src.db.database import get_database
from src.db.repositories import FacturaRepository
from src.utils.hash_generator import generate_content_hash

db = get_database()
repo = FacturaRepository(db)

hash = generate_content_hash('ACME', 'INV-001', '2025-01-15', 1250.50)
factura = repo.find_by_hash(hash)

if factura:
    print(f"⚠️  DUPLICADO: {factura['drive_file_name']}")
else:
    print("✅ Nueva factura")
```

### 2. Limpiar cuarentena antigua

```python
from src.pipeline.duplicate_manager import DuplicateManager

manager = DuplicateManager()
manager.cleanup_old_quarantine(days=60)
```

### 3. Estadísticas

```python
from src.db.repositories import FacturaRepository
from src.db.database import get_database

repo = FacturaRepository(get_database())
stats = repo.get_statistics()

print(f"Total: {stats['total_facturas']}")
print(f"Duplicados: {stats['por_estado'].get('duplicado', 0)}")
```

---

## 📚 Documentación Completa

- **Instalación**: `INSTALL_DUPLICATE_DETECTION.md`
- **Changelog**: `CHANGELOG_DUPLICATE_DETECTION.md`
- **Tests**: `test_duplicate_system.py`

---

## ✅ Checklist

- [x] Módulos Python creados y verificados (21/21 tests ✓)
- [x] Directorios de cuarentena creados
- [x] Sistema integrado en parser_normalizer
- [x] Tests completos ejecutados
- [ ] **Migración SQL aplicada** ← Solo falta esto (ejecuta `./apply_migration.sh`)

---

**Una vez ejecutes `./apply_migration.sh`, el sistema estará 100% operativo! 🎉**
