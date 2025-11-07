/**
 * Funciones de formateo de datos
 */

/**
 * Formatear moneda
 */
export function formatCurrency(value) {
  if (value === null || value === undefined) return '0,00 €';
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

/**
 * Formatear número
 */
export function formatNumber(value) {
  if (value === null || value === undefined) return '0';
  return new Intl.NumberFormat('es-ES').format(value);
}

/**
 * Formatear porcentaje
 */
export function formatPercentage(value) {
  if (value === null || value === undefined) return '+0,0%';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1).replace('.', ',')}%`;
}

/**
 * Formatear fecha
 */
export function formatDate(dateString) {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    }).format(date);
  } catch (e) {
    return dateString;
  }
}

/**
 * Formatear tiempo relativo (hace X minutos)
 */
export function formatRelativeTime(dateString) {
  if (!dateString) return 'Nunca';
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `Hace ${diffHours} h`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `Hace ${diffDays} días`;
  } catch (e) {
    return dateString;
  }
}

