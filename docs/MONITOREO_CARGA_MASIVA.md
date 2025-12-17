# Monitoreo y Control de Carga Masiva

**Fecha**: 2025-11-18  
**Objetivo**: Explicar sistema de logs, monitoreo y control de ejecución para carga masiva

---

## 📊 Sistema de Logs

### Ubicación de Logs

Los logs se guardan en formato JSON estructurado según el estándar Command Center:

- **Ubicación**: `/app/logs/extractor.log` (dentro del contenedor)
- **Formato**: JSON estructurado con campos:
  - `ts`: Timestamp RFC3339 UTC
  - `level`: Nivel (INFO, WARN, ERROR, DEBUG)
  - `component`: Componente (backend)
  - `app`: Nombre de la aplicación
  - `msg`: Mensaje
  - `request_id`: ID de request (si aplica)

### Ver Logs en Tiempo Real

**Opción 1: Desde el contenedor (RECOMENDADO)**
```bash
# Ver logs en tiempo real (formato JSON)
docker exec invoice-backend tail -f /app/logs/extractor.log

# Ver últimos 100 líneas
docker exec invoice-backend tail -n 100 /app/logs/extractor.log

# Filtrar solo errores
docker exec invoice-backend grep -i "error" /app/logs/extractor.log | tail -50

# Ver solo mensajes (sin JSON)
docker exec invoice-backend tail -f /app/logs/extractor.log | grep -o '"msg":"[^"]*"'

# Ver progreso de facturas procesadas
docker exec invoice-backend tail -f /app/logs/extractor.log | grep -i "procesando\|procesada\|exitoso"
```

**Opción 2: Script de Monitoreo Mejorado**
```bash
# Usar el script de monitoreo (ver sección siguiente)
docker exec invoice-backend bash /app/scripts/monitorear_carga.sh
```

**Opción 3: Command Center**
- Los logs en formato JSON pueden ser consumidos por sistemas de agregación de logs
- Si tienes un Command Center configurado, los logs deberían aparecer automáticamente

---

## 🔄 Flujo de Ejecución y Rate Limits

### Proceso de Carga Masiva (1,931 facturas)

#### Fase 1: Descarga de Archivos desde Google Drive
- **Proceso**: Descarga secuencial de todos los archivos PDF
- **Rate Limits**: Google Drive no tiene límites estrictos (solo límites de tamaño por archivo)
- **Tiempo estimado**: ~10-15 minutos para 1,931 archivos
- **Lotes**: No se procesan en lotes, se descargan uno por uno

#### Fase 2: Procesamiento con OpenAI (OCR)
- **Proceso**: Secuencial, una factura a la vez
- **Delay entre facturas**: **3 segundos** (configurado en `ingest.py` línea 115)
- **Modelo**: GPT-4o-mini (Vision API)
- **Rate Limits de OpenAI**:
  - **RPM (Requests Per Minute)**: ~500 requests/minuto
  - **TPM (Tokens Per Minute)**: ~1,000,000 tokens/minuto
  - **Con delay de 3 segundos**: ~20 facturas/minuto (muy conservador, margen de seguridad alto)

#### Fase 3: Retry Logic Automático
- **Manejo de errores 429 (Rate Limit Exceeded)**:
  - ✅ **YA IMPLEMENTADO** con `tenacity`
  - Retry automático con backoff exponencial: 1-60 segundos
  - Máximo 6 intentos por factura
  - Si falla después de 6 intentos, se marca como fallida y continúa con la siguiente

#### Tiempo Estimado Total

| Componente | Tiempo | Detalles |
|------------|--------|----------|
| **Descarga de archivos** | ~10-15 min | Sin rate limits significativos |
| **Delay entre facturas** | ~96.5 min | 1,931 × 3 segundos |
| **Procesamiento OpenAI** | ~160.9 min | ~5 segundos por factura (estimado) |
| **TOTAL ESTIMADO** | **~4.5 horas** | Para 1,931 facturas |

**Nota**: El tiempo real puede variar según:
- Velocidad de respuesta de OpenAI
- Errores y retries
- Complejidad de las facturas

---

## ⚠️ Manejo de Rate Limits

### Sistema de Retry Automático

El código **YA INCLUYE** manejo automático de rate limits:

**Ubicación**: `src/ocr_extractor.py` - método `_extract_with_openai()`

```python
@retry(
    wait=wait_random_exponential(min=1, max=60),  # Espera exponencial 1-60 segundos
    stop=stop_after_attempt(6)  # Máximo 6 intentos
)
def _extract_with_openai(self, img_base64: str) -> dict:
    # ... código ...
    except openai.RateLimitError as e:
        logger.warning(f"Rate limit alcanzado: {e}")
        raise  # Retry automático por tenacity
```

**Comportamiento**:
1. Si OpenAI retorna error 429 (Rate Limit), el sistema espera automáticamente
2. Espera exponencial: 1s, 2s, 4s, 8s, 16s, 32s (hasta 60s máximo)
3. Reintenta hasta 6 veces
4. Si después de 6 intentos sigue fallando, marca la factura como fallida y continúa

**Ventajas**:
- ✅ No necesitas intervención manual
- ✅ El sistema se adapta automáticamente a rate limits
- ✅ No se detiene la ejecución completa si hay un rate limit temporal

---

## 🛑 Control de Ejecución

### Detener Ejecución Manualmente

**Opción 1: Interrupción con Ctrl+C (RECOMENDADO)**
```bash
# Si ejecutas directamente desde terminal
docker exec -it invoice-backend python3 /app/src/main.py
# Presiona Ctrl+C para detener de forma segura
```

**Opción 2: Matar proceso específico**
```bash
# Encontrar PID del proceso
docker exec invoice-backend ps aux | grep "main.py"

# Matar proceso de forma segura (reemplazar PID)
docker exec invoice-backend kill -INT <PID>  # Señal de interrupción (recomendado)
# O forzar si no responde:
docker exec invoice-backend kill -9 <PID>
```

**Opción 3: Detener contenedor (NO RECOMENDADO)**
```bash
# Solo si es absolutamente necesario
docker stop invoice-backend
# ⚠️ Puede dejar datos inconsistentes
```

### Script de Monitoreo

Ver sección siguiente para el script completo de monitoreo.

---

## 📋 Recomendaciones

1. **Monitoreo en tiempo real**: Usar el script de monitoreo o `tail -f`
2. **Control manual**: El script permite detener ejecución de forma segura
3. **Rate limits**: El delay de 3 segundos es muy conservador, el sistema maneja automáticamente los rate limits
4. **Tiempo estimado**: ~4.5 horas para 1,931 facturas
5. **No interrumpir**: Si no es crítico, dejar que el sistema complete (tiene retry automático)

---

## ✅ Resumen Ejecutivo

- **Logs**: `/app/logs/extractor.log` (formato JSON)
- **Monitoreo**: Script disponible o `tail -f`
- **Rate Limits**: ✅ Manejo automático con retry (6 intentos, backoff exponencial)
- **Delay**: 3 segundos entre facturas (muy conservador)
- **Tiempo estimado**: ~4.5 horas para 1,931 facturas
- **Control**: Ctrl+C o script de monitoreo para detener de forma segura

