/**
 * Cliente API para comunicación con el backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Wrapper para fetch con manejo de errores
 */
async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
      throw new Error(error.detail || `Error ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error en API ${endpoint}:`, error);
    throw error;
  }
}

/**
 * Obtener resumen de facturas del mes
 */
export async function fetchInvoiceSummary(month, year) {
  return fetchAPI(`/facturas/summary?month=${month}&year=${year}`);
}

/**
 * Obtener facturas agrupadas por día
 */
export async function fetchInvoicesByDay(month, year) {
  const response = await fetchAPI(`/facturas/by_day?month=${month}&year=${year}`);
  return response.data || [];
}

/**
 * Obtener facturas recientes
 */
export async function fetchRecentInvoices(month, year, limit = 5) {
  const response = await fetchAPI(`/facturas/recent?month=${month}&year=${year}&limit=${limit}`);
  return response.data || [];
}

/**
 * Obtener desglose por categorías
 */
export async function fetchCategoriesBreakdown(month, year) {
  const response = await fetchAPI(`/facturas/categories?month=${month}&year=${year}`);
  return response.data || [];
}

/**
 * Obtener estado de sincronización
 */
export async function fetchSyncStatus() {
  return fetchAPI('/system/sync-status');
}

/**
 * Obtener facturas fallidas del mes
 */
export async function fetchFailedInvoices(month, year) {
  const response = await fetchAPI(`/facturas/failed?month=${month}&year=${year}`);
  return response.data || [];
}

/**
 * Obtener todas las facturas del mes
 */
export async function fetchAllFacturas(month, year) {
  const response = await fetchAPI(`/facturas/list?month=${month}&year=${year}`);
  return response.data || [];
}

