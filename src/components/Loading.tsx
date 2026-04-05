import React from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  return (
    <ArrowPathIcon
      className={`animate-spin text-primary-600 ${sizeClasses[size]} ${className}`}
    />
  );
};

interface LoadingOverlayProps {
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message = '加载中...' }) => {
  return (
    <div className="fixed inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="text-center">
        <Spinner size="xl" />
        <p className="mt-4 text-gray-600 dark:text-gray-400">{message}</p>
      </div>
    </div>
  );
};

interface LoadingCardProps {
  message?: string;
}

export const LoadingCard: React.FC<LoadingCardProps> = ({ message = '加载中...' }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-8 flex items-center justify-center min-h-[200px]">
      <div className="text-center">
        <Spinner size="lg" />
        <p className="mt-3 text-gray-500 dark:text-gray-400">{message}</p>
      </div>
    </div>
  );
};

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'text',
  width,
  height,
}) => {
  const baseClasses = 'animate-pulse bg-gray-200 dark:bg-gray-700';
  
  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  );
};

export const CardSkeleton: React.FC = () => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 space-y-4">
      <div className="flex items-center gap-4">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="flex-1 space-y-2">
          <Skeleton width="60%" height={16} />
          <Skeleton width="40%" height={12} />
        </div>
      </div>
      <div className="space-y-2">
        <Skeleton height={12} />
        <Skeleton height={12} />
        <Skeleton width="80%" height={12} />
      </div>
      <div className="flex gap-2">
        <Skeleton width={80} height={32} variant="rectangular" />
        <Skeleton width={80} height={32} variant="rectangular" />
      </div>
    </div>
  );
};

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-100 dark:border-gray-700">
        <div className="flex gap-4">
          <Skeleton width={100} height={20} />
          <Skeleton width={150} height={20} />
          <Skeleton width={80} height={20} />
        </div>
      </div>
      <div className="divide-y divide-gray-100 dark:divide-gray-700">
        {Array.from({ length: rows }).map((_, index) => (
          <div key={index} className="p-4 flex items-center gap-4">
            <Skeleton variant="circular" width={40} height={40} />
            <div className="flex-1 space-y-2">
              <Skeleton width="40%" height={14} />
              <Skeleton width="60%" height={12} />
            </div>
            <Skeleton width={80} height={28} variant="rectangular" />
          </div>
        ))}
      </div>
    </div>
  );
};

export const FormSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-2">
          <Skeleton width={80} height={16} />
          <Skeleton height={40} variant="rectangular" />
        </div>
      ))}
      <Skeleton height={44} variant="rectangular" />
    </div>
  );
};

export default Spinner;
