/**
 * Design Tokens
 * 
 * Central source of truth for all design values.
 * Based on specs in docs/design/
 */

// ============================================================================
// COLORS
// ============================================================================

export const colors = {
  // Primary (Indigo) - Trust, intelligence, professionalism
  primary: {
    50: '#EEF2FF',
    100: '#E0E7FF',
    200: '#C7D2FE',
    300: '#A5B4FC',
    400: '#818CF8',
    500: '#6366F1',
    600: '#4F46E5', // Default primary
    700: '#4338CA',
    800: '#3730A3',
    900: '#312E81',
  },

  // Secondary (Cyan) - Technology, GitHub, data
  secondary: {
    50: '#ECFEFF',
    100: '#CFFAFE',
    200: '#A5F3FC',
    300: '#67E8F9',
    400: '#22D3EE',
    500: '#06B6D4', // Default secondary
    600: '#0891B2',
    700: '#0E7490',
    800: '#155E75',
    900: '#164E63',
  },

  // Accent (Amber) - Discovery, highlights, important info
  accent: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    200: '#FDE68A',
    300: '#FCD34D',
    400: '#FBBF24',
    500: '#F59E0B', // Default accent
    600: '#D97706',
    700: '#B45309',
    800: '#92400E',
    900: '#78350F',
  },

  // Success (Emerald) - Verified, confirmed, successful
  success: {
    50: '#ECFDF5',
    100: '#D1FAE5',
    200: '#A7F3D0',
    300: '#6EE7B7',
    400: '#34D399',
    500: '#10B981', // Default success
    600: '#059669',
    700: '#047857',
    800: '#065F46',
    900: '#064E3B',
  },

  // Warning (Orange) - Needs attention, verification required
  warning: {
    50: '#FFF7ED',
    100: '#FFEDD5',
    200: '#FED7AA',
    300: '#FDBA74',
    400: '#FB923C',
    500: '#F97316', // Default warning
    600: '#EA580C',
    700: '#C2410C',
    800: '#9A3412',
    900: '#7C2D12',
  },

  // Error (Red) - Errors, destructive actions
  error: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    200: '#FECACA',
    300: '#FCA5A5',
    400: '#F87171',
    500: '#EF4444', // Default error
    600: '#DC2626',
    700: '#B91C1C',
    800: '#991B1B',
    900: '#7F1D1D',
  },

  // Info (Blue) - Information, tips
  info: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    200: '#BFDBFE',
    300: '#93C5FD',
    400: '#60A5FA',
    500: '#3B82F6', // Default info
    600: '#2563EB',
    700: '#1D4ED8',
    800: '#1E40AF',
    900: '#1E3A8A',
  },

  // Purple (AI Features) - AI-powered features, magical moments
  purple: {
    50: '#FAF5FF',
    100: '#F3E8FF',
    200: '#E9D5FF',
    300: '#D8B4FE',
    400: '#C084FC',
    500: '#A855F7',
    600: '#9333EA',
    700: '#7E22CE',
    800: '#6B21A8',
    900: '#581C87',
  },

  // Pink (AI Features) - Complement to purple
  pink: {
    50: '#FDF2F8',
    100: '#FCE7F3',
    200: '#FBCFE8',
    300: '#F9A8D4',
    400: '#F472B6',
    500: '#EC4899',
    600: '#DB2777',
    700: '#BE185D',
    800: '#9D174D',
    900: '#831843',
  },

  // Gray (Neutral) - Text, backgrounds, borders
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
  },

  // Semantic Colors
  text: {
    primary: '#111827',    // gray-900
    secondary: '#374151',  // gray-700
    tertiary: '#6B7280',   // gray-500
    disabled: '#9CA3AF',   // gray-400
    inverse: '#FFFFFF',
  },

  background: {
    primary: '#FFFFFF',
    secondary: '#F9FAFB',  // gray-50
    tertiary: '#F3F4F6',   // gray-100
    inverse: '#111827',    // gray-900
  },

  border: {
    default: '#E5E7EB',    // gray-200
    hover: '#D1D5DB',      // gray-300
    focus: '#4F46E5',      // primary-600
  },
};

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  fontFamily: {
    display: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    body: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif',
    code: '"JetBrains Mono", "Fira Code", "Courier New", monospace',
  },

  fontSize: {
    // Display
    'display-2xl': { size: '72px', lineHeight: '90px', weight: 800 },
    'display-xl': { size: '60px', lineHeight: '72px', weight: 800 },
    'display-lg': { size: '48px', lineHeight: '60px', weight: 700 },
    'display-md': { size: '36px', lineHeight: '44px', weight: 700 },
    'display-sm': { size: '30px', lineHeight: '38px', weight: 600 },

    // Headings
    'heading-xl': { size: '24px', lineHeight: '32px', weight: 600 },
    'heading-lg': { size: '20px', lineHeight: '28px', weight: 600 },
    'heading-md': { size: '18px', lineHeight: '26px', weight: 600 },
    'heading-sm': { size: '16px', lineHeight: '24px', weight: 600 },

    // Body
    'body-xl': { size: '20px', lineHeight: '30px', weight: 400 },
    'body-lg': { size: '18px', lineHeight: '28px', weight: 400 },
    'body-md': { size: '16px', lineHeight: '24px', weight: 400 },
    'body-sm': { size: '14px', lineHeight: '20px', weight: 400 },
    'body-xs': { size: '12px', lineHeight: '16px', weight: 400 },

    // Code
    'code-lg': { size: '16px', lineHeight: '24px', weight: 400 },
    'code-md': { size: '14px', lineHeight: '20px', weight: 400 },
    'code-sm': { size: '12px', lineHeight: '16px', weight: 400 },
  },

  fontWeight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },
};

