export const SVG_ICON_COLORS = {
  background: '#0A2342',
  strokeGold: '#D4AF37',
  accents: {
    libu: '#FF9F4A',
    hubu: '#D4AF37',
    bingbu: '#2C8C8C',
    gongbu: '#2C7DA0',
    libu2: '#8B5CF6',
    xingbu: '#C44536',
    hippocampus: '#9B6BFF',
    attack: '#1E6091',
    social: '#FFB347',
    audit: '#2E7D32',
  },
} as const;

export const SVG_ICON_SIZES = {
  xs: 16,
  sm: 24,
  md: 32,
  lg: 48,
  xl: 64,
  '2xl': 96,
} as const;

export const SVG_ICON_STROKE_WIDTHS = {
  thin: 1,
  default: 1.5,
  thick: 2,
} as const;

export type SvgIconSize = keyof typeof SVG_ICON_SIZES;
export type SvgIconAccentColor = keyof typeof SVG_ICON_COLORS.accents;

export interface SvgIconProps {
  size?: SvgIconSize;
  className?: string;
  accentColor?: SvgIconAccentColor;
  animated?: boolean;
  glow?: boolean;
  pulse?: boolean;
  spin?: boolean;
}

export interface SvgIconDefinition {
  name: string;
  displayName: string;
  category: 'mascot' | 'ministry' | 'cluster';
  svgCode: string;
  width: number;
  height: number;
  accentColor?: SvgIconAccentColor;
}

export const MINISTRY_ICONS = ['libu', 'hubu', 'bingbu', 'gongbu', 'libu2', 'xingbu'] as const;
export const CLUSTER_ICONS = ['hippocampus', 'attack', 'social', 'audit'] as const;

export type MinistryIconName = typeof MINISTRY_ICONS[number];
export type ClusterIconName = typeof CLUSTER_ICONS[number];

export const MINISTRY_DISPLAY_NAMES: Record<MinistryIconName, string> = {
  libu: '礼部',
  hubu: '户部',
  bingbu: '兵部',
  gongbu: '工部',
  libu2: '吏部',
  xingbu: '刑部',
};

export const MINISTRY_FUNCTIONS: Record<MinistryIconName, string> = {
  libu: '智能咨询',
  hubu: '积分管理',
  bingbu: '数据采集',
  gongbu: '深度分析',
  libu2: '智能体管理',
  xingbu: '风控合规',
};

export const CLUSTER_DISPLAY_NAMES: Record<ClusterIconName, string> = {
  hippocampus: '海马体记忆系统',
  attack: '攻击与防御集群',
  social: '防社会工程学集群',
  audit: '审计合规集群',
};

export function getAccentColor(name: MinistryIconName | ClusterIconName): string {
  return SVG_ICON_COLORS.accents[name];
}

export function getIconSize(size: SvgIconSize): number {
  return SVG_ICON_SIZES[size];
}
