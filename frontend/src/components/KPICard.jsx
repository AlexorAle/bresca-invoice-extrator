import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatCurrency, formatNumber, formatPercentage } from '../utils/formatters';

export const KPICard = React.memo(({ 
  icon, 
  value, 
  label, 
  change, 
  background,
  bgColor = 'bg-white', // Color de fondo de la tarjeta
  textColor = 'text-gray-900', // Color de texto principal
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
      className={`${bgColor} border border-gray-200 p-2 sm:p-3 lg:p-4 rounded-lg shadow-card hover:shadow-card-hover transform hover:-translate-y-1 transition-all duration-300 relative overflow-hidden`}
      role="region"
      aria-label={`KPI de ${label}`}
    >
      {/* Barra superior de gradiente */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-active" />
      
      {/* Layout horizontal: Icono izquierda, Info derecha */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Ícono a la izquierda */}
        <div 
          className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center text-lg sm:text-xl lg:text-2xl flex-shrink-0"
          style={{ backgroundColor: background }}
        >
          {icon}
        </div>

        {/* Información a la derecha, centrada verticalmente */}
        <div className="flex-1 flex flex-col justify-center">
          {/* Valor principal */}
          <div className={`text-xl sm:text-2xl lg:text-3xl font-bold ${textColor} mb-0.5`}>
            {formattedValue}
          </div>

          {/* Label */}
          <div className={`text-xs sm:text-sm ${textColor} opacity-80 font-medium`}>
            {label}
          </div>

          {/* Badge de cambio */}
          {change !== undefined && change !== 0 && (
            <div className="flex items-center gap-1.5 flex-wrap mt-1">
              <span className={`inline-flex items-center gap-0.5 px-1.5 sm:px-2 py-0.5 rounded-full text-xs font-semibold ${getTrendClass()}`}>
                {getTrendIcon()}
                {formatPercentage(Math.abs(change))}
              </span>
              <span className="text-xs text-gray-500">vs anterior</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

KPICard.displayName = 'KPICard';

