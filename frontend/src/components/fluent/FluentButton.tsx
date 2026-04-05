import React from 'react';
import { motion } from 'framer-motion';

interface FluentButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'gold';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  className?: string;
}

const FluentButton: React.FC<FluentButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  className = '',
}) => {
  const baseClasses = `
    relative
    overflow-hidden
    font-medium
    rounded-xl
    transition-all
    duration-300
    ease-fluent
    inline-flex
    items-center
    justify-center
    gap-2
    cursor-pointer
    disabled:opacity-50
    disabled:cursor-not-allowed
  `;

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-5 py-2.5 text-base',
    lg: 'px-7 py-3.5 text-lg',
  };

  const variantClasses = {
    primary: `
      bg-fluent-deepOcean-500
      text-white
      border-2
      border-fluent-gold-500/30
      hover:border-fluent-gold-500/60
      hover:shadow-gold-glow
    `,
    secondary: `
      bg-fluent-ivory-500
      text-fluent-deepOcean-500
      border-2
      border-fluent-deepOcean-500/20
      hover:border-fluent-deepOcean-500/40
      hover:bg-fluent-ivory-400
    `,
    outline: `
      bg-transparent
      text-fluent-gold-500
      border-2
      border-fluent-gold-500
      hover:bg-fluent-gold-500/10
      hover:shadow-gold-glow
    `,
    ghost: `
      bg-transparent
      text-fluent-deepOcean-500
      hover:bg-fluent-deepOcean-500/5
      dark:text-white
      dark:hover:bg-white/10
    `,
    gold: `
      bg-gradient-to-r
      from-fluent-gold-400
      to-fluent-gold-600
      text-fluent-deepOcean-900
      border-2
      border-fluent-gold-400/50
      hover:from-fluent-gold-300
      hover:to-fluent-gold-500
      hover:shadow-gold-glow-lg
      font-semibold
    `,
  };

  const LoadingSpinner = () => (
    <svg
      className="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );

  return (
    <motion.button
      className={`
        ${baseClasses}
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      onClick={onClick}
      disabled={disabled || loading}
      whileHover={!disabled && !loading ? { scale: 1.02 } : undefined}
      whileTap={!disabled && !loading ? { scale: 0.98 } : undefined}
    >
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {icon && iconPosition === 'left' && <span className="flex-shrink-0">{icon}</span>}
          <span>{children}</span>
          {icon && iconPosition === 'right' && <span className="flex-shrink-0">{icon}</span>}
        </>
      )}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        initial={{ opacity: 0 }}
        whileHover={{ opacity: 1 }}
        style={{
          background: 'radial-gradient(circle at center, rgba(255,255,255,0.1) 0%, transparent 70%)',
        }}
      />
    </motion.button>
  );
};

export default FluentButton;
