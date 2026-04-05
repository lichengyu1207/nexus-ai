import { SvgIconDefinition, SVG_ICON_COLORS } from './svgIconTypes';

export const SVG_DEFINITIONS: SvgIconDefinition[] = [
  {
    name: 'dudu',
    displayName: '吉祥物嘟嘟',
    category: 'mascot',
    width: 64,
    height: 64,
    svgCode: `<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="30" fill="#0A2342" stroke="#D4AF37" stroke-width="2"/>
  <circle cx="22" cy="27" r="3" fill="white"/>
  <circle cx="42" cy="27" r="3" fill="white"/>
  <path d="M24 38 C28 44 36 44 40 38" stroke="#D4AF37" stroke-width="3" fill="none" stroke-linecap="round"/>
  <path d="M32 20 L32 24 M28 22 L32 24 L36 22" stroke="#D4AF37" stroke-width="2" fill="none"/>
  <rect x="28" y="45" width="8" height="3" fill="#D4AF37" rx="1.5"/>
  <path d="M12 40 L8 44 L12 48" stroke="#D4AF37" stroke-width="2" fill="none"/>
  <path d="M52 40 L56 44 L52 48" stroke="#D4AF37" stroke-width="2" fill="none"/>
</svg>`,
  },
  {
    name: 'libu',
    displayName: '礼部',
    category: 'ministry',
    width: 48,
    height: 48,
    accentColor: 'libu',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <path d="M16 20 L32 20" stroke="#FF9F4A" stroke-width="2" stroke-linecap="round"/>
  <path d="M16 26 L28 26" stroke="#FF9F4A" stroke-width="2" stroke-linecap="round"/>
  <path d="M16 32 L24 32" stroke="#FF9F4A" stroke-width="2" stroke-linecap="round"/>
  <circle cx="36" cy="30" r="4" stroke="#FF9F4A" stroke-width="1.5" fill="none"/>
  <path d="M34 34 L31 37" stroke="#FF9F4A" stroke-width="1.5" fill="none"/>
</svg>`,
  },
  {
    name: 'hubu',
    displayName: '户部',
    category: 'ministry',
    width: 48,
    height: 48,
    accentColor: 'hubu',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <circle cx="24" cy="26" r="5" stroke="#D4AF37" stroke-width="1.5" fill="none"/>
  <path d="M24 21 L24 31" stroke="#D4AF37" stroke-width="1.5"/>
  <path d="M19 26 L29 26" stroke="#D4AF37" stroke-width="1.5"/>
  <rect x="15" y="34" width="18" height="3" fill="#D4AF37" rx="1"/>
</svg>`,
  },
  {
    name: 'bingbu',
    displayName: '兵部',
    category: 'ministry',
    width: 48,
    height: 48,
    accentColor: 'bingbu',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <circle cx="24" cy="24" r="8" stroke="#2C8C8C" stroke-width="1.5" fill="none"/>
  <path d="M24 24 L32 16" stroke="#2C8C8C" stroke-width="1.5"/>
  <circle cx="24" cy="24" r="2" fill="#2C8C8C"/>
  <circle cx="32" cy="16" r="1.5" fill="#2C8C8C"/>
  <circle cx="16" cy="32" r="1.5" fill="#2C8C8C"/>
</svg>`,
  },
  {
    name: 'gongbu',
    displayName: '工部',
    category: 'ministry',
    width: 48,
    height: 48,
    accentColor: 'gongbu',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <path d="M14 34 L20 28 L26 32 L34 22" stroke="#2C7DA0" stroke-width="2" fill="none"/>
  <circle cx="34" cy="22" r="2" fill="#2C7DA0"/>
  <path d="M28 30 L30 32" stroke="#2C7DA0" stroke-width="1.5"/>
  <circle cx="30" cy="32" r="1.5" fill="#2C7DA0"/>
</svg>`,
  },
  {
    name: 'libu2',
    displayName: '吏部',
    category: 'ministry',
    width: 48,
    height: 48,
    accentColor: 'libu2',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <circle cx="18" cy="20" r="3" fill="#8B5CF6"/>
  <circle cx="30" cy="20" r="3" fill="#8B5CF6"/>
  <circle cx="24" cy="30" r="3" fill="#8B5CF6"/>
  <path d="M18 20 L24 30" stroke="#8B5CF6" stroke-width="1.5"/>
  <path d="M30 20 L24 30" stroke="#8B5CF6" stroke-width="1.5"/>
</svg>`,
  },
  {
    name: 'xingbu',
    displayName: '刑部',
    category: 'ministry',
    width: 48,
    height: 48,
    accentColor: 'xingbu',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <path d="M24 16 L34 20 L24 24 L14 20 L24 16Z" fill="#C44536" fill-opacity="0.3" stroke="#C44536" stroke-width="1.5"/>
  <rect x="21" y="26" width="6" height="8" fill="#C44536" rx="1"/>
  <circle cx="24" cy="28" r="1.5" fill="white"/>
</svg>`,
  },
  {
    name: 'hippocampus',
    displayName: '海马体记忆系统',
    category: 'cluster',
    width: 48,
    height: 48,
    accentColor: 'hippocampus',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <path d="M18 26 L21 28 L24 24 L27 30 L30 26" stroke="#9B6BFF" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <circle cx="24" cy="24" r="8" stroke="#9B6BFF" stroke-width="1.5" fill="none"/>
  <circle cx="24" cy="24" r="3" fill="#9B6BFF"/>
</svg>`,
  },
  {
    name: 'attack',
    displayName: '攻击与防御集群',
    category: 'cluster',
    width: 48,
    height: 48,
    accentColor: 'attack',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <path d="M24 18 L30 22 L24 26 L18 22 L24 18Z" fill="#1E6091" fill-opacity="0.5" stroke="#1E6091" stroke-width="1.5"/>
  <path d="M28 30 L34 34 M32 30 L26 34" stroke="#E63946" stroke-width="1.8" stroke-linecap="round"/>
</svg>`,
  },
  {
    name: 'social',
    displayName: '防社会工程学集群',
    category: 'cluster',
    width: 48,
    height: 48,
    accentColor: 'social',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <circle cx="24" cy="24" r="8" stroke="#FFB347" stroke-width="1.5" fill="none"/>
  <circle cx="24" cy="22" r="1.5" fill="#FFB347"/>
  <path d="M20 28 L28 28" stroke="#FFB347" stroke-width="1.5"/>
  <circle cx="24" cy="30" r="1.5" fill="#FFB347"/>
  <line x1="14" y1="34" x2="34" y2="34" stroke="#FFB347" stroke-width="1.5"/>
</svg>`,
  },
  {
    name: 'audit',
    displayName: '审计合规集群',
    category: 'cluster',
    width: 48,
    height: 48,
    accentColor: 'audit',
    svgCode: `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" stroke-width="1.5"/>
  <circle cx="32" cy="32" r="4" stroke="#2E7D32" stroke-width="1.5" fill="none"/>
  <path d="M28 28 L24 24" stroke="#2E7D32" stroke-width="1.5"/>
  <rect x="16" y="20" width="12" height="12" stroke="#2E7D32" stroke-width="1.5" fill="none"/>
  <line x1="20" y1="24" x2="24" y2="24" stroke="#2E7D32" stroke-width="1"/>
  <line x1="20" y1="28" x2="24" y2="28" stroke="#2E7D32" stroke-width="1"/>
</svg>`,
  },
];

export function downloadSvg(name: string): void {
  const definition = SVG_DEFINITIONS.find(d => d.name === name);
  if (!definition) return;

  const blob = new Blob([definition.svgCode], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${name}.svg`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function downloadAllSvgs(): void {
  SVG_DEFINITIONS.forEach(def => downloadSvg(def.name));
}

export function getSvgCode(name: string): string | undefined {
  const definition = SVG_DEFINITIONS.find(d => d.name === name);
  return definition?.svgCode;
}

export function getIconDefinition(name: string): SvgIconDefinition | undefined {
  return SVG_DEFINITIONS.find(d => d.name === name);
}

export function getIconsByCategory(category: 'mascot' | 'ministry' | 'cluster'): SvgIconDefinition[] {
  return SVG_DEFINITIONS.filter(d => d.category === category);
}
