/**
 * KPICard - Componente de KPI migrado a MUI + Design Tokens
 * Reemplazo de KPICard.jsx legacy (Tailwind)
 */
import React from 'react';
import { Box, Typography } from '@mui/material';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatCurrency, formatNumber, formatPercentage } from '../../utils/formatters';
import { COLORS, BORDER_RADIUS } from '../../admin/styles/designTokens';

export const KPICard = React.memo(({ 
  icon, 
  value, 
  label, 
  change, 
  type = 'number', // 'number', 'currency', 'percentage'
  cardIndex = 0 // Índice de la card (0-3) para asignar color
}) => {
  // Formatear valor según tipo
  const formattedValue = typeof value === 'string'
    ? value
    : type === 'currency' 
    ? formatCurrency(value)
    : type === 'percentage'
    ? `${value}%`
    : formatNumber(value);

  // Determinar ícono y estilo de tendencia
  const getTrendIcon = () => {
    if (change > 0) return <TrendingUp size={16} color={COLORS.success.main} />;
    if (change < 0) return <TrendingDown size={16} color={COLORS.error.main} />;
    return <Minus size={16} color={COLORS.text.secondary} />;
  };

  const getTrendStyles = () => {
    if (change > 0) return { bg: COLORS.success.light, text: COLORS.success.dark };
    if (change < 0) return { bg: COLORS.error.light, text: COLORS.error.dark };
    return { bg: COLORS.background.subtle, text: COLORS.text.secondary };
  };

  // Colores de las cards según índice (Card 1-4)
  const cardColors = [COLORS.info.dark, COLORS.info.main, COLORS.primary.dark, COLORS.primary.main];

  const trendStyles = getTrendStyles();

  return (
    <Box
      sx={{
        backgroundColor: COLORS.background.paper,
        borderRadius: BORDER_RADIUS.xl,
        padding: '24px',
        boxShadow: '0 2px 8px rgba(30, 58, 138, 0.12)',
        transition: 'all 0.3s ease',
        position: 'relative',
        overflow: 'hidden',
        '&:hover': {
          boxShadow: '0 8px 20px rgba(30, 58, 138, 0.25), 0 0 0 2px rgba(37, 99, 235, 0.1)',
          transform: 'translateY(-4px)',
        },
      }}
      role="region"
      aria-label={`KPI de ${label}`}
    >
      {/* Layout horizontal: Icono izquierda, Info derecha */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* Ícono a la izquierda */}
        <Box
          sx={{
            fontSize: '28px',
            flexShrink: 0,
            color: cardColors[cardIndex] || cardColors[0],
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon}
        </Box>

        {/* Información a la derecha, centrada verticalmente */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          {/* Valor principal */}
          <Typography
            sx={{
              fontSize: '28px',
              fontWeight: 700,
              mb: 0.5,
              color: COLORS.text.primary,
              lineHeight: 1.2,
            }}
          >
            {formattedValue}
          </Typography>

          {/* Label */}
          <Typography
            sx={{
              fontSize: '13px',
              fontWeight: 300,
              color: COLORS.text.secondary,
              mb: change !== undefined && change !== 0 ? 0.5 : 0,
            }}
          >
            {label}
          </Typography>

          {/* Badge de cambio */}
          {change !== undefined && change !== 0 && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, flexWrap: 'wrap', mt: 0.5 }}>
              <Box
                sx={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 0.5,
                  px: 1.5,
                  py: 0.5,
                  borderRadius: BORDER_RADIUS.md,
                  backgroundColor: trendStyles.bg,
                  color: trendStyles.text,
                  fontSize: '12px',
                  fontWeight: 600,
                }}
              >
                {getTrendIcon()}
                {formatPercentage(Math.abs(change))}
              </Box>
              <Typography
                sx={{
                  fontSize: '12px',
                  color: COLORS.text.secondary,
                  opacity: 0.7,
                }}
              >
                vs anterior
              </Typography>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
});

KPICard.displayName = 'KPICard';
