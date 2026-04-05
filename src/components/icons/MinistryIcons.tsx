import React from 'react';
import { SvgIconProps, SVG_ICON_SIZES, SVG_ICON_COLORS, MinistryIconName } from './svgIconTypes';

interface MinistryIconComponentProps extends SvgIconProps {
  name: MinistryIconName;
}

const MINISTRY_SVGS: Record<MinistryIconName, React.FC<{ accentColor: string }>> = {
  libu: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <path d="M16 20 L32 20" stroke={accentColor} strokeWidth="2" strokeLinecap="round" />
      <path d="M16 26 L28 26" stroke={accentColor} strokeWidth="2" strokeLinecap="round" />
      <path d="M16 32 L24 32" stroke={accentColor} strokeWidth="2" strokeLinecap="round" />
      <circle cx="36" cy="30" r="4" stroke={accentColor} strokeWidth="1.5" fill="none" />
      <path d="M34 34 L31 37" stroke={accentColor} strokeWidth="1.5" fill="none" />
    </svg>
  ),
  
  hubu: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <circle cx="24" cy="26" r="5" stroke={accentColor} strokeWidth="1.5" fill="none" />
      <path d="M24 21 L24 31" stroke={accentColor} strokeWidth="1.5" />
      <path d="M19 26 L29 26" stroke={accentColor} strokeWidth="1.5" />
      <rect x="15" y="34" width="18" height="3" fill={accentColor} rx="1" />
    </svg>
  ),
  
  bingbu: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <circle cx="24" cy="24" r="8" stroke={accentColor} strokeWidth="1.5" fill="none" />
      <path d="M24 24 L32 16" stroke={accentColor} strokeWidth="1.5" />
      <circle cx="24" cy="24" r="2" fill={accentColor} />
      <circle cx="32" cy="16" r="1.5" fill={accentColor} />
      <circle cx="16" cy="32" r="1.5" fill={accentColor} />
    </svg>
  ),
  
  gongbu: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <path d="M14 34 L20 28 L26 32 L34 22" stroke={accentColor} strokeWidth="2" fill="none" />
      <circle cx="34" cy="22" r="2" fill={accentColor} />
      <path d="M28 30 L30 32" stroke={accentColor} strokeWidth="1.5" />
      <circle cx="30" cy="32" r="1.5" fill={accentColor} />
    </svg>
  ),
  
  libu2: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <circle cx="18" cy="20" r="3" fill={accentColor} />
      <circle cx="30" cy="20" r="3" fill={accentColor} />
      <circle cx="24" cy="30" r="3" fill={accentColor} />
      <path d="M18 20 L24 30" stroke={accentColor} strokeWidth="1.5" />
      <path d="M30 20 L24 30" stroke={accentColor} strokeWidth="1.5" />
    </svg>
  ),
  
  xingbu: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <path d="M24 16 L34 20 L24 24 L14 20 L24 16Z" fill={accentColor} fillOpacity="0.3" stroke={accentColor} strokeWidth="1.5" />
      <rect x="21" y="26" width="6" height="8" fill={accentColor} rx="1" />
      <circle cx="24" cy="28" r="1.5" fill="white" />
    </svg>
  ),
};

export const MinistryIcon: React.FC<MinistryIconComponentProps> = ({
  name,
  size = 'lg',
  className = '',
  animated = false,
  glow = false,
}) => {
  const dimension = SVG_ICON_SIZES[size];
  const accentColor = SVG_ICON_COLORS.accents[name];
  const SvgComponent = MINISTRY_SVGS[name];

  const classes = [
    'svg-icon',
    `svg-icon-${size}`,
    animated ? 'svg-icon-animated' : '',
    glow ? 'svg-icon-glow' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <span className={classes} style={{ width: dimension, height: dimension, display: 'inline-block' }}>
      <SvgComponent accentColor={accentColor} />
    </span>
  );
};

export const LibuIcon: React.FC<Omit<MinistryIconComponentProps, 'name'>> = (props) => (
  <MinistryIcon name="libu" {...props} />
);

export const HubuIcon: React.FC<Omit<MinistryIconComponentProps, 'name'>> = (props) => (
  <MinistryIcon name="hubu" {...props} />
);

export const BingbuIcon: React.FC<Omit<MinistryIconComponentProps, 'name'>> = (props) => (
  <MinistryIcon name="bingbu" {...props} />
);

export const GongbuIcon: React.FC<Omit<MinistryIconComponentProps, 'name'>> = (props) => (
  <MinistryIcon name="gongbu" {...props} />
);

export const Libu2Icon: React.FC<Omit<MinistryIconComponentProps, 'name'>> = (props) => (
  <MinistryIcon name="libu2" {...props} />
);

export const XingbuIcon: React.FC<Omit<MinistryIconComponentProps, 'name'>> = (props) => (
  <MinistryIcon name="xingbu" {...props} />
);

export default MinistryIcon;
