# 🚀 Instalación Sistema de Detección de Duplicados

## ✅ Archivos Creados

Los siguientes archivos han sido creados exitosamente:

```
✓ migrations/001_add_duplicate_detection.sql
✓ migrations/apply_migration.py
✓ apply_migration.sh (script bash simplificado)
✓ src/utils/__init__.py
✓ src/utils/hash_generator.py
✓ src/pipeline/duplicate_manager.py
```

## 📋 Paso 1: Aplicar Migración SQL

Ejecuta el siguiente comando (se te pedirá tu contraseña de sudo):

```bash
./apply_migration.sh
```

**Alternativamente**, si prefieres ejecutarlo manualmente:

```bash
sudo -u postgres psql -d negocio_db -f migrations/001_add_duplicate_detection.sql
```

## 🧪 Paso 2: Verificar Instalación

```bash
# Activar entorno virtual
source venv/bin/activate

# Verificar que los módulos se importan correctamente
python3 << 'EOFPY'
from src.utils.hash_generator import generate_content_hash
from src.pipeline.duplicate_manager import DuplicateManager

# Test rápido
hash1 = generate_content_hash('ACME Corp', 'INV-001', '2025-01-15', 1250.50)
print(f"✓ Hash generado: {hash1[:16]}...")

manager = DuplicateManager()
print(f"✓ DuplicateManager inicializado")
print(f"✓ Directorios: {manager.duplicates_path}")

print("\n✅ Sistema de duplicados instalado correctamente!")
EOFPY
```

## 📊 Paso 3: Verificar Base de Datos

```bash
PGPASSWORD='Dagoba50dago-' psql -h localhost -U extractor_user -d negocio_db << 'EOFSQL'
-- Verificar nuevas columnas
\d facturas

-- Verificar índices
\di idx_facturas_hash_contenido_unique

-- Verificar vista
\dv v_duplicate_analysis

-- Verificar función
\df get_last_ingest_timestamp

SELECT '✅ Base de datos configurada correctamente' as status;
EOFSQL
```

## 🎯 Paso 4: Probar con Facturas Reales

```bash
# Activar entorno virtual
source venv/bin/activate

# Procesar facturas (ahora con detección automática)
python3 src/main.py --months=octubre --dry-run

# Ver logs
tail -f logs/extractor.log | grep -i "duplicate"
```

## 📁 Estructura Creada

```
data/
└── quarantine/
    ├── duplicates/     # Facturas duplicadas
    └── review/         # Facturas para revisión manual
```

## ⚠️ Troubleshooting

### Error: "module 'src' not found"
```bash
# Activar entorno virtual
source venv/bin/activate

# Añadir directorio al PYTHONPATH
export PYTHONPATH=/home/alex/proyectos/invoice-extractor:$PYTHONPATH
```

### Error: "permission denied"
```bash
# Asegurarse de que el script es ejecutable
chmod +x apply_migration.sh
```

### Error en migración: "must be owner of table"
```bash
# Ejecutar con permisos de postgres
sudo -u postgres psql -d negocio_db -f migrations/001_add_duplicate_detection.sql
```

## 📚 Documentación

- **Documentación completa**: Ver `QUICKSTART_DUPLICATE_DETECTION.md`
- **Migración SQL**: `migrations/001_add_duplicate_detection.sql`
- **Código fuente**:
  - Hash generator: `src/utils/hash_generator.py`
  - Duplicate manager: `src/pipeline/duplicate_manager.py`

## ✅ Checklist de Instalación

- [ ] Migración SQL aplicada sin errores
- [ ] Módulos de Python se importan correctamente
- [ ] Base de datos tiene nuevas columnas e índices
- [ ] Directorios de cuarentena creados
- [ ] Sistema listo para usar

---

**¡Instalación completada!** 🎉
