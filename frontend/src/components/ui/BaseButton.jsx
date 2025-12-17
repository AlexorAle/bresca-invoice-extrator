/**
 * BaseButton - Componente base reutilizable para botones
 * Usa design tokens para consistencia visual
 */
import { Button } from '@mui/material';
import { BUTTON_HEIGHTS, SPACING, BORDER_RADIUS } from '../../admin/styles/designTokens';

export const BaseButton = ({
  variant = 'contained',
  size = 'primary', // 'primary' | 'secondary' | 'icon'
  children,
  sx,
  ...props
}) => {
  const height = size === 'primary' 
    ? BUTTON_HEIGHTS.primary 
    : size === 'secondary' 
    ? BUTTON_HEIGHTS.secondary 
    : BUTTON_HEIGHTS.icon;

  return (
    <Button
      variant={variant}
      sx={{
        height,
        px: SPACING.md, // '16px'
        borderRadius: BORDER_RADIUS.md, // '6px'
        textTransform: 'none',
        fontWeight: 500,
        fontSize: '14px',
        ...sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
};
