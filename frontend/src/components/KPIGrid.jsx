import React from 'react';
import { KPICard } from './KPICard';

export function KPIGrid({ data, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 ipad:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 ipad:gap-4 lg:gap-6 mb-4 sm:mb-6 lg:mb-8">
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
      label: 'Facturas Procesadas',
      change: data.facturas.cambio,
      background: '#dbeafe', // Azul para el icono
      bgColor: 'bg-green-100', // Verde suave para el fondo
      textColor: 'text-green-800', // Verde oscuro para el texto
      type: 'number'
    },
    {
      icon: '💰',
      value: data.importe.valor,
      label: 'Importe del Mes',
      change: data.importe.cambio,
      background: '#dcfce7', // Verde para el icono
      bgColor: 'bg-emerald-100', // Verde claro para el fondo
      textColor: 'text-emerald-800', // Verde claro oscuro para el texto
      type: 'currency'
    },
    {
      icon: '📈',
      value: data.impuestos_total || 0,
      label: 'Impuestos Totales',
      change: 0,
      background: '#fef3c7', // Amarillo/Naranja para el icono
      bgColor: 'bg-orange-100', // Naranja para el fondo
      textColor: 'text-orange-800', // Naranja oscuro para el texto
      type: 'currency'
    },
    {
      icon: '👥',
      value: data.proveedores.cantidad,
      label: 'Proveedores Activos',
      change: data.proveedores.cambio,
      background: '#e9d5ff', // Púrpura para el icono
      bgColor: 'bg-purple-100', // Morado para el fondo
      textColor: 'text-purple-800', // Morado oscuro para el texto
      type: 'number'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 ipad:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 ipad:gap-4 lg:gap-6 mb-4 sm:mb-6 lg:mb-8">
      {kpis.map((kpi, index) => (
        <KPICard key={index} {...kpi} />
      ))}
    </div>
  );
}

