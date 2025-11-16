# RESUMEN EJECUTIVO: Investigación Facturas No Cargadas

**Fecha:** 2025-11-09  
**Investigación:** Comparación Drive vs BD y análisis de por qué no se están cargando facturas

---

## 📊 ESTADÍSTICAS PRINCIPALES

### Comparación Drive vs Base de Datos
- **PDFs en Google Drive:** 298 archivos
- **Facturas en Base de Datos:** 73 registros
- **Diferencia:** **225 PDFs NO procesados** (75.5% de los archivos en Drive)

### Distribución en Base de Datos
- **Estado "procesado":** 11 facturas (15.1%)
- **Estado "revisar":** 62 facturas (84.9%)
- **Estado "error":** 0 facturas
- **Estado "pendiente":** 0 facturas

---

## 🔍 HALLAZGOS CRÍTICOS

### 1. **Job Incremental FALLA al ejecutarse (Error de Base de Datos)**

**Problema identificado:**
- ❌ **El job SÍ se ejecuta** (cron cada 6 horas ejecuta `monitorear_drive.sh`)
- ❌ **PERO FALLA** con error de constraint de base de datos: `CheckViolation: estado 'error_permanente' violates check constraint`
- El constraint de la BD **NO incluye** `error_permanente` aunque el código intenta usarlo
- Esto causa que el job falle completamente y no procese ningún archivo nuevo

**Evidencia:**
- Logs muestran ejecución del job a las **18:00:04** (hace ~1 hora)
- Error: `new row for relation "facturas" violates check constraint "facturas_estado_check"`
- El sistema intenta marcar facturas como `error_permanente` pero la BD lo rechaza
- Como resultado, **NO existe registro de `last_sync_time`** porque el job falla antes de completarse
- Última factura procesada: **2025-11-08 18:09:16** (hace 23 horas)

### 2. **225 PDFs en Drive nunca fueron procesados**

**Análisis:**
- Hay **298 PDFs** en Google Drive
- Solo **73** están en la base de datos
- **225 PDFs (75.5%)** nunca fueron detectados o procesados por el sistema

**Posibles causas:**
- El job incremental solo busca archivos **modificados desde la última sincronización**
- Como no hay `last_sync_time`, el sistema busca solo archivos modificados en las últimas 24 horas (ventana de sincronización)
- Los archivos antiguos que nunca fueron procesados no aparecen en búsquedas incrementales

### 3. **62 facturas en estado "revisar" con errores de validación**

**Problema:**
- **100% de las facturas en "revisar"** tienen el error: **"Validación de negocio falló"**
- Esto sugiere un problema sistemático con las reglas de validación, no errores individuales

**Implicaciones:**
- Las facturas se están extrayendo correctamente (OCR funciona)
- Pero fallan en la validación de reglas de negocio
- Necesitan revisión manual o ajuste de reglas de validación

---

## 📋 ANÁLISIS DETALLADO

### Estado de Sincronización
- **Última sincronización registrada:** NO EXISTE
- **Última factura procesada:** 2025-11-08 18:09:16 (hace 23 horas)
- **Estado:** El sistema está "dormido" - no procesa nuevos archivos

### Eventos Recientes (últimas 24 horas)
- **Total de eventos:** 627 eventos
- **INFO:** 9 eventos
- **WARNING:** 11 eventos (principalmente "duplicate_check: Archivo ya procesado")
- **Últimos eventos:** Intentos de procesamiento de facturas ya existentes

### Configuración de Cron
- **Cron job encontrado:** `0 */6 * * * /home/alex/proyectos/invoice-extractor/scripts/monitorear_drive.sh`
- **Frecuencia:** Cada 6 horas
- **Script ejecutado:** `monitorear_drive.sh` (no el job incremental directamente)

---

## 🎯 PROBLEMAS IDENTIFICADOS

### Problema #1: Job Incremental Falla por Error de Base de Datos
**Severidad:** 🔴 CRÍTICA

**Causa raíz:**
- El constraint `facturas_estado_check` en la BD **NO incluye** `error_permanente`
- El código intenta marcar facturas como `error_permanente` cuando alcanzan máximo de intentos
- La migración que agregó `error_permanente` al modelo **NO se aplicó correctamente** en la BD
- El job se ejecuta pero falla completamente, impidiendo procesar nuevos archivos

**Impacto:**
- El job falla cada vez que intenta reprocesar facturas en "revisar"
- 225 PDFs nuevos nunca serán procesados automáticamente
- El sistema no puede completar ninguna ejecución exitosa

### Problema #2: Archivos Antiguos No Procesados
**Severidad:** 🟡 ALTA

