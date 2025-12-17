/**
 * Header - Componente de header migrado completamente a MUI
 * Reemplazo de Header.jsx legacy (Tailwind + MUI mixto)
 */
import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Menu, MenuItem, IconButton, Paper } from '@mui/material';
import { ChevronLeft, ChevronRight, Calendar, ChevronDown } from 'lucide-react';
import { MONTH_NAMES } from '../../utils/constants';
import { PAGE_LAYOUT, COLORS, BORDER_RADIUS } from '../../admin/styles/designTokens';

export function Header({ selectedMonth, selectedYear, onMonthChange, onYearChange, compact = false }) {
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
    onMonthChange(monthIndex + 1);
    setIsOpen(false);
  };

  const handleYearChange = (increment) => {
    onYearChange(selectedYear + increment);
  };

  return (
    <Box sx={{ mb: compact ? 0 : 4 }}>
      {/* Si compact=false, mostrar layout completo con título */}
      {!compact && (
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
                color: COLORS.text.primary,
                margin: 0,
              }}
            >
              Dashboard de Facturación
            </Typography>
          </Box>
        </Box>
      )}

      {/* Componente compacto de selección de mes/año */}
      <Box sx={{ position: 'relative' }} ref={dropdownRef}>
        {/* Calendario Principal - MUI Paper */}
        <Paper
          onClick={() => setIsOpen(!isOpen)}
          sx={{
            background: 'linear-gradient(to bottom right, #0f172a, #1e293b)',
            borderRadius: BORDER_RADIUS.lg,
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            overflow: 'hidden',
            cursor: 'pointer',
            width: compact ? 'auto' : '160px',
            minWidth: compact ? '180px' : '160px',
            border: '1px solid #334155',
            transition: 'all 0.3s ease',
            '&:hover': {
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
              transform: compact ? 'scale(1.02)' : 'scale(1.05)',
            },
          }}
        >
            {/* Header con iconos */}
            <Box
              sx={{
                px: compact ? 1 : 1.5,
                py: compact ? 0.75 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid #334155',
              }}
            >
              <Calendar size={compact ? 14 : 16} color="#60a5fa" />
              <ChevronDown 
                size={compact ? 12 : 14} 
                color="#94a3b8"
                style={{
                  transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s ease',
                }}
              />
            </Box>
            
            {/* Display de fecha */}
            <Box sx={{ px: compact ? 1 : 1.5, py: compact ? 1 : 1.5, textAlign: 'center' }}>
              <Typography
                sx={{
                  fontSize: compact ? '0.975rem' : '18px',
                  fontWeight: 300,
                  color: '#ffffff',
                  mb: compact ? 0.25 : 0.5,
                  letterSpacing: '-0.5px',
                }}
              >
                {MONTH_NAMES[currentMonthIndex]}
              </Typography>
              <Typography
                sx={{
                  fontSize: compact ? '0.875rem' : '16px',
                  fontWeight: 700,
                  color: '#60a5fa',
                }}
              >
                {selectedYear}
              </Typography>
            </Box>
            
            {/* Línea decorativa inferior */}
            <Box
              sx={{
                height: '2px',
                background: 'linear-gradient(to right, #3b82f6, #60a5fa, #3b82f6)',
              }}
            />
          </Paper>

          {/* Dropdown Selector - MUI Menu */}
          <Menu
            open={isOpen}
            anchorEl={dropdownRef.current}
            onClose={() => setIsOpen(false)}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            PaperProps={{
              sx: {
                mt: 1,
                backgroundColor: '#0f172a',
                borderRadius: BORDER_RADIUS.lg,
                border: '1px solid #334155',
                width: '192px',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
              },
            }}
          >
            {/* Selector de año */}
            <Box
              sx={{
                backgroundColor: '#1e293b',
                px: 2,
                py: 1.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid #334155',
              }}
            >
              <IconButton
                onClick={(e) => {
                  e.stopPropagation();
                  handleYearChange(-1);
                }}
                size="small"
                sx={{
                  color: '#ffffff',
                  '&:hover': { backgroundColor: '#334155' },
                }}
                aria-label="Año anterior"
              >
                <ChevronLeft size={16} />
              </IconButton>
              <Typography sx={{ fontSize: '14px', fontWeight: 600, color: '#ffffff' }}>
                {selectedYear}
              </Typography>
              <IconButton
                onClick={(e) => {
                  e.stopPropagation();
                  handleYearChange(1);
                }}
                size="small"
                sx={{
                  color: '#ffffff',
                  '&:hover': { backgroundColor: '#334155' },
                }}
                aria-label="Año siguiente"
              >
                <ChevronRight size={16} />
              </IconButton>
            </Box>

            {/* Grid de meses */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 1,
                p: 1.5,
              }}
            >
              {MONTH_NAMES.map((month, index) => (
                <MenuItem
                  key={month}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleMonthSelect(index);
                  }}
                  selected={index === currentMonthIndex}
                  sx={{
                    py: 1,
                    px: 0.75,
                    borderRadius: BORDER_RADIUS.md,
                    fontSize: '12px',
                    fontWeight: 500,
                    textAlign: 'center',
                    justifyContent: 'center',
                    minHeight: 'auto',
                    backgroundColor: index === currentMonthIndex ? '#3b82f6' : '#1e293b',
                    color: index === currentMonthIndex ? '#ffffff' : '#cbd5e1',
                    border: `1px solid ${index === currentMonthIndex ? '#3b82f6' : '#334155'}`,
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      backgroundColor: index === currentMonthIndex ? '#2563eb' : '#334155',
                      borderColor: '#475569',
                      transform: 'scale(1.05)',
                    },
                    '&.Mui-selected': {
                      backgroundColor: '#3b82f6',
                      color: '#ffffff',
                      boxShadow: '0 4px 12px rgba(59, 130, 246, 0.5)',
                      '&:hover': {
                        backgroundColor: '#2563eb',
                      },
                    },
                  }}
                  aria-label={`Seleccionar ${month}`}
                >
                  {month.slice(0, 3)}
                </MenuItem>
              ))}
            </Box>
          </Menu>
        </Box>
    </Box>
  );
}
