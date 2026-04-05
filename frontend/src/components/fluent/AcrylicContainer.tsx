import React from 'react';
import { motion } from 'framer-motion';

interface AcrylicContainerProps {
  children: React.ReactNode;
  className?: string;
  blur?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  opacity?: number;
  border?: boolean;
  goldAccent?: boolean;
  noise?: boolean;
  onClick?: () => void;
}

const blurMap = {
  sm: 'backdrop-blur-sm',
  md: 'backdrop-blur-md',
  lg: 'backdrop-blur-lg',
  xl: 'backdrop-blur-xl',
  '2xl': 'backdrop-blur-2xl',
};

const AcrylicContainer: React.FC<AcrylicContainerProps> = ({
  children,
  className = '',
  blur = 'md',
  opacity = 0.7,
  border = true,
  goldAccent = false,
  noise = false,
  onClick,
}) => {
  const baseClasses = `
    relative
    overflow-hidden
    rounded-2xl
    transition-all
    duration-300
    ease-fluent
  `;

  const acrylicClasses = `
    ${blurMap[blur]}
    bg-white/[${opacity}]
  `;

  const borderClasses = border
    ? goldAccent
      ? 'border-2 border-fluent-gold-500/30 hover:border-fluent-gold-500/60'
      : 'border border-white/20'
    : '';

  const noiseOverlay = noise ? (
    <div
      className="absolute inset-0 pointer-events-none opacity-[0.03]"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
      }}
    />
  ) : null;

  return (
    <motion.div
      className={`${baseClasses} ${acrylicClasses} ${borderClasses} ${className}`}
      onClick={onClick}
      whileHover={onClick ? { scale: 1.01 } : undefined}
      whileTap={onClick ? { scale: 0.99 } : undefined}
      style={{
        backgroundColor: `rgba(255, 255, 255, ${opacity})`,
      }}
    >
      {noiseOverlay}
      <div className="relative z-10">{children}</div>
      {goldAccent && (
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-fluent-gold-500 to-transparent" />
      )}
    </motion.div>
  );
};

export default AcrylicContainer;
