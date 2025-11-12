import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { sanitizeErrorMessage } from '../utils/api';

/**
 * Componente para mostrar tabla de todas las facturas del mes y facturas no procesadas
 */
export function FacturasTable({ facturas = [], failedInvoices = [], loading = false }) {
  const [activeTab, setActiveTab] = useState('todas');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-header p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-12 bg-gray-100 rounded"></div>
            <div className="h-12 bg-gray-100 rounded"></div>
            <div className="h-12 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // Formatear fecha
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('es-ES', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  // Formatear moneda
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
    }).format(amount);
  };


  // Función para ordenar
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Ordenar facturas
  const sortedFacturas = useMemo(() => {
    if (!sortConfig.key) return facturas;
    
    return [...facturas].sort((a, b) => {
      let aValue, bValue;
      
      if (sortConfig.key === 'fecha') {
        aValue = a.fecha_emision ? new Date(a.fecha_emision).getTime() : 0;
        bValue = b.fecha_emision ? new Date(b.fecha_emision).getTime() : 0;
      } else if (sortConfig.key === 'impuestos') {
        aValue = parseFloat(a.impuestos_total || 0);
        bValue = parseFloat(b.impuestos_total || 0);
      } else if (sortConfig.key === 'total') {
        aValue = parseFloat(a.importe_total || 0);
        bValue = parseFloat(b.importe_total || 0);
      } else {
        return 0;
      }
      
      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [facturas, sortConfig]);

  // Renderizar botón de ordenamiento
  const SortButton = ({ columnKey, children }) => {
    const isActive = sortConfig.key === columnKey;
    return (
      <button
        onClick={() => handleSort(columnKey)}
        className="flex items-center justify-center gap-1 hover:text-gray-900 transition-colors mx-auto"
      >
        {children}
        {isActive ? (
          sortConfig.direction === 'asc' ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )
        ) : (
          <div className="w-4 h-4 flex flex-col">
            <ChevronUp className="w-2 h-2 text-gray-400" />
            <ChevronDown className="w-2 h-2 text-gray-400 -mt-1" />
          </div>
        )}
      </button>
    );
  };

  // Sanitizar las razones de las facturas pendientes antes de renderizar
  const facturasPendientes = useMemo(() => {
    const sanitized = (failedInvoices || []).map(invoice => {
      // Asegurar que razon sea una cadena antes de sanitizar
      const originalRazon = invoice.razon ? String(invoice.razon) : '';
      const sanitizedRazon = originalRazon ? sanitizeErrorMessage(originalRazon) : '';
      
      // Debug: verificar si la sanitización cambió el valor
      if (originalRazon && originalRazon !== sanitizedRazon) {
        console.log('🔄 Razón sanitizada:', 
          'Original:', originalRazon.substring(0, 50) + '...',
          'Sanitizado:', sanitizedRazon
        );
      }
      
      return {
        ...invoice,
        razon: sanitizedRazon || 'Sin razón especificada'
      };
    });
    console.log('🔧 Facturas pendientes sanitizadas:', sanitized.length);
    return sanitized;
  }, [failedInvoices]);

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-header p-4 sm:p-6 ipad:p-8">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        <button
          onClick={() => setActiveTab('todas')}
          className={`px-4 py-2 text-sm sm:text-base font-medium transition-colors ${
            activeTab === 'todas'
              ? 'border-b-2 border-purple-500 text-purple-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Todas ({facturas.length})
        </button>
        <button
          onClick={() => setActiveTab('pendientes')}
          className={`px-4 py-2 text-sm sm:text-base font-medium transition-colors ${
            activeTab === 'pendientes'
              ? 'border-b-2 border-purple-500 text-purple-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Pendientes ({facturasPendientes.length})
        </button>
      </div>

      {/* Tabla de facturas */}
      {activeTab === 'todas' ? (
        <>
          {!facturas || facturas.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No hay facturas para mostrar</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-3 px-4 md:px-6 ipad:px-8 text-sm font-semibold text-gray-700">PROVEEDOR</th>
                    <th className="text-center py-3 px-4 md:px-6 ipad:px-8 text-sm font-semibold text-gray-700">
                      <SortButton columnKey="fecha">FECHA</SortButton>
                    </th>
                    <th className="text-right py-3 px-4 md:px-6 ipad:px-8 text-sm font-semibold text-gray-700">
                      <SortButton columnKey="total">TOTAL</SortButton>
                    </th>
                    <th className="text-center py-3 px-4 md:px-6 ipad:px-8 text-sm font-semibold text-gray-700">ESTADO</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedFacturas.map((factura) => (
                    <tr 
                      key={factura.id} 
                      className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 px-4 md:px-6 ipad:px-8">
                        <div className="text-sm font-medium text-gray-900">
                          {factura.proveedor_nombre || 'N/A'}
                        </div>
                      </td>
                      <td className="py-3 px-4 md:px-6 ipad:px-8 text-center text-sm text-gray-600 whitespace-nowrap">
                        {formatDate(factura.fecha_emision)}
                      </td>
                      <td className="py-3 px-4 md:px-6 ipad:px-8 text-right text-sm font-semibold text-gray-900 whitespace-nowrap">
                        {formatCurrency(factura.importe_total || 0)}
                      </td>
                      <td className="py-3 px-4 md:px-6 ipad:px-8 text-center">
                        <span className="inline-flex items-center justify-center">
                          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : (
        <>
          {facturasPendientes.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No hay facturas pendientes de revisión</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-3 px-4 md:px-6 ipad:px-8 text-sm font-semibold text-gray-700">FACTURA</th>
                    <th className="text-left py-3 px-4 md:px-6 ipad:px-8 text-sm font-semibold text-gray-700">RAZÓN</th>
                  </tr>
                </thead>
                <tbody>
                  {facturasPendientes.map((invoice, index) => (
                    <tr
                      key={index}
                      className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 px-4 md:px-6 ipad:px-8">
                        <span className="text-sm font-medium text-gray-900 break-words">{invoice.nombre}</span>
                      </td>
                      <td className="py-3 px-4 md:px-6 ipad:px-8">
                        <span className="text-sm text-gray-600 break-words">
                          {invoice.razon || 'Sin razón especificada'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
