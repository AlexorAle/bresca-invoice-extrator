import React, { useState, useMemo } from 'react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { MONTH_NAMES } from '../utils/constants';
import { formatCurrency, formatNumber } from '../utils/formatters';

export function ChartSection({ data, selectedMonth }) {
  const [activeTab, setActiveTab] = useState('importes');

  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    return data.map(item => ({
      dia: item.dia,
      importe: item.importe_total || 0,
      cantidad: item.cantidad || 0,
      iva: item.importe_iva || 0
    }));
  }, [data]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">Día {label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.dataKey === 'importe' || entry.dataKey === 'iva' 
                ? formatCurrency(entry.value)
                : formatNumber(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-[20px] shadow-header p-4 sm:p-6 lg:p-8 mb-6 sm:mb-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 sm:mb-8 gap-4">
        <h2 className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-900">
          Distribución Diaria - {MONTH_NAMES[selectedMonth - 1]} 2025
        </h2>

        {/* Tabs */}
        <div className="flex gap-2 sm:gap-4 w-full md:w-auto overflow-x-auto md:overflow-x-visible scrollbar-hide pb-1">
          {[
            { key: 'importes', label: 'Importes' },
            { key: 'cantidad', label: 'Cantidad' },
            { key: 'iva', label: 'IVA' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 sm:px-6 py-2 rounded-[10px] text-xs sm:text-sm font-medium transition-all duration-200 min-w-[80px] sm:min-w-0 ${
                activeTab === tab.key
                  ? 'bg-gradient-active text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Gráfico */}
      <div style={{ width: '100%', height: '250px' }} className="sm:h-[300px]">
        <ResponsiveContainer>
          {activeTab === 'importes' ? (
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorImporte" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#667eea" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#667eea" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                dataKey="dia" 
                stroke="#94a3b8"
                style={{ fontSize: '0.875rem' }}
              />
              <YAxis 
                stroke="#94a3b8"
                style={{ fontSize: '0.875rem' }}
                tickFormatter={(value) => formatCurrency(value)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area 
                type="monotone" 
                dataKey="importe" 
                stroke="#667eea" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorImporte)" 
              />
            </AreaChart>
          ) : activeTab === 'cantidad' ? (
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                dataKey="dia" 
                stroke="#94a3b8"
                style={{ fontSize: '0.875rem' }}
              />
              <YAxis 
                stroke="#94a3b8"
                style={{ fontSize: '0.875rem' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="cantidad" fill="#667eea" radius={[8, 8, 0, 0]} />
            </BarChart>
          ) : (
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorIva" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#764ba2" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#764ba2" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                dataKey="dia" 
                stroke="#94a3b8"
                style={{ fontSize: '0.875rem' }}
              />
              <YAxis 
                stroke="#94a3b8"
                style={{ fontSize: '0.875rem' }}
                tickFormatter={(value) => formatCurrency(value)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area 
                type="monotone" 
                dataKey="iva" 
                stroke="#764ba2" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorIva)" 
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

