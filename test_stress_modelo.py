#!/usr/bin/env python3
"""
Prueba de stress/consistencia del modelo Ollama
Procesa la misma factura 30 veces para detectar problemas de:
- Inconsistencia en resultados
- Errores intermitentes
- Timeouts
- Variabilidad en extracción
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from security.secrets import load_env, validate_secrets
from logging_conf import get_logger
from ocr_extractor import InvoiceExtractor
from parser_normalizer import create_factura_dto, validate_fiscal_rules
from pipeline.validate import validate_business_rules

# Cargar entorno
load_env()
validate_secrets()

logger = get_logger(__name__)


class StressTestModelo:
    """Clase para realizar pruebas de stress en el modelo"""
    
    def __init__(self, pdf_path: str, num_iteraciones: int = 30):
        self.pdf_path = Path(pdf_path)
        self.num_iteraciones = num_iteraciones
        self.extractor = InvoiceExtractor()
        self.resultados: List[Dict[str, Any]] = []
        self.errores: List[Dict[str, Any]] = []
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")
    
    def ejecutar_prueba(self, iteracion: int) -> Dict[str, Any]:
        """Ejecuta una iteración de la prueba"""
        inicio = time.time()
        resultado = {
            'iteracion': iteracion,
            'timestamp': datetime.now().isoformat(),
            'exito': False,
            'tiempo_segundos': 0,
            'error': None,
            'datos_extraidos': None,
            'dto_creado': False,
            'validacion_fiscal': False,
            'validacion_negocio': False
        }
        
        try:
            # Extraer datos
            raw_data = self.extractor.extract_invoice_data(str(self.pdf_path))
            tiempo_extraccion = time.time() - inicio
            
            resultado['tiempo_segundos'] = round(tiempo_extraccion, 2)
            resultado['datos_extraidos'] = raw_data
            resultado['confianza'] = raw_data.get('confianza', 'desconocida')
            resultado['extractor_usado'] = 'ollama' if raw_data.get('confianza') != 'baja' else 'tesseract'
            
            # Crear DTO
            metadata = {
                'drive_file_id': f'stress_test_{iteracion}',
                'drive_file_name': self.pdf_path.name,
                'drive_folder_name': 'stress_test',
                'extractor': resultado['extractor_usado']
            }
            
            dto = create_factura_dto(raw_data, metadata)
            resultado['dto_creado'] = dto is not None
            
            if dto:
                resultado['estado_dto'] = dto.get('estado', 'desconocido')
                resultado['importe_total'] = dto.get('importe_total')
                resultado['proveedor'] = dto.get('proveedor')
                resultado['numero_factura'] = dto.get('numero_factura')
                resultado['fecha_emision'] = str(dto.get('fecha_emision')) if dto.get('fecha_emision') else None
                
                # Validaciones (retornan solo bool, no tupla)
                resultado['validacion_fiscal'] = validate_fiscal_rules(dto)
                resultado['mensaje_fiscal'] = 'OK' if resultado['validacion_fiscal'] else 'Falló'
                
                # validate_business_rules solo toma el DTO, no metadata
                resultado['validacion_negocio'] = validate_business_rules(dto)
                resultado['mensaje_negocio'] = 'OK' if resultado['validacion_negocio'] else 'Falló'
            
            resultado['exito'] = True
            
        except Exception as e:
            resultado['tiempo_segundos'] = round(time.time() - inicio, 2)
            resultado['error'] = str(e)
            resultado['tipo_error'] = type(e).__name__
            self.errores.append(resultado)
            logger.error(f"Iteración {iteracion} falló: {e}")
        
        return resultado
    
    def ejecutar_todas_las_pruebas(self):
        """Ejecuta todas las iteraciones"""
        print("\n" + "="*70)
        print("🧪 PRUEBA DE STRESS - MODELO OLLAMA")
        print("="*70)
        print(f"Archivo: {self.pdf_path.name}")
        print(f"Iteraciones: {self.num_iteraciones}")
        print(f"Modelo: {self.extractor.ollama_model}")
        print("="*70 + "\n")
        
        for i in range(1, self.num_iteraciones + 1):
            print(f"[{i:2d}/{self.num_iteraciones}] Procesando...", end=" ", flush=True)
            resultado = self.ejecutar_prueba(i)
            self.resultados.append(resultado)
            
            if resultado['exito']:
                tiempo = resultado['tiempo_segundos']
                confianza = resultado.get('confianza', 'N/A')
                importe = resultado.get('importe_total', 'N/A')
                print(f"✓ ({tiempo:.1f}s) Confianza: {confianza}, Importe: {importe}")
            else:
                print(f"✗ ERROR: {resultado.get('error', 'Desconocido')}")
            
            # Pequeña pausa para no saturar el servidor
            if i < self.num_iteraciones:
                time.sleep(0.5)
        
        print("\n" + "="*70)
        print("✅ PRUEBAS COMPLETADAS")
        print("="*70 + "\n")
    
    def analizar_resultados(self) -> Dict[str, Any]:
        """Analiza los resultados y genera estadísticas"""
        exitosos = [r for r in self.resultados if r['exito']]
        fallidos = [r for r in self.resultados if not r['exito']]
        
        analisis = {
            'resumen': {
                'total_iteraciones': self.num_iteraciones,
                'exitosas': len(exitosos),
                'fallidas': len(fallidos),
                'tasa_exito_porcentaje': round((len(exitosos) / self.num_iteraciones) * 100, 2) if self.num_iteraciones > 0 else 0
            },
            'tiempos': {
                'promedio': round(sum(r['tiempo_segundos'] for r in exitosos) / len(exitosos), 2) if exitosos else 0,
                'minimo': min((r['tiempo_segundos'] for r in exitosos), default=0),
                'maximo': max((r['tiempo_segundos'] for r in exitosos), default=0),
                'desviacion': self._calcular_desviacion([r['tiempo_segundos'] for r in exitosos])
            },
            'confianza': {
                'distribucion': dict(Counter(r.get('confianza', 'desconocida') for r in exitosos)),
                'alta_porcentaje': round((sum(1 for r in exitosos if r.get('confianza') == 'alta') / len(exitosos)) * 100, 2) if exitosos else 0,
                'media_porcentaje': round((sum(1 for r in exitosos if r.get('confianza') == 'media') / len(exitosos)) * 100, 2) if exitosos else 0,
                'baja_porcentaje': round((sum(1 for r in exitosos if r.get('confianza') == 'baja') / len(exitosos)) * 100, 2) if exitosos else 0
            },
            'extractor': {
                'ollama_usado': sum(1 for r in exitosos if r.get('extractor_usado') == 'ollama'),
                'tesseract_usado': sum(1 for r in exitosos if r.get('extractor_usado') == 'tesseract'),
                'ollama_porcentaje': round((sum(1 for r in exitosos if r.get('extractor_usado') == 'ollama') / len(exitosos)) * 100, 2) if exitosos else 0
            },
            'importes': {
                'valores_unicos': len(set(r.get('importe_total') for r in exitosos if r.get('importe_total') is not None)),
                'valores_distintos': list(set(r.get('importe_total') for r in exitosos if r.get('importe_total') is not None)),
                'frecuencia_valores': dict(Counter(r.get('importe_total') for r in exitosos if r.get('importe_total') is not None))
            },
            'proveedores': {
                'valores_unicos': len(set(r.get('proveedor') for r in exitosos if r.get('proveedor') is not None)),
                'valores_distintos': list(set(r.get('proveedor') for r in exitosos if r.get('proveedor') is not None)),
                'frecuencia_valores': dict(Counter(r.get('proveedor') for r in exitosos if r.get('proveedor') is not None))
            },
            'validaciones': {
                'fiscal_ok': sum(1 for r in exitosos if r.get('validacion_fiscal')),
                'fiscal_fallo': sum(1 for r in exitosos if not r.get('validacion_fiscal')),
                'negocio_ok': sum(1 for r in exitosos if r.get('validacion_negocio')),
                'negocio_fallo': sum(1 for r in exitosos if not r.get('validacion_negocio'))
            },
            'problemas_detectados': self._detectar_problemas(),
            'errores': {
                'total': len(fallidos),
                'tipos': dict(Counter(r.get('tipo_error', 'Desconocido') for r in fallidos)),
                'detalles': [{'iteracion': r['iteracion'], 'error': r.get('error'), 'tipo': r.get('tipo_error')} for r in fallidos]
            }
        }
        
        return analisis
    
    def _calcular_desviacion(self, valores: List[float]) -> float:
        """Calcula la desviación estándar"""
        if not valores:
            return 0.0
        promedio = sum(valores) / len(valores)
        varianza = sum((x - promedio) ** 2 for x in valores) / len(valores)
        return round(varianza ** 0.5, 2)
    
    def _detectar_problemas(self) -> List[str]:
        """Detecta problemas comunes en los resultados"""
        problemas = []
        exitosos = [r for r in self.resultados if r['exito']]
        
        if not exitosos:
            return ["CRÍTICO: Ninguna iteración exitosa"]
        
        # Verificar inconsistencia en importes
        importes = [r.get('importe_total') for r in exitosos if r.get('importe_total') is not None]
        if len(set(importes)) > 1:
            problemas.append(f"⚠️ INCONSISTENCIA: Se encontraron {len(set(importes))} valores distintos de importe_total")
        
        # Verificar inconsistencias en proveedores
        proveedores = [r.get('proveedor') for r in exitosos if r.get('proveedor') is not None]
        if len(set(proveedores)) > 1:
            problemas.append(f"⚠️ INCONSISTENCIA: Se encontraron {len(set(proveedores))} valores distintos de proveedor")
        
        # Verificar alta variabilidad en tiempos
        tiempos = [r['tiempo_segundos'] for r in exitosos]
        if tiempos:
            promedio = sum(tiempos) / len(tiempos)
            max_tiempo = max(tiempos)
            if max_tiempo > promedio * 2:
                problemas.append(f"⚠️ VARIABILIDAD: Tiempo máximo ({max_tiempo:.1f}s) es más del doble del promedio ({promedio:.1f}s)")
        
        # Verificar muchas confidencias bajas
        bajas = sum(1 for r in exitosos if r.get('confianza') == 'baja')
        if bajas > len(exitosos) * 0.5:
            problemas.append(f"⚠️ BAJA CONFIANZA: {bajas}/{len(exitosos)} iteraciones con confianza baja (>{bajas/len(exitosos)*100:.0f}%)")
        
        # Verificar muchos fallos de validación
        fiscal_fallos = sum(1 for r in exitosos if not r.get('validacion_fiscal'))
        if fiscal_fallos > len(exitosos) * 0.3:
            problemas.append(f"⚠️ VALIDACIÓN FISCAL: {fiscal_fallos}/{len(exitosos)} fallos de validación fiscal")
        
        return problemas
    
    def generar_informe(self, analisis: Dict[str, Any]):
        """Genera un informe detallado"""
        print("\n" + "="*70)
        print("📊 ANÁLISIS DE RESULTADOS")
        print("="*70)
        
        # Resumen general
        resumen = analisis['resumen']
        print(f"\n📈 RESUMEN GENERAL")
        print(f"   Total de iteraciones: {resumen['total_iteraciones']}")
        print(f"   ✅ Exitosas: {resumen['exitosas']} ({resumen['tasa_exito_porcentaje']}%)")
        print(f"   ❌ Fallidas: {resumen['fallidas']}")
        
        # Tiempos
        tiempos = analisis['tiempos']
        print(f"\n⏱️  TIEMPOS DE PROCESAMIENTO")
        print(f"   Promedio: {tiempos['promedio']}s")
        print(f"   Mínimo: {tiempos['minimo']}s")
        print(f"   Máximo: {tiempos['maximo']}s")
        print(f"   Desviación estándar: {tiempos['desviacion']}s")
        
        # Confianza
        confianza = analisis['confianza']
        print(f"\n🎯 DISTRIBUCIÓN DE CONFIANZA")
        print(f"   Alta: {confianza['alta_porcentaje']}%")
        print(f"   Media: {confianza['media_porcentaje']}%")
        print(f"   Baja: {confianza['baja_porcentaje']}%")
        print(f"   Distribución: {confianza['distribucion']}")
        
        # Extractor usado
        extractor = analisis['extractor']
        print(f"\n🔧 EXTRACTOR UTILIZADO")
        print(f"   Ollama: {extractor['ollama_usado']} veces ({extractor['ollama_porcentaje']}%)")
        print(f"   Tesseract: {extractor['tesseract_usado']} veces")
        
        # Importes
        importes = analisis['importes']
        print(f"\n💰 IMPORTES EXTRAÍDOS")
        print(f"   Valores únicos: {importes['valores_unicos']}")
        if importes['valores_distintos']:
            print(f"   Valores encontrados: {importes['valores_distintos']}")
            print(f"   Frecuencia: {importes['frecuencia_valores']}")
        
        # Proveedores
        proveedores = analisis['proveedores']
        print(f"\n🏢 PROVEEDORES EXTRAÍDOS")
        print(f"   Valores únicos: {proveedores['valores_unicos']}")
        if proveedores['valores_distintos']:
            print(f"   Valores encontrados: {proveedores['valores_distintos']}")
            print(f"   Frecuencia: {proveedores['frecuencia_valores']}")
        
        # Validaciones
        validaciones = analisis['validaciones']
        print(f"\n✅ VALIDACIONES")
        print(f"   Fiscal OK: {validaciones['fiscal_ok']}/{resumen['exitosas']}")
        print(f"   Fiscal Falló: {validaciones['fiscal_fallo']}/{resumen['exitosas']}")
        print(f"   Negocio OK: {validaciones['negocio_ok']}/{resumen['exitosas']}")
        print(f"   Negocio Falló: {validaciones['negocio_fallo']}/{resumen['exitosas']}")
        
        # Problemas detectados
        problemas = analisis['problemas_detectados']
        print(f"\n⚠️  PROBLEMAS DETECTADOS")
        if problemas:
            for problema in problemas:
                print(f"   {problema}")
        else:
            print("   ✅ No se detectaron problemas significativos")
        
        # Errores
        errores = analisis['errores']
        if errores['total'] > 0:
            print(f"\n❌ ERRORES ({errores['total']})")
            print(f"   Tipos: {errores['tipos']}")
            for error in errores['detalles'][:5]:  # Mostrar solo los primeros 5
                print(f"   Iteración {error['iteracion']}: {error['tipo']} - {error['error'][:60]}")
        
        print("\n" + "="*70)
    
    def guardar_resultados(self, analisis: Dict[str, Any], archivo_salida: str = None):
        """Guarda los resultados en un archivo JSON"""
        if archivo_salida is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_salida = f"resultados_stress_test_{timestamp}.json"
        
        datos_completos = {
            'metadata': {
                'archivo_procesado': str(self.pdf_path),
                'modelo_ollama': self.extractor.ollama_model,
                'fecha_prueba': datetime.now().isoformat(),
                'numero_iteraciones': self.num_iteraciones
            },
            'analisis': analisis,
            'resultados_detallados': self.resultados
        }
        
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(datos_completos, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Resultados guardados en: {archivo_salida}")
        return archivo_salida


def main():
    """Función principal"""
    pdf_path = Path(__file__).parent / 'temp' / 'Iberdrola Junio 2025.pdf'
    
    if not pdf_path.exists():
        print(f"❌ Error: Archivo no encontrado: {pdf_path}")
        sys.exit(1)
    
    # Crear y ejecutar prueba (10 iteraciones para prueba rápida)
    prueba = StressTestModelo(str(pdf_path), num_iteraciones=10)
    prueba.ejecutar_todas_las_pruebas()
    
    # Analizar resultados
    analisis = prueba.analizar_resultados()
    prueba.generar_informe(analisis)
    
    # Guardar resultados
    archivo_resultados = prueba.guardar_resultados(analisis)
    
    print(f"\n✅ Prueba completada. Ver archivo '{archivo_resultados}' para detalles completos.")


if __name__ == '__main__':
    main()

