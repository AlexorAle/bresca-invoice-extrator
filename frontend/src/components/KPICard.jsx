import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatCurrency, formatNumber, formatPercentage } from '../utils/formatters';

export const KPICard = React.memo(({ 
  icon, 
  value, 
  label, 
  change, 
  background,
  type = 'number' // 'number', 'currency', 'percentage'
}) => {
  // Formatear valor según tipo
  // Si el valor ya es un string (ej: "27/27"), no formatear
  const formattedValue = typeof value === 'string'
    ? value
    : type === 'currency' 
    ? formatCurrency(value)
    : type === 'percentage'
    ? `${value}%`
    : formatNumber(value);

  // Determinar ícono y estilo de tendencia
  const getTrendIcon = () => {
    if (change > 0) return <TrendingUp className="w-5 h-5 text-green-600" />;
    if (change < 0) return <TrendingDown className="w-5 h-5 text-red-600" />;
    return <Minus className="w-5 h-5 text-gray-600" />;
  };

  const getTrendClass = () => {
    if (change > 0) return 'bg-green-100 text-green-700';
    if (change < 0) return 'bg-red-100 text-red-700';
    return 'bg-gray-100 text-gray-700';
  };

  return (
    <div 
      className="bg-white p-4 sm:p-6 lg:p-8 rounded-2xl shadow-card hover:shadow-card-hover transform hover:-translate-y-1 transition-all duration-300 relative overflow-hidden"
      role="region"
      aria-label={`KPI de ${label}`}
    >
      {/* Barra superior de gradiente */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-active" />
      
      {/* Ícono */}
      <div 
        className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center text-xl sm:text-2xl lg:text-3xl mb-3 sm:mb-4"
        style={{ backgroundColor: background }}
      >
        {icon}
      </div>

      {/* Valor principal */}
      <div className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-2">
        {formattedValue}
      </div>

      {/* Label */}
      <div className="text-sm sm:text-base lg:text-lg text-gray-600 font-medium mb-2 sm:mb-3">
        {label}
      </div>

      {/* Badge de cambio */}
      {change !== undefined && change !== 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`inline-flex items-center gap-1 px-2 sm:px-3 py-1 rounded-full text-sm font-semibold ${getTrendClass()}`}>
            {getTrendIcon()}
            {formatPercentage(Math.abs(change))}
          </span>
          <span className="text-sm text-gray-500">vs anterior</span>
        </div>
      )}
    </div>
  );
});

KPICard.displayName = 'KPICard';

