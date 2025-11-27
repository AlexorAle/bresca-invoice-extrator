/**
 * Página de Pendientes - React-admin
 * Muestra la tabla de facturas pendientes
 */
import React from 'react';
import { List } from 'react-admin';
import { Box, Typography, Button } from '@mui/material';
import { FacturasTable } from '../../../components/FacturasTable';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { useInvoiceData } from '../../../hooks/useInvoiceData';
import DownloadIcon from '@mui/icons-material/Download';

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
      const url = `${apiBaseUrl}/facturas/export/excel?month=${selectedMonth}&year=${selectedYear}`;
      
      const response = await fetch(url);
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

  return (
    <List {...props} title="Facturas Pendientes" empty={false} actions={false}>
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#f9fafb',
        padding: 0,
        margin: 0,
      }}
    >
      <div className="p-2 sm:p-4 md:p-6 lg:p-8">
        <div className="mx-auto px-3 sm:px-4 md:px-5 lg:px-6">
          {/* Header */}
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography
              variant="h3"
              sx={{
                fontFamily: "'Inter', 'Outfit', sans-serif",
                fontWeight: 700,
                fontSize: '2rem',
                color: '#1e293b',
              }}
            >
              Facturas Pendientes
            </Typography>
            {/* Botón de exportación a Excel */}
            <Button
              onClick={handleExportExcel}
              variant="contained"
              startIcon={<DownloadIcon />}
              sx={{
                backgroundColor: '#10b981',
                color: '#ffffff',
                fontWeight: 600,
                padding: '10px 20px',
                borderRadius: '8px',
                textTransform: 'none',
                '&:hover': {
                  backgroundColor: '#059669',
                },
              }}
            >
              Exportar a Excel
            </Button>
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
        </div>
      </div>
    </Box>
    </List>
  );
};