// ============================================================================
// SPACING
// ============================================================================

export const spacing = {
  xs: '4px',      // 0.25rem
  sm: '8px',      // 0.5rem
  md: '16px',     // 1rem
  lg: '24px',     // 1.5rem
  xl: '32px',     // 2rem
  '2xl': '48px',  // 3rem
  '3xl': '64px',  // 4rem
  '4xl': '96px',  // 6rem
  '5xl': '128px', // 8rem
};

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows = {
  none: 'none',
  xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
};

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const borderRadius = {
  none: '0',
  sm: '4px',
  md: '6px',
  lg: '8px',
  xl: '12px',
  '2xl': '16px',
  '3xl': '24px',
  full: '9999px',
};

// ============================================================================
// Z-INDEX
// ============================================================================

export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  fixed: 1200,
  modalBackdrop: 1300,
  modal: 1400,
  popover: 1500,
  toast: 1600,
};

// ============================================================================
// BREAKPOINTS
// ============================================================================

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// ============================================================================
// LAYOUT
// ============================================================================

export const layout = {
  maxWidth: {
    content: '65ch',
    page: '1440px',
    modal: '600px',
    modalLg: '800px',
    modalXl: '1200px',
  },

  header: {
    height: '64px',
    mobileHeight: '56px',
  },

  sidebar: {
    width: '280px',
    collapsedWidth: '64px',
  },
};

// ============================================================================
// TRANSITIONS
// ============================================================================

export const transitions = {
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
  slowest: '500ms cubic-bezier(0.4, 0, 0.2, 1)',
};

// ============================================================================
// MATCH SCORE COLORS
// ============================================================================

export const matchScoreColors = {
  excellent: {
    background: colors.success[500],
    text: '#FFFFFF',
    border: colors.success[600],
  },
  good: {
    background: colors.secondary[500],
    text: '#FFFFFF',
    border: colors.secondary[600],
  },
  fair: {
    background: colors.info[500],
    text: '#FFFFFF',
    border: colors.info[600],
  },
  low: {
    background: colors.gray[400],
    text: '#FFFFFF',
    border: colors.gray[500],
  },
};

// Helper function to get match score color
export function getMatchScoreColor(score: number) {
  if (score >= 80) return matchScoreColors.excellent;
  if (score >= 60) return matchScoreColors.good;
  if (score >= 40) return matchScoreColors.fair;
  return matchScoreColors.low;
}

// ============================================================================
// GRADIENTS
// ============================================================================

export const gradients = {
  ai: 'linear-gradient(135deg, #9333EA 0%, #EC4899 100%)', // purple to pink
  hero: 'linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%)', // indigo to cyan
  success: 'linear-gradient(135deg, #10B981 0%, #06B6D4 100%)', // emerald to cyan
  avatar: [
    'linear-gradient(135deg, #818CF8 0%, #6366F1 100%)', // indigo
    'linear-gradient(135deg, #22D3EE 0%, #06B6D4 100%)', // cyan
    'linear-gradient(135deg, #C084FC 0%, #A855F7 100%)', // purple
    'linear-gradient(135deg, #34D399 0%, #10B981 100%)', // emerald
  ],
};

// Helper function to get consistent gradient for a string (e.g., name)
export function getGradientForString(str: string): string {
  const hash = str.split('').reduce((acc, char) => {
    return char.charCodeAt(0) + ((acc << 5) - acc);
  }, 0);
  
  return gradients.avatar[Math.abs(hash) % gradients.avatar.length];
}

// ============================================================================
// EXPORT ALL
// ============================================================================

export const tokens = {
  colors,
  typography,
  spacing,
  shadows,
  borderRadius,
  zIndex,
  breakpoints,
  layout,
  transitions,
  gradients,
  matchScoreColors,
  getMatchScoreColor,
  getGradientForString,
};

export default tokens;

