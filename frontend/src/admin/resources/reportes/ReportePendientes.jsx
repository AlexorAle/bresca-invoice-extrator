/**
 * Página de Pendientes - React-admin
 * Muestra la tabla de facturas pendientes
 */
import React from 'react';
import { List } from 'react-admin';
import { Box, Typography } from '@mui/material';
import { FacturasTable } from '../../../components/ui/FacturasTable';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { useInvoiceData } from '../../../hooks/useInvoiceData';
import DownloadIcon from '@mui/icons-material/Download';
import { SPACING, PAGE_LAYOUT, COLORS } from '../../styles/designTokens';
import { BaseButton, BaseSection } from '../../../components/ui';

/**
 * Lista de facturas pendientes
 * Envuelto en List de React-admin para que el routing funcione correctamente
 */
export const ReportePendientes = (props) => {
  // Ignorar props de React-admin, usar nuestros datos
  // Mes por defecto: julio (7) donde están las facturas procesadas
  const selectedMonth = 7;
  const selectedYear = 2025;

  const { data, loading, refetch } = useInvoiceData(selectedMonth, selectedYear);

  const handleRefresh = () => {
    if (refetch) {
      refetch();
    } else {
      window.location.reload();
    }
  };

  const handleExportExcel = async () => {
    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/invoice-api/api';
      // Usar endpoint específico para facturas pendientes (sin filtro de mes, trae TODAS)
      const url = `${apiBaseUrl}/facturas/export/excel/pendientes`;
      
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
      let filename = 'Facturas_Pendientes.xlsx';
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
      console.error('Error al exportar facturas pendientes a Excel:', error);
      alert('Error al exportar facturas pendientes a Excel. Por favor, intente nuevamente.');
    }
  };

  return (
    <List 
      {...props} 
      title="Facturas Pendientes" 
      empty={false} 
      actions={false}
      sx={{
        padding: '0 !important',
        margin: '0 !important',
        '& .RaList-main': {
          backgroundColor: '#f8fafc',
          paddingTop: '0 !important',
          paddingLeft: '0 !important',
          paddingRight: '0 !important',
          paddingBottom: '0 !important',
        },
        '& .RaList-content': {
          boxShadow: 'none',
          borderTop: 'none',
          padding: '0 !important',
        },
        '& .RaList-actions': {
          display: 'none',
          padding: '0 !important',
        },
      }}
    >
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: COLORS.background.subtle,
        padding: 0,
        margin: 0,
        '& > *': {
          borderTop: 'none !important',
        },
      }}
    >
      <Box sx={{ p: { xs: 1, sm: 2, md: 3, lg: 4 } }}>
        <Box sx={{ mx: 'auto', px: { xs: 1.5, sm: 2, md: 2.5, lg: 3 } }}>
          {/* Header - Sin margen superior */}
          <Box sx={{ 
            mt: PAGE_LAYOUT.titleMarginTop,
            mb: PAGE_LAYOUT.sectionSpacing,
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
          }}>
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
              Facturas Pendientes
            </Typography>
            {/* Botón de exportación a Excel */}
            <BaseButton
              onClick={handleExportExcel}
              variant="contained"
              startIcon={<DownloadIcon />}
              sx={{
                backgroundColor: '#10b981',
                color: '#ffffff',
                '&:hover': {
                  backgroundColor: '#059669',
                },
              }}
            >
              Exportar a Excel
            </BaseButton>
          </Box>

          {/* Tabla de facturas pendientes */}
          {loading ? (
            <LoadingSpinner />
          ) : (
            <FacturasTable 
              facturas={[]} 
              failedInvoices={data?.failedInvoices}
              loading={loading}
              showTabs={false}
              showOnlyPendientes={true}
              onRefresh={handleRefresh}
            />
          )}
        </Box>
      </Box>
    </Box>
    </List>
  );
};
