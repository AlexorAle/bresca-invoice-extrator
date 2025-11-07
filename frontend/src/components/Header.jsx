import React from 'react';
import { MONTH_NAMES, MONTH_NAMES_SHORT } from '../utils/constants';

export function Header({ selectedMonth, selectedYear, onMonthChange, onYearChange }) {
  // Generar años desde 2020 hasta año actual + 1
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: currentYear - 2020 + 2 }, (_, i) => 2020 + i);

  return (
    <div className="bg-white rounded-[20px] shadow-header p-3 sm:p-4 md:p-6 lg:p-8 mb-4 sm:mb-6 lg:mb-8 flex flex-col">
      {/* Título en la parte superior */}
      <div className="mb-4 sm:mb-6">
        <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900 mb-1 sm:mb-2 break-words">
          🧾 Dashboard de Facturación
        </h1>
        <p className="text-xs sm:text-sm md:text-base text-gray-600">
          Vista mensual - Actualizado en tiempo real
        </p>
      </div>

      {/* Filtro del año centrado a la izquierda en el medio */}
      <div className="mb-4 sm:mb-6 flex justify-start items-center">
        <div className="year-selector">
          <select
            value={selectedYear}
            onChange={(e) => onYearChange(parseInt(e.target.value))}
            className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg bg-white border border-gray-200 text-sm sm:text-base font-medium text-gray-700 hover:border-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all duration-300 shadow-sm hover:shadow-md"
            aria-label="Seleccionar año"
          >
            {years.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Los doce meses del año en la parte inferior */}
      <div className="month-selector bg-gray-50 p-1.5 sm:p-2 rounded-xl mt-auto">
        <div className="flex gap-1.5 sm:gap-2 overflow-x-auto md:overflow-x-visible scrollbar-hide pb-1">
          {MONTH_NAMES_SHORT.map((month, index) => {
            const monthNumber = index + 1;
            const isActive = selectedMonth === monthNumber;

            return (
              <button
                key={monthNumber}
                onClick={() => onMonthChange(monthNumber)}
                aria-label={`Seleccionar ${MONTH_NAMES[index]}`}
                aria-pressed={isActive}
                className={`px-3 sm:px-4 md:px-5 py-2 sm:py-2.5 md:py-3 rounded-lg text-xs sm:text-sm md:text-base font-medium transition-all duration-300 min-w-[44px] sm:min-w-[50px] flex-shrink-0 ${
                  isActive
                    ? 'bg-gradient-active text-white shadow-button-active'
                    : 'text-gray-600 hover:bg-white hover:text-purple-600'
                }`}
              >
                {month}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

