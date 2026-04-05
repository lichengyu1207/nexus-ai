import React from 'react';
import { SvgIconProps, SVG_ICON_SIZES, SVG_ICON_COLORS, ClusterIconName } from './svgIconTypes';

interface ClusterIconComponentProps extends SvgIconProps {
  name: ClusterIconName;
}

const CLUSTER_SVGS: Record<ClusterIconName, React.FC<{ accentColor: string }>> = {
  hippocampus: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <path d="M18 26 L21 28 L24 24 L27 30 L30 26" stroke={accentColor} strokeWidth="1.8" fill="none" strokeLinecap="round" />
      <circle cx="24" cy="24" r="8" stroke={accentColor} strokeWidth="1.5" fill="none" />
      <circle cx="24" cy="24" r="3" fill={accentColor} />
    </svg>
  ),
  
  attack: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <path d="M24 18 L30 22 L24 26 L18 22 L24 18Z" fill={accentColor} fillOpacity="0.5" stroke={accentColor} strokeWidth="1.5" />
      <path d="M28 30 L34 34 M32 30 L26 34" stroke="#E63946" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  
  social: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <circle cx="24" cy="24" r="8" stroke={accentColor} strokeWidth="1.5" fill="none" />
      <circle cx="24" cy="22" r="1.5" fill={accentColor} />
      <path d="M20 28 L28 28" stroke={accentColor} strokeWidth="1.5" />
      <circle cx="24" cy="30" r="1.5" fill={accentColor} />
      <line x1="14" y1="34" x2="34" y2="34" stroke={accentColor} strokeWidth="1.5" />
    </svg>
  ),
  
  audit: ({ accentColor }) => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="24" cy="24" r="22" fill="#0A2342" stroke="#D4AF37" strokeWidth="1.5" />
      <circle cx="32" cy="32" r="4" stroke={accentColor} strokeWidth="1.5" fill="none" />
      <path d="M28 28 L24 24" stroke={accentColor} strokeWidth="1.5" />
      <rect x="16" y="20" width="12" height="12" stroke={accentColor} strokeWidth="1.5" fill="none" />
      <line x1="20" y1="24" x2="24" y2="24" stroke={accentColor} strokeWidth="1" />
      <line x1="20" y1="28" x2="24" y2="28" stroke={accentColor} strokeWidth="1" />
    </svg>
  ),
};

export const ClusterIcon: React.FC<ClusterIconComponentProps> = ({
  name,
  size = 'lg',
  className = '',
  animated = false,
  glow = false,
}) => {
  const dimension = SVG_ICON_SIZES[size];
  const accentColor = SVG_ICON_COLORS.accents[name];
  const SvgComponent = CLUSTER_SVGS[name];

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

export const HippocampusIcon: React.FC<Omit<ClusterIconComponentProps, 'name'>> = (props) => (
  <ClusterIcon name="hippocampus" {...props} />
);

export const AttackIcon: React.FC<Omit<ClusterIconComponentProps, 'name'>> = (props) => (
  <ClusterIcon name="attack" {...props} />
);

export const SocialIcon: React.FC<Omit<ClusterIconComponentProps, 'name'>> = (props) => (
  <ClusterIcon name="social" {...props} />
);

export const AuditIcon: React.FC<Omit<ClusterIconComponentProps, 'name'>> = (props) => (
  <ClusterIcon name="audit" {...props} />
);

export default ClusterIcon;
