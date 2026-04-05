import React from 'react';
import clsx from 'clsx';
import { motion } from 'framer-motion';

type ProgressStatus = 'default' | 'processing' | 'success' | 'error';

interface ProgressBarProps {
  value: number;
  max?: number;
  status?: ProgressStatus;
  showValue?: boolean;
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

const statusColors: Record<ProgressStatus, { bg: string; fill: string }> = {
  default: {
    bg: 'bg-bg-tertiary',
    fill: 'bg-gradient-to-r from-gray-500 to-gray-400',
  },
  processing: {
    bg: 'bg-bg-tertiary',
    fill: 'bg-gradient-to-r from-primary-dark to-primary',
  },
  success: {
    bg: 'bg-bg-tertiary',
    fill: 'bg-gradient-to-r from-status-success to-emerald-400',
  },
  error: {
    bg: 'bg-bg-tertiary',
    fill: 'bg-gradient-to-r from-status-error to-red-400',
  },
};

const sizeClasses = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  status = 'default',
  showValue = false,
  size = 'md',
  animated = false,
  className,
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const colors = statusColors[status];

  return (
    <div className={clsx('w-full', className)}>
      <div
        className={clsx(
          'w-full rounded-full overflow-hidden',
          colors.bg,
          sizeClasses[size]
        )}
      >
        <motion.div
          className={clsx(
            'h-full rounded-full relative overflow-hidden',
            colors.fill
          )}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        >
          {status === 'processing' && animated && (
            <div className="absolute inset-0 overflow-hidden rounded-full">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
            </div>
          )}
        </motion.div>
      </div>
      {showValue && (
        <div className="flex justify-between mt-1">
          <span className="text-xs text-text-secondary">{value}</span>
          <span className="text-xs text-text-secondary">{max}</span>
        </div>
      )}
    </div>
  );
};

export default ProgressBar;
