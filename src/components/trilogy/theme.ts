export const theme = {
  colors: {
    primary: {
      gold: '#D4AF37',
      goldLight: '#E5C76B',
      goldDark: '#B8960C',
      deepBlue: '#0A2342',
      deepBlueLight: '#1A3A5C',
      deepBlueDark: '#051525',
    },
    agents: {
      libu: '#8B5CF6',
      gongbu: '#F97316',
      hubu: '#22C55E',
      bingbu: '#EF4444',
      libu2: '#3B82F6',
      xingbu: '#6B7280',
    },
    memory: {
      userMemory: '#60A5FA',
      businessData: '#34D399',
      externalKnowledge: '#FBBF24',
    },
    evolution: {
      stage1: '#3B82F6',
      stage2: '#8B5CF6',
      stage3: '#D4AF37',
      complete: '#FFD700',
    },
    personality: {
      zhouyu: {
        primary: '#D4AF37',
        secondary: '#F59E0B',
        glow: 'rgba(212, 175, 55, 0.5)',
      },
      luxun: {
        primary: '#3B82F6',
        secondary: '#60A5FA',
        glow: 'rgba(59, 130, 246, 0.5)',
      },
    },
  },
  animation: {
    duration: {
      fast: 0.15,
      standard: 0.3,
      slow: 0.6,
      verySlow: 1.2,
    },
    easing: {
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    },
  },
  particles: {
    types: {
      lightBeam: {
        color: '#D4AF37',
        size: { min: 2, max: 6 },
        speed: { min: 100, max: 300 },
        opacity: { min: 0.3, max: 0.8 },
        lifetime: { min: 1000, max: 3000 },
      },
      probe: {
        color: '#60A5FA',
        size: { min: 3, max: 5 },
        speed: { min: 150, max: 250 },
        opacity: { min: 0.5, max: 0.9 },
        lifetime: { min: 2000, max: 4000 },
      },
      memory: {
        color: '#34D399',
        size: { min: 2, max: 4 },
        speed: { min: 50, max: 150 },
        opacity: { min: 0.4, max: 0.7 },
        lifetime: { min: 3000, max: 5000 },
      },
      evolution: {
        color: '#FFD700',
        size: { min: 4, max: 8 },
        speed: { min: 80, max: 200 },
        opacity: { min: 0.6, max: 1.0 },
        lifetime: { min: 1500, max: 3000 },
      },
    },
    maxCount: 500,
    performanceThreshold: 50,
  },
  typography: {
    fontFamily: {
      primary: '"Noto Sans SC", "Microsoft YaHei", sans-serif',
      display: '"ZCOOL XiaoWei", "Noto Serif SC", serif',
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem',
    },
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    '2xl': '1.5rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    glow: {
      gold: '0 0 20px rgba(212, 175, 55, 0.5)',
      blue: '0 0 20px rgba(59, 130, 246, 0.5)',
      green: '0 0 20px rgba(34, 197, 94, 0.5)',
    },
  },
  zIndex: {
    background: 0,
    particles: 10,
    content: 20,
    overlay: 30,
    modal: 40,
    tooltip: 50,
    toast: 60,
  },
};

export type Theme = typeof theme;
export default theme;
