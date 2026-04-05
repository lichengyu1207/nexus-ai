import React from 'react';
import { SvgIconProps, SVG_ICON_SIZES, SvgIconSize } from './svgIconTypes';

interface DuduIconProps extends SvgIconProps {
  expression?: 'happy' | 'thinking' | 'excited';
}

const DUDU_SVG = `
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="30" fill="#0A2342" stroke="#D4AF37" stroke-width="2"/>
  <circle cx="22" cy="27" r="3" fill="white"/>
  <circle cx="42" cy="27" r="3" fill="white"/>
  <path d="M24 38 C28 44 36 44 40 38" stroke="#D4AF37" stroke-width="3" fill="none" stroke-linecap="round"/>
  <path d="M32 20 L32 24 M28 22 L32 24 L36 22" stroke="#D4AF37" stroke-width="2" fill="none"/>
  <rect x="28" y="45" width="8" height="3" fill="#D4AF37" rx="1.5"/>
  <path d="M12 40 L8 44 L12 48" stroke="#D4AF37" stroke-width="2" fill="none"/>
  <path d="M52 40 L56 44 L52 48" stroke="#D4AF37" stroke-width="2" fill="none"/>
</svg>
`;

export const DuduIcon: React.FC<DuduIconProps> = ({
  size = 'xl',
  className = '',
  animated = false,
  glow = false,
  pulse = false,
  spin = false,
}) => {
  const dimension = SVG_ICON_SIZES[size];
  const scale = dimension / 64;

  const classes = [
    'svg-icon',
    `svg-icon-${size}`,
    animated ? 'svg-icon-animated' : '',
    glow ? 'svg-icon-glow' : '',
    pulse ? 'svg-icon-pulse' : '',
    spin ? 'svg-icon-spin' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <span
      className={classes}
      dangerouslySetInnerHTML={{ __html: DUDU_SVG }}
      style={{
        width: dimension,
        height: dimension,
        display: 'inline-block',
      }}
    />
  );
};

export const DuduIconInline: React.FC<DuduIconProps> = ({
  size = 'xl',
  className = '',
  animated = false,
  glow = false,
}) => {
  const dimension = SVG_ICON_SIZES[size];

  return (
    <svg
      width={dimension}
      height={dimension}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`svg-icon ${className} ${animated ? 'svg-icon-animated' : ''} ${glow ? 'svg-icon-glow' : ''}`}
    >
      <circle cx="32" cy="32" r="30" fill="#0A2342" stroke="#D4AF37" strokeWidth="2" />
      <circle cx="22" cy="27" r="3" fill="white" />
      <circle cx="42" cy="27" r="3" fill="white" />
      <path d="M24 38 C28 44 36 44 40 38" stroke="#D4AF37" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M32 20 L32 24 M28 22 L32 24 L36 22" stroke="#D4AF37" strokeWidth="2" fill="none" />
      <rect x="28" y="45" width="8" height="3" fill="#D4AF37" rx="1.5" />
      <path d="M12 40 L8 44 L12 48" stroke="#D4AF37" strokeWidth="2" fill="none" />
      <path d="M52 40 L56 44 L52 48" stroke="#D4AF37" strokeWidth="2" fill="none" />
    </svg>
  );
};

export default DuduIcon;
