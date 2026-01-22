/**
 * Tema personalizado de Material-UI
 * Alineado con design tokens y uso real de componentes
 */
import { createTheme } from '@mui/material/styles';
import { BORDER_RADIUS, COLORS } from './styles/designTokens';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: COLORS.primary.main, // blue-400
      light: COLORS.primary.light, // blue-300
      dark: COLORS.primary.dark,  // blue-500
      contrastText: '#ffffff',
    },
    secondary: {
      main: COLORS.secondary.main, // slate-600
      light: COLORS.secondary.light, // slate-500
      dark: COLORS.secondary.dark,  // slate-700
    },
    background: {
      default: COLORS.background.default, // slate-50
      paper: COLORS.background.paper, // white
    },
    text: {
      primary: COLORS.text.primary,   // slate-800
      secondary: COLORS.text.secondary, // slate-500
    },
    error: {
      main: COLORS.error.main, // red-500
      light: COLORS.error.light, // red-100
      dark: COLORS.error.dark, // red-800
    },
    success: {
      main: COLORS.success.main, // green-500
      light: COLORS.success.light, // green-100
      dark: COLORS.success.dark, // green-800
    },
    warning: {
      main: COLORS.warning.main, // purple-500
      light: COLORS.warning.light, // purple-100
      dark: COLORS.warning.dark, // purple-800
    },
    info: {
      main: COLORS.info.main, // blue-500
      light: COLORS.info.light, // blue-100
      dark: COLORS.info.dark, // blue-800
    },
  },
  typography: {
    fontFamily: "'Inter', 'Outfit', sans-serif",
    h1: {
      fontSize: '2.5rem', // text-4xl
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem', // text-3xl
      fontWeight: 700,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '2rem', // Ajustado para coincidir con uso real (títulos principales)
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h4: {
      fontSize: '1.25rem', // text-xl
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 12, // Cambiado de 20 → 12px para coincidir con BORDER_RADIUS.xl
  },
  components: {
    MuiCard: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          borderRadius: BORDER_RADIUS.xl, // '12px'
          border: `1px solid ${COLORS.border.default}`, // '#e5e7eb'
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: BORDER_RADIUS.md, // '6px'
          textTransform: 'none',
          fontWeight: 500,
          padding: '8px 16px',
        },
        contained: {
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          '&:hover': {
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: BORDER_RADIUS.md, // '6px'
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: BORDER_RADIUS.xl, // '12px'
          '&.RaList-content': {
            borderTop: 'none !important',
            boxShadow: 'none !important',
            border: 'none !important',
          },
          // Eliminar cualquier border-top en Papers dentro de List
          '.RaList-main &': {
            borderTop: 'none !important',
          },
        },
      },
    },
    MuiList: {
      styleOverrides: {
        root: {
          padding: '0 !important',
          '& .RaList-content': {
            borderTop: 'none !important',
            boxShadow: 'none !important',
            border: 'none !important',
            padding: '0 !important',
          },
          '& .RaList-main': {
            paddingTop: '0 !important',
            paddingLeft: '0 !important',
            paddingRight: '0 !important',
            paddingBottom: '0 !important',
            borderTop: 'none !important',
          },
          '& .RaList-actions': {
            borderTop: 'none !important',
            padding: '0 !important',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          fontSize: '1.125rem', // text-lg
          padding: '20px',
        },
        head: {
          fontSize: '1.25rem', // text-xl
          fontWeight: 600,
        },
      },
    },
  },
});

