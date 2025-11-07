# Resumen Ejecutivo: Primera Carga y Automatización

**Fecha:** 5 de noviembre de 2025  
**Objetivo:** Configurar primera carga de facturas y automatización de monitoreo

---

## ✅ Sistema Preparado

### Detección Automática de Duplicados

El sistema ya tiene implementado:

1. **Hash de Contenido** (`hash_contenido`):
   - Calcula SHA256 del contenido del PDF
   - Compara con BD antes de procesar
   - Si existe → **ignora** (ya procesado)
   - Si no existe → **procesa** (nuevo)

2. **Drive File ID** (`drive_file_id`):
   - Identificador único de Google Drive
   - También se usa para detectar duplicados

**Resultado:** El sistema automáticamente solo procesa archivos nuevos.

---

## 🚀 Primera Carga (Ejecutar Ahora)

### Pasos

1. **Ejecutar script de primera carga:**
   ```bash
   cd /home/alex/proyectos/invoice-extractor
   ./scripts/primera_carga.sh
   ```

2. **Qué hace:**
   - ✅ Busca TODOS los PDFs en Google Drive (recursivo)
   - ✅ Compara cada archivo con BD usando hash
   - ✅ Solo procesa archivos que NO estén en BD
   - ✅ Calcula y guarda hash para futuras comparaciones
   - ✅ Espera 3 segundos entre facturas (rate limiting)

3. **Tiempo estimado:**
   - ~5 segundos por factura
   - Si hay 80 facturas: ~6-7 minutos

---

## 🔄 Automatización (Opcional)

### ¿Necesitas dejar un proceso corriendo?

**Respuesta corta:** NO, no necesitas dejar un proceso corriendo 24/7.

**Mejor opción:** Usar **Cron Job** que ejecuta periódicamente.

### Opción Recomendada: Cron Job

**Ejecutar cada hora:**
```bash
crontab -e
# Agregar esta línea:
0 * * * * /home/alex/proyectos/invoice-extractor/scripts/monitorear_drive.sh
```

**Qué hace:**
- Cada hora, el cron ejecuta el script
- El script busca nuevos archivos en Drive
- Solo procesa los que no están en BD (usa hash)
- Registra logs en `logs/monitoreo_drive.log`

**Ventajas:**
- ✅ No requiere proceso corriendo 24/7
- ✅ Simple de configurar
- ✅ Ejecución automática periódica
- ✅ Logs para monitoreo

---

## 📋 Flujo Completo

### Primera Carga (Hoy)
```
1. Ejecutar: ./scripts/primera_carga.sh
2. Sistema busca TODOS los PDFs en Drive
3. Compara con BD (vacía) → todos son nuevos
4. Procesa todos los archivos
5. Guarda hash de cada archivo en BD
```

### Automatización (Futuro)
```
1. Cron ejecuta: ./scripts/monitorear_drive.sh (cada hora)
2. Sistema busca TODOS los PDFs en Drive
3. Compara hash con BD
4. Si hash existe → ignora (ya procesado)
5. Si hash NO existe → procesa (nuevo archivo)
6. Guarda nuevo hash en BD
```

---

## ✅ Checklist

### Primera Carga
- [ ] Verificar variables de entorno (.env)
- [ ] Verificar conexión a Google Drive
- [ ] Verificar conexión a PostgreSQL
- [ ] Ejecutar: `./scripts/primera_carga.sh`
- [ ] Verificar resultados en dashboard

### Automatización (Opcional)
- [ ] Configurar cron job (recomendado: cada hora)
- [ ] Verificar logs: `tail -f logs/monitoreo_drive.log`
- [ ] Probar subiendo un archivo nuevo a Drive
- [ ] Verificar que se procese automáticamente

---

## 📊 Monitoreo

### Ver Estado

**Dashboard Web:**
```
http://localhost:5173
```

**API Directa:**
```bash
curl http://localhost:8001/api/facturas/summary?month=11&year=2025
```

**Logs:**
```bash
tail -f logs/monitoreo_drive.log
```

---

## 🎯 Conclusión

**Sistema listo para:**

1. ✅ **Primera carga**: Ejecutar `./scripts/primera_carga.sh`
2. ✅ **Automatización**: Configurar cron job (opcional)
3. ✅ **Monitoreo**: Dashboard y logs disponibles

**No necesitas:**
- ❌ Proceso corriendo 24/7
- ❌ Monitoreo manual constante
- ❌ Scripts adicionales

**El sistema automáticamente:**
- Detecta archivos nuevos usando hash
- Solo procesa archivos que no están en BD
- Funciona con cron job periódico

---

**Estado:** ✅ Listo para primera carga  
**Próximo paso:** Ejecutar `./scripts/primera_carga.sh`

