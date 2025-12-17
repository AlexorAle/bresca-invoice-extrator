import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { KPIGrid } from './KPIGrid';
import { FacturasTable } from './FacturasTable';
import { LoadingSpinner } from './LoadingSpinner';
import { useInvoiceData } from '../hooks/useInvoiceData';
import { sanitizeErrorMessage } from '../utils/api';

export default function Dashboard() {
  // Cambiar mes por defecto a julio (7) donde están las facturas procesadas
  // En lugar de mes actual (noviembre) que tiene 0 facturas
  const [selectedMonth, setSelectedMonth] = useState(7); // Julio por defecto
  const [selectedYear, setSelectedYear] = useState(2025);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

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
    <div className="min-h-screen bg-white flex">
      {/* Sidebar */}
      <Sidebar 
        activeSection={activeSection} 
        onSectionChange={setActiveSection}
        onCollapseChange={setIsSidebarCollapsed}
      />

      {/* Main Content */}
      <div className={`flex-1 transition-all duration-300 ${isSidebarCollapsed ? 'ml-16' : 'ml-64'}`}>
        <div className="p-2 sm:p-4 md:p-6 lg:p-8">
          <div className="mx-auto px-3 sm:px-4 md:px-5 lg:px-6">
            {activeSection === 'dashboard' && (
              <>
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
              </>
            )}

            {activeSection === 'pendientes' && (
              <>
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
              </>
            )}

            {activeSection === 'reportes' && (
              <div className="bg-white rounded-2xl shadow-header p-6 sm:p-8">
                <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
                  Reportes
                </h2>
                <p className="text-gray-600">
                  Sección de reportes en desarrollo...
                </p>
              </div>
            )}

            {activeSection === 'datos' && (
              <div className="bg-white rounded-2xl shadow-header p-6 sm:p-8">
                <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
                  Datos
                </h2>
                <p className="text-gray-600">
                  Sección de carga de datos en desarrollo...
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

