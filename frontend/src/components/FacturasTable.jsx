import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Edit, FileText } from 'lucide-react';
import { sanitizeErrorMessage } from '../utils/api';
import { ManualInvoiceForm } from './ManualInvoiceForm';

/**
 * Componente para mostrar tabla de todas las facturas del mes y facturas no procesadas
 */
export function FacturasTable({ facturas = [], failedInvoices = [], loading = false, showTabs = true, showOnlyPendientes = false, onRefresh }) {
  const [activeTab, setActiveTab] = useState('todas');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

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

  // Categorizar estado basado en la razón del error
  const getEstadoFromRazon = (razon) => {
    if (!razon) return { texto: 'Sin clasificar', color: 'gray' };
    
    const razonLower = razon.toLowerCase();
    
    // Archivo corrupto
    if (razonLower.includes('archivo inválido') || razonLower.includes('archivo corrupto') || razonLower.includes('corrupt')) {
      return { texto: 'Archivo corrupto', color: 'red' };
    }
    
    // Error técnico (BD, constraints, etc.)
    if (razonLower.includes('checkviolation') || razonLower.includes('error técnico') || razonLower.includes('database') || razonLower.includes('constraint')) {
      return { texto: 'Error técnico', color: 'gray' };
    }
    
    // Datos faltantes (proveedor no encontrado, etc.)
    if (razonLower.includes('proveedor') || razonLower.includes('emisor') || razonLower.includes('no encontrado') || razonLower.includes('faltante')) {
      return { texto: 'Datos faltantes', color: 'gray' };
    }
    
    // Por defecto
    return { texto: 'Sin clasificar', color: 'gray' };
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
        className="flex items-center justify-center gap-2 transition-colors mx-auto"
        style={{ color: '#1e293b' }}
      >
        {children}
        {isActive ? (
          sortConfig.direction === 'asc' ? (
            <ChevronUp className="w-4 h-4" style={{ color: '#3b82f6' }} />
          ) : (
            <ChevronDown className="w-4 h-4" style={{ color: '#3b82f6' }} />
          )
        ) : (
          <div className="w-4 h-4 flex flex-col">
            <ChevronUp className="w-2 h-2" style={{ color: '#64748b', opacity: 0.5 }} />
            <ChevronDown className="w-2 h-2 -mt-1" style={{ color: '#64748b', opacity: 0.5 }} />
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
    <div 
      className="rounded-2xl p-8 overflow-x-auto"
      style={{
        backgroundColor: '#ffffff', // Tarjetas/Cards
        boxShadow: '0 4px 12px rgba(30, 58, 138, 0.08)', // Sombra Cards
      }}
    >
      {/* Tabs - Solo mostrar si showTabs es true y no es solo pendientes */}
      {showTabs && !showOnlyPendientes && (
        <div className="flex border-b border-gray-200 mb-4">
          <button
            onClick={() => setActiveTab('todas')}
            className={`px-5 py-3 text-base sm:text-lg font-medium transition-colors ${
              activeTab === 'todas'
                ? 'border-b-2 border-purple-500 text-purple-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Todas ({facturas.length})
          </button>
          <button
            onClick={() => setActiveTab('pendientes')}
            className={`px-5 py-3 text-base sm:text-lg font-medium transition-colors ${
              activeTab === 'pendientes'
                ? 'border-b-2 border-purple-500 text-purple-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Pendientes ({facturasPendientes.length})
          </button>
        </div>
      )}

      {/* Tabla de facturas */}
      {showOnlyPendientes ? (
        // Mostrar solo pendientes
        <>
          {facturasPendientes.length === 0 ? (
            <p className="text-gray-500 text-center py-8 text-lg">No hay facturas pendientes de revisión</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-5 px-5 md:px-7 ipad:px-9 font-semibold text-gray-700" style={{ fontSize: '0.875rem' }}>FACTURA</th>
                    <th className="text-center py-5 px-5 md:px-7 ipad:px-9 font-semibold text-gray-700" style={{ fontSize: '0.875rem' }}>ESTADO</th>
                    <th className="text-left py-5 px-5 md:px-7 ipad:px-9 font-semibold text-gray-700" style={{ fontSize: '0.875rem' }}>RAZÓN</th>
                    <th className="text-center py-5 px-5 md:px-7 ipad:px-9 font-semibold text-gray-700" style={{ fontSize: '0.875rem' }}>ACCIONES</th>
                  </tr>
                </thead>
                <tbody>
                  {facturasPendientes.map((invoice, index) => {
                    const estado = getEstadoFromRazon(invoice.razon);
                    return (
                      <tr
                        key={index}
                        className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                      >
                        <td className="py-5 px-5 md:px-7 ipad:px-9">
                          <div className="flex items-center gap-3">
                            <FileText size={20} className="text-gray-400 flex-shrink-0" />
                            <span className="font-medium text-gray-900 break-words" style={{ fontSize: '0.9375rem' }}>{invoice.nombre}</span>
                          </div>
                        </td>
                        <td className="py-5 px-5 md:px-7 ipad:px-9 text-center">
                          <span
                            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                              estado.color === 'red'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {estado.texto}
                          </span>
                        </td>
                        <td className="py-5 px-5 md:px-7 ipad:px-9">
                          <span className="text-gray-600 break-words" style={{ fontSize: '0.9375rem' }}>
                            {invoice.razon || 'Sin razón especificada'}
                          </span>
                        </td>
                        <td className="py-5 px-5 md:px-7 ipad:px-9 text-center">
                          <button
                            onClick={() => {
                              setSelectedInvoice(invoice);
                              setIsEditModalOpen(true);
                            }}
                            className="inline-flex items-center justify-center p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                            title="Editar factura manualmente"
                          >
                            <Edit size={18} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      ) : activeTab === 'todas' ? (
        <>
          {!facturas || facturas.length === 0 ? (
            <p className="text-gray-500 text-center py-8 text-lg">No hay facturas para mostrar</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-5 px-5 md:px-7 ipad:px-9 font-semibold" style={{ color: '#1e293b', fontSize: '0.875rem' }}>PROVEEDOR</th>
                    <th className="text-center py-5 px-5 md:px-7 ipad:px-9 font-semibold" style={{ color: '#1e293b', fontSize: '0.875rem' }}>
                      <SortButton columnKey="fecha">FECHA</SortButton>
                    </th>
                    <th className="text-center py-5 px-5 md:px-7 ipad:px-9 font-semibold" style={{ color: '#1e293b', fontSize: '0.875rem' }}>
                      <SortButton columnKey="total">TOTAL</SortButton>
                    </th>
                    <th className="text-center py-5 px-5 md:px-7 ipad:px-9 font-semibold" style={{ color: '#1e293b', fontSize: '0.875rem' }}>ESTADO</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedFacturas.map((factura) => (
                    <tr 
                      key={factura.id}
                      className="border-b border-gray-200 transition-all duration-200"
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(37, 99, 235, 0.04)'; // Fondo Hover Fila
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(37, 99, 235, 0.08)'; // Sombra Hover Fila
                        // Cambiar color de texto en hover
                        const tds = e.currentTarget.querySelectorAll('td');
                        tds.forEach(td => {
                          if (td.querySelector('span.w-3') === null) { // No cambiar el badge
                            td.style.color = '#3b82f6'; // Color Texto Hover
                          }
                        });
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = '#ffffff';
                        e.currentTarget.style.boxShadow = 'none';
                        // Restaurar color de texto
                        const tds = e.currentTarget.querySelectorAll('td');
                        tds.forEach(td => {
                          if (td.querySelector('span.w-3') === null) { // No cambiar el badge
                            td.style.color = '#1e293b'; // Texto Principal
                          }
                        });
                      }}
                    >
                      <td className="py-5 px-5 md:px-7 ipad:px-9 font-medium" style={{ color: '#1e293b', fontSize: '0.9375rem' }}>
                        {factura.proveedor_nombre || 'N/A'}
                      </td>
                      <td className="py-5 px-5 md:px-7 ipad:px-9 text-center whitespace-nowrap" style={{ color: '#1e293b', fontSize: '0.9375rem' }}>
                        {formatDate(factura.fecha_emision)}
                      </td>
                      <td className="py-5 px-5 md:px-7 ipad:px-9 text-center font-semibold whitespace-nowrap" style={{ color: '#1e293b', fontSize: '0.9375rem' }}>
                        {formatCurrency(factura.importe_total || 0)}
                      </td>
                      <td className="py-5 px-5 md:px-7 ipad:px-9 text-center">
                        <span 
                          className="inline-flex items-center justify-center transition-all duration-200"
                          onMouseEnter={(e) => {
                            e.currentTarget.style.boxShadow = '0 0 6px #2563eb'; // Badge Glow Hover
                            e.currentTarget.style.transform = 'scale(1.3)'; // Transform Badge
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.boxShadow = 'none';
                            e.currentTarget.style.transform = 'scale(1)';
                          }}
                        >
                          <span className="w-3 h-3 bg-green-500 rounded-full"></span>
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
            <p className="text-center py-8 text-lg" style={{ color: '#64748b' }}>No hay facturas pendientes de revisión</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-5 px-5 md:px-7 ipad:px-9 font-semibold" style={{ color: '#1e293b', fontSize: '0.875rem' }}>FACTURA</th>
                    <th className="text-center py-5 px-5 md:px-7 ipad:px-9 font-semibold" style={{ color: '#1e293b', fontSize: '0.875rem' }}>ESTADO</th>
                    <th className="text-left py-5 px-5 md:px-7 ipad:px-9 font-semibold" style={{ color: '#1e293b', fontSize: '0.875rem' }}>RAZÓN</th>
                    <th className="text-center py-5 px-5 md:px-7 ipad:px-9 font-semibold" style={{ color: '#1e293b', fontSize: '0.875rem' }}>ACCIONES</th>
                  </tr>
                </thead>
                <tbody>
                  {facturasPendientes.map((invoice, index) => {
                    const estado = getEstadoFromRazon(invoice.razon);
                    return (
                      <tr
                        key={index}
                        className="border-b border-gray-200 transition-all duration-200"
                        style={{
                          transform: 'scale(1)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(37, 99, 235, 0.04)'; // Fondo Hover Fila
                          e.currentTarget.style.boxShadow = '0 2px 8px rgba(37, 99, 235, 0.08)'; // Sombra Hover Fila
                          // Cambiar color de texto en hover
                          const tds = e.currentTarget.querySelectorAll('td');
                          tds.forEach(td => {
                            const badge = td.querySelector('span.inline-flex');
                            const button = td.querySelector('button');
                            if (!badge && !button) {
                              td.style.color = '#3b82f6'; // Color Texto Hover
                            }
                          });
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = '#ffffff';
                          e.currentTarget.style.boxShadow = 'none';
                          // Restaurar color de texto
                          const tds = e.currentTarget.querySelectorAll('td');
                          tds.forEach(td => {
                            const badge = td.querySelector('span.inline-flex');
                            const button = td.querySelector('button');
                            if (!badge && !button) {
                              td.style.color = '#1e293b'; // Texto Principal
                            }
                          });
                        }}
                      >
                        <td className="py-5 px-5 md:px-7 ipad:px-9 font-medium" style={{ color: '#1e293b', fontSize: '0.9375rem' }}>
                          <div className="flex items-center gap-3">
                            <FileText size={20} className="flex-shrink-0" style={{ color: '#64748b' }} />
                            <span className="break-words">{invoice.nombre}</span>
                          </div>
                        </td>
                        <td className="py-5 px-5 md:px-7 ipad:px-9 text-center">
                          <span
                            className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium transition-all duration-200"
                            style={{
                              backgroundColor: estado.color === 'red' ? '#fee2e2' : '#f1f5f9',
                              color: estado.color === 'red' ? '#dc2626' : '#475569',
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.boxShadow = '0 0 6px #2563eb'; // Badge Glow Hover
                              e.currentTarget.style.transform = 'scale(1.3)'; // Transform Badge
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.boxShadow = 'none';
                              e.currentTarget.style.transform = 'scale(1)';
                            }}
                          >
                            {estado.texto}
                          </span>
                        </td>
                        <td className="py-5 px-5 md:px-7 ipad:px-9" style={{ color: '#1e293b', fontSize: '0.9375rem' }}>
                          <span className="break-words">
                            {invoice.razon || 'Sin razón especificada'}
                          </span>
                        </td>
                        <td className="py-5 px-5 md:px-7 ipad:px-9 text-center">
                          <button
                            onClick={() => {
                              setSelectedInvoice(invoice);
                              setIsEditModalOpen(true);
                            }}
                            className="inline-flex items-center justify-center p-2 rounded-lg transition-all duration-200"
                            style={{ color: '#64748b' }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.color = '#3b82f6';
                              e.currentTarget.style.backgroundColor = 'rgba(37, 99, 235, 0.08)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.color = '#64748b';
                              e.currentTarget.style.backgroundColor = 'transparent';
                            }}
                            title="Editar factura manualmente"
                          >
                            <Edit size={18} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Modal de edición manual */}
      <ManualInvoiceForm
        open={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setSelectedInvoice(null);
        }}
        invoice={selectedInvoice}
        onSuccess={(response) => {
          console.log('Factura guardada exitosamente:', response);
          // Refrescar datos si hay callback
          if (onRefresh) {
            onRefresh();
          } else {
            // Recargar página si no hay callback
            window.location.reload();
          }
        }}
      />
    </div>
  );
}
