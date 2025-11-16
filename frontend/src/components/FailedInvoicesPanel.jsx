import React from 'react';

export function FailedInvoicesPanel({ failedInvoices }) {
  if (!failedInvoices || !Array.isArray(failedInvoices) || failedInvoices.length === 0) {
    return (
      <div className="bg-white rounded-[20px] shadow-header p-4 sm:p-6 lg:p-8">
        <h3 className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-900 mb-3 sm:mb-4 lg:mb-6">
          ⚠️ Facturas No Procesadas
        </h3>
        <p className="text-sm sm:text-base text-gray-600">✅ No hay facturas que requieran revisión</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-[20px] shadow-header p-4 sm:p-6 lg:p-8">
      <h3 className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-900 mb-2 sm:mb-3">
        ⚠️ Facturas No Procesadas
      </h3>
      <p className="text-xs sm:text-sm text-gray-600 mb-3 sm:mb-4 lg:mb-6">
        Archivos que requieren revisión manual (todas las facturas fallidas, sin filtro de mes)
      </p>

      <div className="space-y-2">
        {failedInvoices.map((invoice, index) => (
          <div
            key={index}
            className="py-2.5 sm:py-3 px-3 sm:px-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center">
              <span className="text-gray-400 mr-2 sm:mr-3">•</span>
              <span className="text-sm sm:text-base text-gray-900 font-medium break-words min-w-0">{invoice.nombre}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

