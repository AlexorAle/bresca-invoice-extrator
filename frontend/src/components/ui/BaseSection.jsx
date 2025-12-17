/**
 * BaseSection - Componente para espaciado consistente entre secciones
 * Usa design tokens para mantener uniformidad
 */
import { Box } from '@mui/material';
import { PAGE_LAYOUT } from '../../admin/styles/designTokens';

export const BaseSection = ({
  children,
  spacing = 'default', // 'default' | 'large' | 'small'
  sx,
  ...props
}) => {
  const spacingMap = {
    default: PAGE_LAYOUT.sectionSpacing, // '32px'
    large: PAGE_LAYOUT.gridGapLarge, // '24px'
    small: PAGE_LAYOUT.gridGap, // '16px'
  };

  return (
    <Box
      mb={spacingMap[spacing]}
      sx={sx}
      {...props}
    >
      {children}
    </Box>
  );
};
