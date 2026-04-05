import React from 'react';
import { motion } from 'framer-motion';

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'gold' | 'gradient';
  animated?: boolean;
  className?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  size = 'md',
  variant = 'gold',
  animated = true,
  className = '',
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  const variantStyles = {
    default: 'bg-blue-500',
    gold: 'bg-fluent-gold-500',
    gradient: 'bg-gradient-to-r from-fluent-gold-400 via-fluent-gold-500 to-fluent-gold-600',
  };

  return (
    <div className={`w-full ${className}`}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-1.5">
          {label && (
            <span className="text-sm font-medium text-gray-700">{label}</span>
          )}
          {showPercentage && (
            <span className="text-sm font-semibold text-fluent-gold-500">
              {percentage.toFixed(0)}%
            </span>
          )}
        </div>
      )}
      <div
        className={`
          relative w-full overflow-hidden rounded-full
          bg-gray-200 dark:bg-gray-700
          ${sizeClasses[size]}
        `}
      >
        <motion.div
          className={`
            absolute top-0 left-0 h-full rounded-full
            ${variantStyles[variant]}
          `}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        >
          {animated && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              animate={{ x: ['-100%', '100%'] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            />
          )}
        </motion.div>
        {animated && percentage > 0 && (
          <motion.div
            className="absolute top-0 h-full w-8 bg-gradient-to-r from-transparent via-white/50 to-transparent"
            animate={{ left: ['0%', '100%'] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
        )}
      </div>
    </div>
  );
};

export default ProgressBar;
