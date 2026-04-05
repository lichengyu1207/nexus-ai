import React from 'react';
import Skeleton from './Skeleton';

interface SkeletonAvatarProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeClasses = {
  sm: 'w-8 h-8',
  md: 'w-10 h-10',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
};

const SkeletonAvatar: React.FC<SkeletonAvatarProps> = ({
  size = 'md',
  className = '',
}) => {
  return (
    <Skeleton
      className={`${sizeClasses[size]} rounded-full flex-shrink-0 ${className}`}
    />
  );
};

export default SkeletonAvatar;
