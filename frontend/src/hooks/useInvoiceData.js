import { useState, useEffect } from 'react';
import {
  fetchInvoiceSummary,
  fetchInvoicesByDay,
  fetchRecentInvoices,
  fetchCategoriesBreakdown,
  fetchFailedInvoices,
  fetchAllFacturas,
  sanitizeErrorMessage
} from '../utils/api';

/**
 * Hook personalizado para obtener datos de facturas
 */
export function useInvoiceData(month, year) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        // Fetch paralelo de todos los endpoints
        // Nota: fetchFailedInvoices no requiere month/year - devuelve TODAS las facturas fallidas
        // Usar Promise.allSettled para que si un endpoint falla, los demás sigan funcionando
        const results = await Promise.allSettled([
          fetchInvoiceSummary(month, year),
          fetchInvoicesByDay(month, year),
          fetchRecentInvoices(month, year, 5),
          fetchCategoriesBreakdown(month, year),
          fetchFailedInvoices(), // Sin parámetros - devuelve todas las facturas fallidas
          fetchAllFacturas(month, year)
        ]);
        
        // Extraer valores, usando valores por defecto si algún promise falló
        const summary = results[0].status === 'fulfilled' ? results[0].value : null;
        const byDay = results[1].status === 'fulfilled' ? results[1].value : [];
        const recent = results[2].status === 'fulfilled' ? results[2].value : [];
        const categories = results[3].status === 'fulfilled' ? results[3].value : [];
        const failed = results[4].status === 'fulfilled' ? results[4].value : []; // Si falla, usar array vacío
        const allFacturas = results[5].status === 'fulfilled' ? results[5].value : [];
        
        // Si el summary falló, lanzar error (es crítico)
        if (!summary) {
          throw new Error(results[0].reason?.message || 'Error al cargar resumen de facturas');
        }

        // Transformar datos para KPIs
        const kpis = transformToKPIs(summary, allFacturas);

        // Transformar datos de calidad
        const quality = extractQualityMetrics(summary);

        setData({
          summary,
          kpis,
          chartData: byDay,
          recent,
          quality,
          categories,
          failedInvoices: failed,
          allFacturas: allFacturas
        });
      } catch (err) {
        console.error('Error fetching invoice data:', err);
        // Formatear error de forma legible
        let errorMsg = 'Error al cargar datos';
        if (err?.message) {
          errorMsg = err.message;
        } else if (typeof err === 'string') {
          errorMsg = err;
        } else if (err && typeof err === 'object') {
          errorMsg = err.message || err.detail || 'Error de conexión con el servidor';
        }
        // Sanitizar el mensaje de error para ocultar detalles técnicos
        errorMsg = sanitizeErrorMessage(errorMsg);
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    }

    if (month && year) {
      fetchData();
    }
  }, [month, year]);

  return { data, loading, error };
}

/**
 * Transformar summary a formato de KPIs
 */
function transformToKPIs(summary, allFacturas = []) {
  // Nota: Los cambios porcentuales se calcularían comparando con el mes anterior
  // Por ahora, retornamos valores sin comparación
  // Si facturas_exitosas es 0 pero hay total_facturas, usar total_facturas como actual
  const facturasActual = (summary.facturas_exitosas > 0) 
    ? summary.facturas_exitosas 
    : (summary.total_facturas || 0);
  
  // Calcular suma de impuestos totales desde las facturas del mes
  const impuestosTotal = allFacturas.reduce((sum, factura) => {
    return sum + (parseFloat(factura.impuestos_total) || 0);
  }, 0);
  
  return {
    facturas: {
      actual: facturasActual,
      total: summary.total_facturas || 0,
      cambio: 0 // Se calcularía comparando con mes anterior
    },
    importe: {
      valor: summary.importe_total || 0,
      cambio: 0 // Se calcularía comparando con mes anterior
    },
    impuestos_total: impuestosTotal,
    promedio: {
      valor: summary.promedio_factura || 0,
      cambio: 0 // Se calcularía comparando con mes anterior
    },
    proveedores: {
      cantidad: summary.proveedores_activos || 0,
      cambio: 0 // Se calcularía comparando con mes anterior
    }
  };
}

/**
 * Extraer métricas de calidad del summary
 */
function extractQualityMetrics(summary) {
  return {
    exitosas: summary.facturas_exitosas || 0,
    fallidas: summary.facturas_fallidas || 0,
    confianza: summary.confianza_extraccion || 0
  };
}

