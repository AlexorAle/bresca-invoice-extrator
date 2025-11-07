# 📚 Documentación - Invoice Extractor

Bienvenido a la documentación del sistema **Invoice Extractor** con **Sistema de Detección de Duplicados**.

---

## 🆕 Sistema de Detección de Duplicados (Nuevo)

**Estado**: ✅ 95% Implementado | **Tests**: 21/21 ✓

### 📖 Documentación Disponible

| Guía | Descripción | ¿Para qué? |
|------|-------------|------------|
| **[📑 Índice Principal](INDICE_SISTEMA_DUPLICADOS.md)** | Índice completo de toda la documentación | 👉 **Empieza aquí** |
| [🚀 README](README_SISTEMA_DUPLICADOS.md) | Introducción y visión general | Entender qué hace el sistema |
| [⚡ Quickstart](QUICKSTART_DUPLICATE_DETECTION.md) | Guía de 5 minutos | Activar el sistema rápido |
| [📦 Instalación](INSTALL_DUPLICATE_DETECTION.md) | Guía detallada de instalación | Instalar paso a paso |
| [📊 Reporte](REPORTE_IMPLEMENTACION_DUPLICADOS.md) | Reporte ejecutivo completo | Entender la implementación |

### ⚡ Inicio Rápido

```bash
# 1. Aplicar migración (requiere sudo)
./apply_migration.sh

# 2. Verificar instalación
python3 test_duplicate_system.py

# 3. Usar el sistema
source venv/bin/activate
python3 src/main.py --months=octubre
```

### 🎯 ¿Qué hace?

Detecta y previene facturas duplicadas basándose en el **contenido** (no el nombre del archivo):

- 🔐 Hash SHA256 de `proveedor + número + fecha + importe`
- 🎭 5 decisiones inteligentes: INSERT, DUPLICATE, REVIEW, IGNORE, UPDATE_REVISION
- 📁 Cuarentena organizada: `data/quarantine/duplicates/` y `review/`
- 📊 Auditoría completa en BD y logs
- ⚡ Procesamiento incremental

---

## 📖 Documentación Original del Sistema

### Arquitectura y Desarrollo

| Documento | Descripción |
|-----------|-------------|
| [🏗️ arquitectura.md](arquitectura.md) | Arquitectura general del sistema |
| [💻 developer.md](developer.md) | Guía completa para desarrolladores |
| [📡 implementation.md](implementation.md) | Detalles de implementación |
| [🌐 infraestructura.md](infraestructura.md) | Infraestructura y despliegue |

---

## 🗂️ Estructura de Documentación

```
docs/
├── README.md                              ← Este archivo (punto de entrada)
│
├── 🆕 Sistema de Detección de Duplicados
│   ├── INDICE_SISTEMA_DUPLICADOS.md      ← Índice completo
│   ├── README_SISTEMA_DUPLICADOS.md      ← README del sistema
│   ├── QUICKSTART_DUPLICATE_DETECTION.md ← Inicio rápido (5 min)
│   ├── INSTALL_DUPLICATE_DETECTION.md    ← Instalación detallada
│   └── REPORTE_IMPLEMENTACION_DUPLICADOS.md ← Reporte ejecutivo
│
└── 📚 Documentación Original
    ├── arquitectura.md
    ├── developer.md
    ├── implementation.md
    └── infraestructura.md
```

---

## 🚀 ¿Por Dónde Empezar?

### Si eres nuevo:
1. 📑 **[INDICE_SISTEMA_DUPLICADOS.md](INDICE_SISTEMA_DUPLICADOS.md)** - Índice completo
2. 🚀 **[README_SISTEMA_DUPLICADOS.md](README_SISTEMA_DUPLICADOS.md)** - Qué hace el sistema
3. 💻 **[developer.md](developer.md)** - Guía de desarrollo

### Si quieres activar el sistema de duplicados:
1. ⚡ **[QUICKSTART_DUPLICATE_DETECTION.md](QUICKSTART_DUPLICATE_DETECTION.md)** - 5 minutos
2. 📦 **[INSTALL_DUPLICATE_DETECTION.md](INSTALL_DUPLICATE_DETECTION.md)** - Detalles

### Si quieres entender la implementación:
1. 📊 **[REPORTE_IMPLEMENTACION_DUPLICADOS.md](REPORTE_IMPLEMENTACION_DUPLICADOS.md)** - Reporte
2. 📡 **[implementation.md](implementation.md)** - Implementación general

---

## 📊 Estado del Sistema

| Componente | Estado | Tests | Docs |
|------------|--------|-------|------|
| Invoice Extractor | ✅ Producción | ✅ | ✅ |
| OCR Híbrido | ✅ Producción | ✅ | ✅ |
| Sistema Duplicados | ⚠️ 95% | 21/21 ✓ | ✅ |

---

## ⚡ Comandos Útiles

```bash
# Ver documentación
cat docs/README.md                            # Este archivo
cat docs/INDICE_SISTEMA_DUPLICADOS.md        # Índice completo

# Sistema de duplicados
cat docs/QUICKSTART_DUPLICATE_DETECTION.md   # Inicio rápido
./apply_migration.sh                          # Aplicar migración
python3 test_duplicate_system.py              # Tests

# Usar sistema
source venv/bin/activate
python3 src/main.py --months=octubre
```

---

## 📞 Soporte

1. **Leer documentación**: Empieza por el [Índice](INDICE_SISTEMA_DUPLICADOS.md)
2. **Ejecutar tests**: `python3 test_duplicate_system.py`
3. **Ver logs**: `tail -f logs/extractor.log`

---

## 🎉 Características del Sistema Completo

### ✅ Invoice Extractor (Original)
- OCR híbrido (Tesseract + Ollama)
- Extracción de datos estructurados
- Validación de facturas
- Dashboard con Streamlit
- Integración con Google Drive

### 🆕 Sistema de Detección de Duplicados (Nuevo)
- Detección por contenido (hash SHA256)
- 5 decisiones inteligentes
- Cuarentena organizada
- Auditoría completa
- Procesamiento incremental

---

**¡Sistema completo y documentado!** 🎉

**Siguiente paso**: [Ver índice completo](INDICE_SISTEMA_DUPLICADOS.md)

---

*Última actualización: 2025-11-02*
