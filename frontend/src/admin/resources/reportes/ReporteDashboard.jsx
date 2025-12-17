/**
 * Facturas - Vista principal de facturas
 * Migrado completamente desde Dashboard.jsx manteniendo diseño original
 */
import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { Header } from '../../../components/ui/Header';
import { KPIGrid } from '../../../components/ui/KPIGrid';
import { FacturasTable } from '../../../components/ui/FacturasTable';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { useInvoiceData } from '../../../hooks/useInvoiceData';
import { sanitizeErrorMessage } from '../../../utils/api';
import DownloadIcon from '@mui/icons-material/Download';
import { SPACING, PAGE_LAYOUT, BUTTON_HEIGHTS, BORDER_RADIUS, TABLE_STYLES, COLORS } from '../../styles/designTokens';
import { BaseButton, BaseSection } from '../../../components/ui';

/**
 * Facturas - Vista principal de facturas - Diseño original preservado
 */
export const ReporteDashboard = () => {
  // Mes por defecto: julio (7) donde están las facturas procesadas
  const [selectedMonth, setSelectedMonth] = useState(7); // Julio por defecto
  const [selectedYear, setSelectedYear] = useState(2025);

  const { data, loading, error } = useInvoiceData(selectedMonth, selectedYear);

  const handleExportExcel = async () => {
    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/invoice-api/api';
      const url = `${apiBaseUrl}/facturas/export/excel?month=${selectedMonth}&year=${selectedYear}`;
      
      const response = await fetch(url, {
        credentials: 'include', // Importante: incluir cookies de sesión
      });
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const link = document.createElement('a');
      const url_blob = window.URL.createObjectURL(blob);
      link.href = url_blob;
      
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `Facturas_${selectedMonth}_${selectedYear}.xlsx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url_blob);
    } catch (error) {
      console.error('Error al exportar a Excel:', error);
      alert('Error al exportar a Excel. Por favor, intente nuevamente.');
    }
  };

  if (error) {
    // Formatear mensaje de error de forma legible
    let errorMessage = 'Error desconocido';
    if (typeof error === 'string') {
      errorMessage = error;
    } else if (error?.message) {
      errorMessage = error.message;
    } else if (Array.isArray(error)) {
      errorMessage = error.map(e => typeof e === 'string' ? e : e?.message || JSON.stringify(e)).join(', ');
    } else if (error && typeof error === 'object') {
      errorMessage = error.message || error.detail || JSON.stringify(error);
    }
    
    // Sanitizar el mensaje de error para ocultar detalles técnicos
    errorMessage = sanitizeErrorMessage(errorMessage);
    
    return (
      <Box
        sx={{
          minHeight: '100vh',
          backgroundColor: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: { xs: 4, sm: 6, lg: 8 },
        }}
      >
        <Box
          sx={{
            backgroundColor: '#ffffff',
            borderRadius: BORDER_RADIUS.xl,
            boxShadow: '0 20px 60px rgba(0,0,0,0.1)',
            p: { xs: 3, sm: 4, lg: 4 },
            maxWidth: '448px',
            textAlign: 'center',
            mx: 2,
          }}
        >
          <Typography sx={{ fontSize: '60px', mb: 2 }}>❌</Typography>
          <Typography
            variant="h2"
            sx={{
              fontSize: { xs: '24px', sm: '30px' },
              fontWeight: 700,
              color: COLORS.text.primary,
              mb: 1,
            }}
          >
            Error de Conexión
          </Typography>
          <Typography
            sx={{
              fontSize: '18px',
              color: COLORS.text.secondary,
              mb: 2,
              wordBreak: 'break-word',
            }}
          >
            {errorMessage}
          </Typography>
          <BaseButton
            onClick={() => window.location.reload()}
            variant="contained"
            sx={{
              backgroundColor: COLORS.primary.main,
              color: '#ffffff',
              fontSize: '18px',
              '&:hover': {
                backgroundColor: COLORS.primary.dark,
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
              },
            }}
          >
            Reintentar
          </BaseButton>
        </Box>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#f8fafc', // Fondo General
        padding: 0,
        margin: 0,
      }}
    >
      <Box 
        sx={{ 
          p: { xs: 2, sm: 4, md: 6, lg: 8 },
          backgroundColor: COLORS.background.default,
        }}
      >
        <Box sx={{ px: { xs: 2, md: 4 } }}>
          {/* Título principal con márgenes reducidos */}
          <Typography
            variant="h3"
            sx={{
              fontFamily: "'Inter', 'Outfit', sans-serif",
              fontWeight: 700,
              fontSize: '2rem',
              color: COLORS.text.primary,
              mt: 1.125, // Reducido 25% desde 1.5
              ml: { xs: 1.125, md: 2.25 }, // Reducido 25% desde 1.5 y 3
              mb: 3,
            }}
          >
            Facturas
          </Typography>

          {loading ? (
            <LoadingSpinner />
          ) : (
            <>
              {/* Grid de KPIs - Justo debajo del título */}
              <Box sx={{ mt: 2, px: { xs: 2, md: 4 } }}>
                <KPIGrid data={data?.kpis} loading={loading} />
              </Box>

              {/* Fila con Botón Exportar (izq) y Selector (der) */}
              <Box 
                sx={{ 
                  display: 'flex', 
                  flexDirection: { xs: 'column', sm: 'row' },
                  justifyContent: 'space-between', 
                  alignItems: { xs: 'stretch', sm: 'center' },
                  gap: { xs: 2, sm: 3 },
                  mt: 4,
                  px: { xs: 2, md: 4 },
                }}
              >
                {/* Botón Exportar a Excel - Izquierda */}
                <BaseButton
                  onClick={handleExportExcel}
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  sx={{
                    backgroundColor: '#10b981',
                    color: '#ffffff',
                    alignSelf: { xs: 'stretch', sm: 'flex-start' },
                    '&:hover': {
                      backgroundColor: '#059669',
                    },
                  }}
                >
                  Exportar a Excel
                </BaseButton>

                {/* Selector de mes/año - Derecha, tamaño reducido */}
                <Box sx={{ alignSelf: { xs: 'stretch', sm: 'flex-end' } }}>
                  <Header 
                    selectedMonth={selectedMonth}
                    selectedYear={selectedYear}
                    onMonthChange={setSelectedMonth}
                    onYearChange={setSelectedYear}
                    compact={true}
                  />
                </Box>
              </Box>

              {/* Tabla de facturas */}
              <BaseSection spacing="default" sx={{ mt: 4, px: { xs: 2, md: 4 } }}>
                <FacturasTable 
                  facturas={data?.allFacturas} 
                  failedInvoices={data?.failedInvoices}
                  loading={loading}
                  showTabs={false}
                />
              </BaseSection>
            </>
          )}
        </Box>
      </Box>
    </Box>
  );
};
