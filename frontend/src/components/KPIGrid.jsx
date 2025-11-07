import React from 'react';
import { KPICard } from './KPICard';

export function KPIGrid({ data, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6 lg:mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl shadow-card animate-pulse">
            <div className="w-12 h-12 bg-gray-200 rounded-xl mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-32 mb-4"></div>
            <div className="h-6 bg-gray-200 rounded w-20"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!data) return null;

  const kpis = [
    {
      icon: '📊',
      value: `${data.facturas.actual || 0}/${data.facturas.total || 0}`,
      label: 'Facturas del Mes',
      change: data.facturas.cambio,
      background: '#dbeafe',
      type: 'number'
    },
    {
      icon: '💰',
      value: data.importe.valor,
      label: 'Importe Total',
      change: data.importe.cambio,
      background: '#dcfce7',
      type: 'currency'
    },
    {
      icon: '📈',
      value: data.promedio.valor,
      label: 'Promedio por Factura',
      change: data.promedio.cambio,
      background: '#fef3c7',
      type: 'currency'
    },
    {
      icon: '👥',
      value: data.proveedores.cantidad,
      label: 'Proveedores Únicos',
      change: data.proveedores.cambio,
      background: '#e9d5ff',
      type: 'number'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6 lg:mb-8">
      {kpis.map((kpi, index) => (
        <KPICard key={index} {...kpi} />
      ))}
    </div>
  );
}

