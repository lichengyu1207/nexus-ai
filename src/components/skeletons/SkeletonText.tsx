import React from 'react';
import Skeleton from './Skeleton';

interface SkeletonTextProps {
  lines?: number;
  lineHeight?: string;
  lastLineWidth?: string;
  className?: string;
}

const SkeletonText: React.FC<SkeletonTextProps> = ({
  lines = 3,
  lineHeight = 'h-4',
  lastLineWidth = 'w-3/4',
  className = '',
}) => {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={`${lineHeight} ${
            index === lines - 1 ? lastLineWidth : 'w-full'
          }`}
        />
      ))}
    </div>
  );
};

export default SkeletonText;
