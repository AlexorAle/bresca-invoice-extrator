import React, { useState } from 'react';
import { Header } from './Header';
import { KPIGrid } from './KPIGrid';
import { CategoriesPanel } from './CategoriesPanel';
import { AnalysisGrid } from './AnalysisGrid';
import { FacturasTable } from './FacturasTable';
import { LoadingSpinner } from './LoadingSpinner';
import { useInvoiceData } from '../hooks/useInvoiceData';

export default function Dashboard() {
  // Cambiar mes por defecto a julio (7) donde están las facturas procesadas
  // En lugar de mes actual (noviembre) que tiene 0 facturas
  const [selectedMonth, setSelectedMonth] = useState(7); // Julio por defecto
  const [selectedYear, setSelectedYear] = useState(2025);

  const { data, loading, error } = useInvoiceData(selectedMonth, selectedYear);

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-dashboard flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="bg-white rounded-2xl shadow-header p-6 sm:p-8 max-w-md text-center mx-4">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Error de Conexión</h2>
          <p className="text-lg text-gray-600 mb-4">{error}</p>
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
    <div className="min-h-screen bg-gradient-dashboard p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto px-2 sm:px-4 md:px-6">
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
            <CategoriesPanel categories={data?.categories} />
            <AnalysisGrid 
              quality={data?.quality}
              failedInvoices={data?.failedInvoices}
            />
            <div className="mt-4 sm:mt-6">
              <FacturasTable 
                facturas={data?.allFacturas} 
                loading={loading}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

