import React from 'react';
import Skeleton from './Skeleton';
import SkeletonAvatar from './SkeletonAvatar';
import SkeletonText from './SkeletonText';

interface SkeletonCardProps {
  hasAvatar?: boolean;
  hasImage?: boolean;
  lines?: number;
  className?: string;
}

const SkeletonCard: React.FC<SkeletonCardProps> = ({
  hasAvatar = false,
  hasImage = false,
  lines = 2,
  className = '',
}) => {
  return (
    <div
      className={`
        bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4
        ${className}
      `}
    >
      {hasImage && (
        <Skeleton className="w-full h-40 rounded-lg mb-4" />
      )}
      
      {hasAvatar ? (
        <div className="flex items-start gap-3">
          <SkeletonAvatar size="md" />
          <div className="flex-1">
            <Skeleton className="h-4 w-1/3 mb-2" />
            <SkeletonText lines={lines} lineHeight="h-3" lastLineWidth="w-2/3" />
          </div>
        </div>
      ) : (
        <>
          <Skeleton className="h-5 w-3/4 mb-3" />
          <SkeletonText lines={lines} lineHeight="h-3" lastLineWidth="w-1/2" />
        </>
      )}
    </div>
  );
};

export default SkeletonCard;
