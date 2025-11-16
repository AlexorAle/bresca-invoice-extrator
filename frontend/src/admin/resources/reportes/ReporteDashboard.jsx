/**
 * Dashboard de Reportes - React-admin
 * Migrado completamente desde Dashboard.jsx manteniendo diseño original
 */
import React, { useState } from 'react';
import { Box } from '@mui/material';
import { Header } from '../../../components/Header';
import { KPIGrid } from '../../../components/KPIGrid';
import { FacturasTable } from '../../../components/FacturasTable';
import { LoadingSpinner } from '../../../components/LoadingSpinner';
import { useInvoiceData } from '../../../hooks/useInvoiceData';
import { sanitizeErrorMessage } from '../../../utils/api';

/**
 * Dashboard principal de reportes - Diseño original preservado
 */
export const ReporteDashboard = () => {
  // Mes por defecto: julio (7) donde están las facturas procesadas
  const [selectedMonth, setSelectedMonth] = useState(7); // Julio por defecto
  const [selectedYear, setSelectedYear] = useState(2025);

  const { data, loading, error } = useInvoiceData(selectedMonth, selectedYear);

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
      <div className="min-h-screen bg-white flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="bg-white rounded-2xl shadow-header p-6 sm:p-8 max-w-md text-center mx-4">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Error de Conexión</h2>
          <p className="text-lg text-gray-600 mb-4 break-words">{errorMessage}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-gradient-active text-white px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition-all text-lg"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

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
          <Header 
            selectedMonth={selectedMonth}
            selectedYear={selectedYear}
            onMonthChange={setSelectedMonth}
            onYearChange={setSelectedYear}
          />

          {loading ? (
            <LoadingSpinner />
          ) : (
            <>
              <KPIGrid data={data?.kpis} loading={loading} />
              <div className="mt-4 sm:mt-6">
                <FacturasTable 
                  facturas={data?.allFacturas} 
                  failedInvoices={data?.failedInvoices}
                  loading={loading}
                  showTabs={false}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </Box>
  );
};