**Causa raíz:**
- El job incremental solo busca archivos modificados desde `last_sync_time`
- Sin `last_sync_time`, busca solo archivos de las últimas 24 horas
- Archivos antiguos que nunca fueron procesados quedan fuera del alcance

**Impacto:**
- 225 PDFs existentes en Drive nunca se procesarán con el job incremental actual

### Problema #3: Validación de Negocio Falla Sistemáticamente
**Severidad:** 🟡 ALTA

**Causa raíz:**
- 62 de 73 facturas (84.9%) fallan validación de negocio
- Todas con el mismo tipo de error: "Validación de negocio falló"
- Necesita análisis de qué regla específica está fallando

**Impacto:**
- Facturas se extraen pero no se marcan como "procesado"
- Requieren revisión manual

---

## 💡 RECOMENDACIONES

### Acción Inmediata #1: CORREGIR CONSTRAINT DE BASE DE DATOS (URGENTE)
```sql
-- Verificar constraint actual
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'facturas'::regclass 
AND conname = 'facturas_estado_check';

-- Corregir constraint para incluir 'error_permanente'
ALTER TABLE facturas 
DROP CONSTRAINT IF EXISTS facturas_estado_check;

ALTER TABLE facturas 
ADD CONSTRAINT facturas_estado_check 
CHECK (estado IN ('procesado', 'pendiente', 'error', 'revisar', 'duplicado', 'error_permanente'));
```

**Objetivo:** Permitir que el sistema marque facturas como `error_permanente` sin fallar

### Acción Inmediata #2: Ejecutar Job Incremental Manualmente
```bash
cd /home/alex/proyectos/invoice-extractor
venv/bin/python scripts/run_ingest_incremental.py
```

**Objetivo:** Procesar los 9 archivos que el sistema detectó como modificados recientemente

### Acción Inmediata #3: Procesar Archivos Antiguos
**Opciones:**
1. **Ejecutar job inicial completo** (si existe) para procesar todos los archivos desde cero
2. **Modificar temporalmente** `last_sync_time` a una fecha muy antigua para forzar procesamiento de todos los archivos
3. **Crear script ad-hoc** que liste todos los PDFs y los procese

### Acción Inmediata #4: Investigar Errores de Validación
**Pasos:**
1. Revisar ejemplos específicos de facturas en "revisar"
2. Identificar qué regla de validación está fallando
3. Ajustar reglas o corregir datos según corresponda

### Acción a Mediano Plazo #1: Configurar Cron Correctamente
**Recomendación:**
- Modificar `monitorear_drive.sh` para que ejecute el job incremental
- O agregar línea en cron que ejecute directamente `run_ingest_incremental.py`
- Verificar que el job guarde `last_sync_time` correctamente

### Acción a Mediano Plazo #2: Implementar Job de "Catch-up"
**Recomendación:**
- Crear mecanismo para procesar archivos antiguos que nunca fueron procesados
- Ejecutar periódicamente (ej: semanal) para detectar archivos faltantes

---

## 📈 MÉTRICAS DE SALUD DEL SISTEMA

| Métrica | Valor | Estado |
|---------|-------|--------|
| PDFs en Drive | 298 | ✅ |
| Facturas en BD | 73 | ⚠️ |
| Cobertura | 24.5% | 🔴 |
| Última sync | N/A | 🔴 |
| Última factura | Hace 23h | 🟡 |
| Facturas procesadas | 11 (15.1%) | 🔴 |
| Facturas en revisar | 62 (84.9%) | 🟡 |
| Job ejecutándose | No | 🔴 |

---

## 🎬 CONCLUSIÓN

El sistema tiene **4 problemas principales**:

1. **El job incremental FALLA por error de BD** - el constraint no permite `error_permanente`, bloqueando todas las ejecuciones
2. **225 PDFs antiguos nunca fueron procesados** - el sistema solo busca archivos recientes
3. **84.9% de las facturas fallan validación** - problema sistemático con reglas de negocio
4. **El job se ejecuta pero no completa** - falla antes de guardar `last_sync_time`, impidiendo sincronización incremental

**Prioridad de acción:**
1. 🔴 **CRÍTICO:** Corregir constraint de BD para permitir `error_permanente` (bloquea todo el sistema)
2. 🔴 **URGENTE:** Ejecutar job incremental manualmente después de corregir BD
3. 🟡 **ALTA:** Investigar y corregir errores de validación de negocio
4. 🟡 **ALTA:** Procesar los 225 PDFs antiguos pendientes

---

**Investigación realizada:** 2025-11-09  
**Próximos pasos:** Ejecutar acciones inmediatas y monitorear resultados

