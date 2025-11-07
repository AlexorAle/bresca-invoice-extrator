import { useState, useEffect } from 'react';
import {
  fetchInvoiceSummary,
  fetchInvoicesByDay,
  fetchRecentInvoices,
  fetchCategoriesBreakdown,
  fetchFailedInvoices,
  fetchAllFacturas
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
        const [summary, byDay, recent, categories, failed, allFacturas] = await Promise.all([
          fetchInvoiceSummary(month, year),
          fetchInvoicesByDay(month, year),
          fetchRecentInvoices(month, year, 5),
          fetchCategoriesBreakdown(month, year),
          fetchFailedInvoices(month, year),
          fetchAllFacturas(month, year)
        ]);

        // Transformar datos para KPIs
        const kpis = transformToKPIs(summary);

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
        setError(err.message || 'Error al cargar datos');
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
function transformToKPIs(summary) {
  // Nota: Los cambios porcentuales se calcularían comparando con el mes anterior
  // Por ahora, retornamos valores sin comparación
  // Si facturas_exitosas es 0 pero hay total_facturas, usar total_facturas como actual
  const facturasActual = (summary.facturas_exitosas > 0) 
    ? summary.facturas_exitosas 
    : (summary.total_facturas || 0);
  
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

