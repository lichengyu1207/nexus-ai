import React from 'react';
import Skeleton from './Skeleton';
import SkeletonText from './SkeletonText';

interface SkeletonTimelineProps {
  items?: number;
  className?: string;
}

const SkeletonTimeline: React.FC<SkeletonTimelineProps> = ({
  items = 4,
  className = '',
}) => {
  return (
    <div className={`space-y-6 ${className}`}>
      {Array.from({ length: items }).map((_, index) => (
        <div key={index} className="flex gap-4">
          <div className="flex flex-col items-center">
            <Skeleton className="w-3 h-3 rounded-full" />
            {index < items - 1 && (
              <Skeleton className="w-0.5 flex-1 mt-2" />
            )}
          </div>
          <div className="flex-1 pb-6">
            <div className="flex items-center gap-2 mb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-3 w-16" />
            </div>
            <SkeletonText lines={2} lineHeight="h-3" lastLineWidth="w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
};

export default SkeletonTimeline;
