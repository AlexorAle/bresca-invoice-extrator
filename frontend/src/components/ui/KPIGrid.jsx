/**
 * KPIGrid - Componente de grid de KPIs migrado a MUI + Design Tokens
 * Reemplazo de KPIGrid.jsx legacy (Tailwind)
 */
import React from 'react';
import { Box, Skeleton } from '@mui/material';
import { KPICard } from './KPICard';
import { SPACING } from '../../admin/styles/designTokens';

export function KPIGrid({ data, loading }) {
  if (loading) {
    return (
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
          gap: 2.5,
          mb: 2.5,
        }}
      >
        {[1, 2, 3, 4].map((i) => (
          <Box
            key={i}
            sx={{
              backgroundColor: '#ffffff',
              padding: { xs: 2, sm: 3, lg: 4 },
              borderRadius: '12px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}
          >
            <Skeleton variant="circular" width={48} height={48} sx={{ mb: 2 }} />
            <Skeleton variant="text" width="60%" height={32} sx={{ mb: 1 }} />
            <Skeleton variant="text" width="80%" height={20} sx={{ mb: 2 }} />
            <Skeleton variant="text" width="40%" height={24} />
          </Box>
        ))}
      </Box>
    );
  }

  if (!data) return null;

  const kpis = [
    {
      icon: '📊',
      value: `${data.facturas.actual || 0}/${data.facturas.total || 0}`,
      label: 'Facturas Procesadas',
      change: data.facturas.cambio,
      type: 'number'
    },
    {
      icon: '💰',
      value: data.importe.valor,
      label: 'Importe del Mes',
      change: data.importe.cambio,
      type: 'currency'
    },
    {
      icon: '📈',
      value: data.impuestos_total || 0,
      label: 'Impuestos Totales',
      change: 0,
      type: 'currency'
    },
    {
      icon: '👥',
      value: data.proveedores.cantidad,
      label: 'Proveedores Activos',
      change: data.proveedores.cambio,
      type: 'number'
    }
  ];

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
        gap: 2.5,
        mb: 2.5,
      }}
    >
      {kpis.map((kpi, index) => (
        <KPICard key={index} {...kpi} cardIndex={index} />
      ))}
    </Box>
  );
}
