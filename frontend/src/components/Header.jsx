import React, { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, Calendar, ChevronDown } from 'lucide-react';
import { MONTH_NAMES } from '../utils/constants';

export function Header({ selectedMonth, selectedYear, onMonthChange, onYearChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  // Convertir selectedMonth (1-12) a índice (0-11) para el componente
  const currentMonthIndex = selectedMonth - 1;

  const handleMonthSelect = (monthIndex) => {
    // monthIndex es 0-11, convertir a 1-12 para el estado
    onMonthChange(monthIndex + 1);
    setIsOpen(false);
  };

  const handleYearChange = (increment) => {
    onYearChange(selectedYear + increment);
  };

  return (
    <div className="bg-white border-b border-gray-200 rounded-[20px] shadow-header p-1.5 sm:p-2 md:p-3 lg:p-4 mb-2 sm:mb-3 lg:mb-4">
      {/* Header con título a la izquierda y selector a la derecha */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-3">
        {/* Título a la izquierda */}
        <div className="flex-1">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 break-words">
            🧾 Dashboard de Facturación
          </h1>
        </div>

        {/* Componente compacto de selección de mes/año - A la derecha (50% más pequeño) */}
        <div className="relative" ref={dropdownRef}>
          {/* Calendario Principal - Compacto y más pequeño (50% del tamaño original) */}
          <div 
            className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg shadow-lg overflow-hidden cursor-pointer w-40 border border-slate-700 transition-all hover:shadow-blue-500/10 hover:shadow-xl"
            onClick={() => setIsOpen(!isOpen)}
          >
            {/* Header con iconos */}
            <div className="px-3 py-2 flex items-center justify-between border-b border-slate-700">
              <Calendar className="text-blue-400" size={16} />
              <ChevronDown 
                className={`text-slate-400 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} 
                size={14} 
              />
            </div>
            
            {/* Display de fecha */}
            <div className="px-3 py-3 text-center">
              <div className="text-lg font-light text-white mb-0.5 tracking-tight">
                {MONTH_NAMES[currentMonthIndex]}
              </div>
              <div className="text-base font-bold text-blue-400">
                {selectedYear}
              </div>
            </div>
            
            {/* Línea decorativa inferior */}
            <div className="h-0.5 bg-gradient-to-r from-blue-500 via-blue-400 to-blue-500"></div>
          </div>

          {/* Dropdown Selector */}
          {isOpen && (
          <div className="absolute top-full mt-2 right-0 bg-slate-900 rounded-lg shadow-2xl overflow-hidden z-50 border border-slate-700 w-48 animate-[fadeIn_0.3s_ease-out]">
            {/* Selector de año */}
            <div className="bg-slate-800 px-4 py-3 flex items-center justify-between border-b border-slate-700">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleYearChange(-1);
                }}
                className="p-1.5 hover:bg-slate-700 rounded transition-all text-white hover:scale-110"
                aria-label="Año anterior"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm font-semibold text-white">{selectedYear}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleYearChange(1);
                }}
                className="p-1.5 hover:bg-slate-700 rounded transition-all text-white hover:scale-110"
                aria-label="Año siguiente"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            {/* Grid de meses */}
            <div className="grid grid-cols-3 gap-2 p-3">
              {MONTH_NAMES.map((month, index) => (
                <button
                  key={month}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleMonthSelect(index);
                  }}
                  className={`py-2 px-1.5 rounded text-xs font-medium transition-all duration-200 ${
                    index === currentMonthIndex
                      ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/50 scale-105'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 hover:scale-105'
                  }`}
                  aria-label={`Seleccionar ${month}`}
                  aria-pressed={index === currentMonthIndex}
                >
                  {month.slice(0, 3)}
                </button>
              ))}
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  );
}

