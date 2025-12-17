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
  type = 'number', // 'number', 'currency', 'percentage'
  cardIndex = 0 // Índice de la card (0-3) para asignar color
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

  // Colores de las cards según índice (Card 1-4)
  const cardColors = ['#1e3a8a', '#1e40af', '#2563eb', '#3b82f6'];

  return (
    <div 
      className="rounded-2xl p-6 transition-all duration-300 relative overflow-hidden"
      style={{
        backgroundColor: '#ffffff', // Tarjetas/Cards
        boxShadow: '0 2px 8px rgba(30, 58, 138, 0.12)', // Sombra Normal
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 8px 20px rgba(30, 58, 138, 0.25), 0 0 0 2px rgba(37, 99, 235, 0.1)';
        e.currentTarget.style.transform = 'translateY(-4px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(30, 58, 138, 0.12)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
      role="region"
      aria-label={`KPI de ${label}`}
    >
      {/* Layout horizontal: Icono izquierda, Info derecha */}
      <div className="flex items-center gap-4">
        {/* Ícono a la izquierda */}
        <div 
          className="text-[28px] flex-shrink-0"
          style={{ color: cardColors[cardIndex] || cardColors[0] }}
        >
          {icon}
        </div>

        {/* Información a la derecha, centrada verticalmente */}
        <div className="flex-1 flex flex-col justify-center">
          {/* Valor principal */}
          <div className="text-[28px] font-bold mb-1.5" style={{ color: '#1e293b' }}>
            {formattedValue}
          </div>

          {/* Label */}
          <div className="text-[13px] font-light" style={{ color: '#64748b' }}>
            {label}
          </div>

          {/* Badge de cambio */}
          {change !== undefined && change !== 0 && (
            <div className="flex items-center gap-1.5 flex-wrap mt-1">
              <span className={`inline-flex items-center gap-0.5 px-1.5 sm:px-2 py-0.5 rounded-full text-xs font-semibold ${getTrendClass()}`}>
                {getTrendIcon()}
                {formatPercentage(Math.abs(change))}
              </span>
              <span className="text-xs text-white opacity-70">vs anterior</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

KPICard.displayName = 'KPICard';

