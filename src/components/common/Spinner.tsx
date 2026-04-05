import React from 'react';
import { motion } from 'framer-motion';

type SpinnerSize = 'sm' | 'md' | 'lg';

interface SpinnerProps {
  size?: SpinnerSize;
  color?: string;
  className?: string;
}

const sizeMap: Record<SpinnerSize, string> = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-3',
  lg: 'w-12 h-12 border-4',
};

const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  color = 'primary',
  className = '',
}) => {
  const colorClass = color === 'primary' 
    ? 'border-primary-500 border-t-transparent' 
    : `border-${color}-500 border-t-transparent`;

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      className={`
        rounded-full
        ${sizeMap[size]}
        ${colorClass}
        ${className}
      `}
    />
  );
};

export default Spinner;
