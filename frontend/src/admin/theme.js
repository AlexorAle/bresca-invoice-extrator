/**
 * Tema personalizado de Material-UI
 * Mantiene el diseño visual actual del Dashboard
 */
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#60a5fa', // blue-400
      light: '#93c5fd', // blue-300
      dark: '#3b82f6',  // blue-500
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#475569', // slate-600
      light: '#64748b', // slate-500
      dark: '#334155',  // slate-700
    },
    background: {
      default: '#f8fafc', // slate-50
      paper: '#ffffff',
    },
    text: {
      primary: '#1e293b',   // slate-800
      secondary: '#64748b', // slate-500
    },
    error: {
      main: '#ef4444', // red-500
    },
    success: {
      main: '#10b981', // green-500
    },
    warning: {
      main: '#f59e0b', // amber-500
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
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
      fontSize: '1.5rem', // text-2xl
      fontWeight: 600,
      lineHeight: 1.4,
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
    borderRadius: 20, // rounded-[20px]
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '20px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          border: '1px solid #e2e8f0', // border-gray-200
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          textTransform: 'none',
          fontWeight: 600,
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
            borderRadius: '8px',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '20px',
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

