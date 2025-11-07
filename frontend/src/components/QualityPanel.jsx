import React from 'react';
import { formatNumber } from '../utils/formatters';

export function QualityPanel({ quality }) {
  if (!quality) return null;

  const metrics = [
    {
      label: 'Procesadas exitosamente',
      detail: quality.exitosas > 0 ? '100% de tasa de éxito' : 'Sin facturas exitosas',
      value: `${formatNumber(quality.exitosas)} ${quality.exitosas > 0 ? '✅' : '❌'}`,
      badgeClass: quality.exitosas > 0 
        ? 'bg-green-100 text-green-700' 
        : 'bg-red-100 text-red-700'
    },
    {
      label: 'Fallidas / Corruptas',
      detail: quality.fallidas > 0 ? 'Requieren revisión manual' : 'Sin facturas fallidas',
      value: `${formatNumber(quality.fallidas)} ⚠️`,
      badgeClass: quality.fallidas > 0
        ? 'bg-yellow-100 text-yellow-700'
        : 'bg-green-100 text-green-700'
    },
    {
      label: 'Confianza extracción',
      detail: 'Nivel de precisión promedio',
      value: `${quality.confianza.toFixed(1)}% 🎯`,
      valueClass: 'text-green-600 font-bold'
    }
  ];

  return (
    <div className="bg-white rounded-[20px] shadow-header p-4 sm:p-6 lg:p-8">
      <h3 className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-900 mb-3 sm:mb-4 lg:mb-6">
        ⚙️ Calidad del Procesamiento
      </h3>

      <div className="space-y-3 sm:space-y-4">
        {metrics.map((metric, index) => (
          <div
            key={index}
            className={`flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:gap-4 py-3 sm:py-4 ${
              index < metrics.length - 1 ? 'border-b border-gray-100' : ''
            }`}
          >
            <div className="flex-1 w-full sm:w-auto min-w-0">
              <div className="font-semibold text-sm sm:text-base md:text-lg text-gray-900 mb-1 break-words">
                {metric.label}
              </div>
              <div className="text-xs sm:text-sm text-gray-600 break-words">
                {metric.detail}
              </div>
            </div>
            <div className="ml-0 sm:ml-4 self-end sm:self-auto flex-shrink-0">
              {metric.badgeClass ? (
                <span className={`inline-block px-2 sm:px-3 py-1 rounded-full text-sm sm:text-base font-semibold whitespace-nowrap ${metric.badgeClass}`}>
                  {metric.value}
                </span>
              ) : (
                <span className={`text-sm sm:text-base md:text-lg whitespace-nowrap ${metric.valueClass || 'text-purple-600 font-bold'}`}>
                  {metric.value}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

