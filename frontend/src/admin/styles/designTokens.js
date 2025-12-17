/**
 * Design Tokens - Sistema de espaciado y estilos consistentes
 * Basado en múltiplos de 8px
 */
export const SPACING = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
};

export const BORDER_RADIUS = {
  sm: '4px',   // inputs pequeños
  md: '6px',   // botones
  lg: '8px',   // tarjetas pequeñas
  xl: '12px',  // contenedores grandes (estándar)
  '2xl': '16px',  // tarjetas grandes
  '3xl': '20px',  // contenedores muy grandes (legacy, mantener para compatibilidad)
};

export const BUTTON_HEIGHTS = {
  primary: '40px',
  secondary: '36px',
  icon: '32px',
};

export const TABLE_STYLES = {
  headerHeight: '48px',
  rowHeight: '56px',
  cellPaddingHorizontal: '16px',
  cellPaddingVertical: '16px',
  headerFontSize: '0.875rem', // 14px - Tamaño unificado para headers
  cellFontSize: '0.9375rem', // 15px - Tamaño unificado para celdas
};

export const INPUT_STYLES = {
  height: '40px',
  padding: '0 16px',
  borderRadius: BORDER_RADIUS.md,
  width: '300px', // ancho fijo para buscadores
};

export const CARD_STYLES = {
  padding: '24px',
  borderRadius: BORDER_RADIUS.lg,
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
};

export const PAGE_LAYOUT = {
  titleMarginTop: '24px', // Reducido a la mitad (de 48px a 24px)
  titleMarginBottom: '24px',
  sectionSpacing: '32px',
  gridGap: '16px',
  gridGapLarge: '24px',
};

/**
 * Colores del sistema - Paleta unificada
 * Alineados con tema MUI pero accesibles como tokens
 */
export const COLORS = {
  background: {
    default: '#f8fafc',  // slate-50
    paper: '#ffffff',    // white
    subtle: '#f9fafb',   // gray-50 (para fondos sutiles)
  },
  text: {
    primary: '#1e293b',   // slate-800
    secondary: '#64748b', // slate-500
  },
  primary: {
    main: '#60a5fa',      // blue-400
    light: '#93c5fd',     // blue-300
    dark: '#3b82f6',      // blue-500
  },
  secondary: {
    main: '#475569',      // slate-600
    light: '#64748b',     // slate-500
    dark: '#334155',      // slate-700
  },
  success: {
    main: '#10b981',      // green-500
    light: '#d1fae5',     // green-100
    dark: '#065f46',      // green-800
  },
  error: {
    main: '#ef4444',      // red-500
    light: '#fee2e2',     // red-100
    dark: '#991b1b',      // red-800
  },
  info: {
    main: '#3b82f6',      // blue-500
    light: '#dbeafe',      // blue-100
    dark: '#1e40af',      // blue-800
  },
  warning: {
    main: '#8b5cf6',      // purple-500
    light: '#e9d5ff',     // purple-100
    dark: '#6b21a8',      // purple-800
  },
  border: {
    default: '#e5e7eb',   // gray-200
    subtle: '#e2e8f0',    // slate-200
  },
};

