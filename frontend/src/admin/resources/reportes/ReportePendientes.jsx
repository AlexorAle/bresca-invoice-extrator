/**
 * Reporte de Facturas Pendientes - React-admin
 * Migrado desde sección "Pendientes" del Dashboard original
 */
import React from 'react';
import { Box } from '@mui/material';
import { FacturasTable } from '../../../components/FacturasTable';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { useInvoiceData } from '../../../hooks/useInvoiceData';

/**
 * Lista de facturas pendientes - Diseño original preservado
 */
export const ReportePendientes = () => {
  // Mes por defecto: julio (7) donde están las facturas procesadas
  const selectedMonth = 7;
  const selectedYear = 2025;

  const { data, loading } = useInvoiceData(selectedMonth, selectedYear);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: '#ffffff',
        padding: 0,
        margin: 0,
      }}
    >
      <div className="p-2 sm:p-4 md:p-6 lg:p-8">
        <div className="mx-auto px-3 sm:px-4 md:px-5 lg:px-6">
          <div className="bg-white rounded-2xl shadow-header p-5 sm:p-7 ipad:p-9 mb-4 sm:mb-6">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">
              Facturas Pendientes
            </h2>
          </div>
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
  );
};
