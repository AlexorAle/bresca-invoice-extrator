import React from 'react';

/**
 * Componente para mostrar tabla de todas las facturas del mes
 */
export function FacturasTable({ facturas = [], loading = false }) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-header p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-12 bg-gray-100 rounded"></div>
            <div className="h-12 bg-gray-100 rounded"></div>
            <div className="h-12 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!facturas || facturas.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-header p-6">
        <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900 mb-3 sm:mb-4">Todas las Facturas</h2>
        <p className="text-gray-500 text-center py-8">No hay facturas para mostrar</p>
      </div>
    );
  }

  // Formatear fecha
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('es-ES', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  // Formatear moneda
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="bg-white rounded-2xl shadow-header p-6">
      <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900 mb-3 sm:mb-4">
        Todas las Facturas ({facturas.length})
      </h2>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="text-left py-2 sm:py-3 px-2 sm:px-4 text-xs sm:text-sm md:text-base font-semibold text-gray-700">Proveedor</th>
              <th className="text-left py-2 sm:py-3 px-2 sm:px-4 text-xs sm:text-sm md:text-base font-semibold text-gray-700 whitespace-nowrap">Fecha</th>
              <th className="text-right py-2 sm:py-3 px-2 sm:px-4 text-xs sm:text-sm md:text-base font-semibold text-gray-700 whitespace-nowrap">Impuestos</th>
              <th className="text-right py-2 sm:py-3 px-2 sm:px-4 text-xs sm:text-sm md:text-base font-semibold text-gray-700 whitespace-nowrap">Total</th>
            </tr>
          </thead>
          <tbody>
            {facturas.map((factura) => (
              <tr 
                key={factura.id} 
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="py-2.5 sm:py-3 lg:py-4 px-2 sm:px-4">
                  <div className="text-xs sm:text-sm md:text-base text-gray-900 break-words max-w-[150px] sm:max-w-[200px] md:max-w-none">
                    {factura.proveedor_nombre || 'N/A'}
                  </div>
                </td>
                <td className="py-2.5 sm:py-3 lg:py-4 px-2 sm:px-4 text-xs sm:text-sm md:text-base text-gray-600 whitespace-nowrap">
                  {formatDate(factura.fecha_emision)}
                </td>
                <td className="py-2.5 sm:py-3 lg:py-4 px-2 sm:px-4 text-right text-xs sm:text-sm md:text-base text-gray-700 whitespace-nowrap">
                  {formatCurrency(factura.impuestos_total || 0)}
                </td>
                <td className="py-2.5 sm:py-3 lg:py-4 px-2 sm:px-4 text-right text-xs sm:text-sm md:text-base font-semibold text-gray-900 whitespace-nowrap">
                  {formatCurrency(factura.importe_total || 0)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

