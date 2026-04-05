import React from 'react';

interface SkeletonProps {
  className?: string;
  animate?: boolean;
}

const Skeleton: React.FC<SkeletonProps> = ({ className = '', animate = true }) => {
  return (
    <div
      className={`
        bg-gray-200 dark:bg-gray-700 rounded
        ${animate ? 'animate-pulse' : ''}
        ${className}
      `}
    />
  );
};

export default Skeleton;
