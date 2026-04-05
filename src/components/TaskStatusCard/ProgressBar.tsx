import React from 'react';
import { motion } from 'framer-motion';

type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

interface ProgressBarProps {
  progress: number;
  status: TaskStatus;
}

const statusColors: Record<TaskStatus, { bg: string; fill: string }> = {
  pending: {
    bg: 'bg-gray-200 dark:bg-gray-700',
    fill: 'bg-gray-400',
  },
  processing: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    fill: 'bg-gradient-to-r from-blue-500 to-blue-400',
  },
  completed: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    fill: 'bg-gradient-to-r from-green-500 to-green-400',
  },
  failed: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    fill: 'bg-gradient-to-r from-red-500 to-red-400',
  },
};

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, status }) => {
  const colors = statusColors[status];
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className="relative w-full h-2 rounded-full overflow-hidden">
      <div className={`absolute inset-0 ${colors.bg}`} />
      
      <motion.div
        className={`absolute inset-y-0 left-0 ${colors.fill} rounded-full`}
        initial={{ width: 0 }}
        animate={{ width: `${clampedProgress}%` }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        data-testid="progress-fill"
      />
      
      {status === 'processing' && (
        <motion.div
          className="absolute inset-y-0 w-20 bg-gradient-to-r from-transparent via-white/40 to-transparent rounded-full"
          animate={{
            x: ['-100px', '400px'],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'linear',
          }}
          data-testid="progress-shimmer"
        />
      )}
    </div>
  );
};

export default ProgressBar;
