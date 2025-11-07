import React from 'react';
import { formatCurrency, formatNumber } from '../utils/formatters';

export function CategoriesPanel({ categories }) {
  if (!categories || !Array.isArray(categories) || categories.length === 0) {
    return (
      <div className="bg-white rounded-[20px] shadow-header p-4 sm:p-6 lg:p-8 mb-4 sm:mb-6 lg:mb-8">
        <h3 className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-900 mb-3 sm:mb-4">
          📊 Desglose por Categorías
        </h3>
        <p className="text-sm sm:text-base text-gray-600">No hay datos disponibles</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-[20px] shadow-header p-4 sm:p-6 lg:p-8 mb-4 sm:mb-6 lg:mb-8">
      <h3 className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-900 mb-3 sm:mb-4 lg:mb-6">
        📊 Desglose por Categorías
      </h3>

      {/* Scroll horizontal mejorado para móvil */}
      <div className="overflow-x-auto -mx-4 sm:-mx-6 lg:mx-0 px-4 sm:px-6 lg:px-0">
        <div className="inline-block min-w-full align-middle">
          <table className="w-full min-w-[500px] sm:min-w-0">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="text-left py-2 sm:py-3 px-2 sm:px-4 text-gray-600 text-xs sm:text-sm md:text-base font-semibold">
                  Concepto
                </th>
                <th className="text-right py-2 sm:py-3 px-2 sm:px-4 text-gray-600 text-xs sm:text-sm md:text-base font-semibold whitespace-nowrap">
                  Cantidad
                </th>
                <th className="text-right py-2 sm:py-3 px-2 sm:px-4 text-gray-600 text-xs sm:text-sm md:text-base font-semibold whitespace-nowrap">
                  Importe
                </th>
              </tr>
            </thead>
            <tbody>
              {categories.map((category, index) => (
                <tr
                  key={index}
                  className={`${index < categories.length - 1 ? 'border-b border-gray-100' : ''} hover:bg-gray-50 transition-colors`}
                >
                  <td className="py-2.5 sm:py-3 lg:py-4 px-2 sm:px-4">
                    <div className="font-semibold text-xs sm:text-sm md:text-base text-gray-900 break-words max-w-[200px] sm:max-w-none">
                      {category.categoria || 'Sin proveedor'}
                    </div>
                  </td>
                  <td className="text-right py-2.5 sm:py-3 lg:py-4 px-2 sm:px-4 text-xs sm:text-sm md:text-base text-gray-900 whitespace-nowrap">
                    {formatNumber(category.cantidad)}
                  </td>
                  <td className="text-right py-2.5 sm:py-3 lg:py-4 px-2 sm:px-4 text-xs sm:text-sm md:text-base text-purple-600 font-bold whitespace-nowrap">
                    {formatCurrency(category.importe_total)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
