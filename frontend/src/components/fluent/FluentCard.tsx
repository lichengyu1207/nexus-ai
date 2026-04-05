import React from 'react';
import { motion } from 'framer-motion';

interface FluentCardProps {
  children: React.ReactNode;
  className?: string;
  elevated?: boolean;
  acrylic?: boolean;
  bordered?: boolean;
  goldAccent?: boolean;
  padding?: 'sm' | 'md' | 'lg';
  hover?: boolean;
  onClick?: () => void;
}

const FluentCard: React.FC<FluentCardProps> = ({
  children,
  className = '',
  elevated = true,
  acrylic = false,
  bordered = true,
  goldAccent = false,
  padding = 'md',
  hover = false,
  onClick,
}) => {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <motion.div
      className={`
        relative overflow-hidden rounded-2xl 
        transition-all duration-300 ease-fluent
        ${elevated ? 'shadow-fluent-lg hover:shadow-fluent-xl' : 'shadow-fluent-sm'}
        ${acrylic ? 'bg-white/70 backdrop-blur-lg' : 'bg-white'}
        ${bordered ? (goldAccent ? 'border-2 border-fluent-gold-500/30 hover:border-fluent-gold-500/60' : 'border border-gray-100') : ''}
        ${paddingClasses[padding]}
        ${className}
      `}
      onClick={onClick}
      whileHover={hover ? { y: -4, scale: 1.01 } : undefined}
      whileTap={onClick ? { scale: 0.99 } : undefined}
    >
      {acrylic && (
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.02]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          }}
        />
      )}
      <div className="relative z-10">{children}</div>
      {goldAccent && (
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-fluent-gold-500 to-transparent" />
      )}
    </motion.div>
  );
};

export default FluentCard;
