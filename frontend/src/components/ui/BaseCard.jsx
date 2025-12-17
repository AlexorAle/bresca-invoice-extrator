/**
 * BaseCard - Componente base reutilizable para tarjetas
 * Usa design tokens para consistencia visual
 */
import { Card, CardHeader, CardContent } from '@mui/material';
import { BORDER_RADIUS } from '../../admin/styles/designTokens';

export const BaseCard = ({
  children,
  title,
  headerAction,
  variant = 'default', // 'default' | 'kpi' | 'elevated' (futuro)
  sx,
  contentSx,
  headerSx,
  ...props
}) => {
  // Estilos base
  const baseSx = {
    borderRadius: BORDER_RADIUS.xl, // '12px'
  };

  // Variantes específicas
  const variantStyles = {
    default: {},
    kpi: {
      minHeight: '80px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
    },
    elevated: {
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    },
  };

  return (
    <Card
      sx={{
        ...baseSx,
        ...variantStyles[variant],
        ...sx,
      }}
      {...props}
    >
      {title && (
        <CardHeader
          title={title}
          action={headerAction}
          sx={{
            padding: '20px 24px',
            minHeight: '72px',
            ...headerSx,
          }}
        />
      )}
      <CardContent
        sx={{
          p: '16px',
          ...contentSx,
        }}
      >
        {children}
      </CardContent>
    </Card>
  );
};
