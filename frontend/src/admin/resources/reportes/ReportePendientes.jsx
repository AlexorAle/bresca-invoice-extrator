/**
 * Página de Pendientes - React-admin
 * Muestra la tabla de facturas pendientes
 */
import React from 'react';
import { List } from 'react-admin';
import { Box, Typography } from '@mui/material';
import { FacturasTable } from '../../../components/FacturasTable';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { useInvoiceData } from '../../../hooks/useInvoiceData';

/**
 * Lista de facturas pendientes
 * Envuelto en List de React-admin para que el routing funcione correctamente
 */
export const ReportePendientes = (props) => {
  // Ignorar props de React-admin, usar nuestros datos
  // Mes por defecto: julio (7) donde están las facturas procesadas
  const selectedMonth = 7;
  const selectedYear = 2025;

  const { data, loading } = useInvoiceData(selectedMonth, selectedYear);

  return (
    <List {...props} title="Facturas Pendientes" empty={false}>
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
          <Box sx={{ mb: 4 }}>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                fontSize: '2rem',
                color: '#1f2937',
                mb: 1,
              }}
            >
              Facturas Pendientes
            </Typography>
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
            />
          )}
        </div>
      </div>
    </Box>
    </List>
  );
};
