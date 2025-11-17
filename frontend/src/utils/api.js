/**
 * Cliente API para comunicación con el backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/invoice-api/api';

/**
 * Sanitiza mensajes de error técnicos y los convierte en mensajes amigables
 * @param {string} errorMessage - Mensaje de error original
 * @returns {string} - Mensaje de error sanitizado
 */
export function sanitizeErrorMessage(errorMessage) {
  // Si no es un string válido, devolver string vacío (el componente manejará el fallback)
  if (!errorMessage || typeof errorMessage !== 'string') {
    return '';
  }

  // Detectar errores técnicos de base de datos
  const technicalErrorPatterns = [
    /CheckViolation/i,
    /psycopg2\.errors\./i,
    /violates check constraint/i,
    /Failing row contains/i,
    /DETAIL:/i,
    /IntegrityError/i,
    /ForeignKeyViolation/i,
    /UniqueViolation/i,
    /NotNullViolation/i
  ];

  // Verificar si es un error técnico
  const isTechnicalError = technicalErrorPatterns.some(pattern => pattern.test(errorMessage));
  
  // Debug: log si detecta error técnico
  if (isTechnicalError) {
    console.log('🔍 Error técnico detectado:', errorMessage.substring(0, 100));
  }

  if (isTechnicalError) {
    // Intentar extraer códigos de referencia (IDs, números de factura, etc.)
    const referencePatterns = [
      /\((\d+),/g,  // IDs numéricos al inicio de "Failing row contains"
      /Fact\s+([A-Z0-9]+)/gi,  // Números de factura (agregado 'g' para matchAll)
      /id[:\s]+(\d+)/gi,  // IDs después de "id:" (agregado 'g' para matchAll)
      /\((\d+)\)/g  // IDs entre paréntesis
    ];

    const references = [];
    referencePatterns.forEach(pattern => {
      const matches = errorMessage.matchAll(pattern);
      for (const match of matches) {
        if (match[1] && !references.includes(match[1])) {
          references.push(match[1]);
        }
      }
    });

    // Construir mensaje amigable
    let friendlyMessage = 'Error técnico en la base de datos';
    
    if (references.length > 0) {
      friendlyMessage += ` (Referencia: ${references.slice(0, 3).join(', ')})`;
    }

    console.log('✅ Mensaje sanitizado:', friendlyMessage);
    return friendlyMessage;
  }

  // Si no es un error técnico, devolver el mensaje original
  return errorMessage;
}

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
      let errorDetail = `Error ${response.status}`;
      try {
        const error = await response.json();
        if (error.detail) {
          // Si es un array de errores de validación, extraer mensajes
          if (Array.isArray(error.detail)) {
            errorDetail = error.detail.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
          } else if (typeof error.detail === 'string') {
            errorDetail = error.detail;
          } else {
            errorDetail = JSON.stringify(error.detail);
          }
        } else {
          errorDetail = JSON.stringify(error);
        }
      } catch (e) {
        errorDetail = `Error ${response.status}: ${response.statusText}`;
      }
      
      // Sanitizar el mensaje de error antes de lanzarlo
      const sanitizedError = sanitizeErrorMessage(errorDetail);
      throw new Error(sanitizedError);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error en API ${endpoint}:`, error);
    // Asegurar que el mensaje también esté sanitizado si no lo estaba
    if (error.message) {
      error.message = sanitizeErrorMessage(error.message);
    }
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
 * Obtener todas las facturas fallidas (sin filtro de mes)
 */
export async function fetchFailedInvoices() {
  const response = await fetchAPI(`/facturas/failed`);
  return response.data || [];
}

/**
 * Obtener todas las facturas del mes
 */
export async function fetchAllFacturas(month, year) {
  const response = await fetchAPI(`/facturas/list?month=${month}&year=${year}`);
  return response.data || [];
}

/**
 * Obtener estadísticas de carga de datos
 */
export async function fetchDataLoadStats() {
  const response = await fetchAPI('/system/data-load-stats');
  return response;
}

