import React, { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, Calendar, ChevronDown } from 'lucide-react';
import { Typography, Box } from '@mui/material';
import { MONTH_NAMES } from '../utils/constants';
import { PAGE_LAYOUT } from '../admin/styles/designTokens';

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
    <Box sx={{ mb: 4 }}>
      {/* Header con título a la izquierda y selector a la derecha */}
      <Box sx={{ 
        display: 'flex', 
        flexDirection: { xs: 'column', sm: 'row' },
        alignItems: { xs: 'flex-start', sm: 'center' },
        justifyContent: 'space-between',
        gap: { xs: 2, sm: 3 },
        mt: PAGE_LAYOUT.titleMarginTop,
        mb: 1,
      }}>
        {/* Título a la izquierda - Estilo normalizado igual que Reportes */}
        <Box sx={{ flex: 1 }}>
          <Typography
            variant="h3"
            sx={{
              fontFamily: "'Inter', 'Outfit', sans-serif",
              fontWeight: 700,
              fontSize: '2rem',
              color: '#1e293b',
              margin: 0,
            }}
          >
            Dashboard de Facturación
          </Typography>
        </Box>

        {/* Componente compacto de selección de mes/año - A la derecha (50% más pequeño) */}
        <Box sx={{ position: 'relative' }} ref={dropdownRef}>
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
          <Box sx={{ 
            position: 'absolute',
            top: '100%',
            mt: 2,
            right: 0,
            backgroundColor: '#0f172a',
            borderRadius: '8px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            overflow: 'hidden',
            zIndex: 50,
            border: '1px solid #334155',
            width: '192px',
          }}>
            {/* Selector de año */}
            <Box sx={{ 
              backgroundColor: '#1e293b',
              px: 2,
              py: 1.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #334155',
            }}>
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
            </Box>

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
          </Box>
        )}
        </Box>
      </Box>
    </Box>
  );
}

