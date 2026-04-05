import React from 'react';
import { motion } from 'framer-motion';

interface LoadingFallbackProps {
  message?: string;
  fullScreen?: boolean;
}

const SkeletonLoader: React.FC = () => (
  <div className="animate-pulse space-y-4 p-4">
    <div className="h-8 bg-gray-200 rounded w-1/4"></div>
    <div className="space-y-3">
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 rounded w-5/6"></div>
    </div>
    <div className="grid grid-cols-3 gap-4 mt-6">
      <div className="h-24 bg-gray-200 rounded"></div>
      <div className="h-24 bg-gray-200 rounded"></div>
      <div className="h-24 bg-gray-200 rounded"></div>
    </div>
  </div>
);

const Spinner: React.FC = () => (
  <motion.div
    className="flex flex-col items-center justify-center"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.3 }}
  >
    <div className="relative w-16 h-16">
      <motion.div
        className="absolute inset-0 border-4 border-blue-200 rounded-full"
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
      />
      <motion.div
        className="absolute inset-0 border-4 border-blue-600 rounded-full border-t-transparent"
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      />
    </div>
    <motion.div
      className="mt-4 flex space-x-1"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2 }}
    >
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-2 h-2 bg-blue-600 rounded-full"
          animate={{ y: [0, -8, 0] }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: i * 0.1,
          }}
        />
      ))}
    </motion.div>
  </motion.div>
);

const LoadingFallback: React.FC<LoadingFallbackProps> = ({
  message = '加载中...',
  fullScreen = true,
}) => {
  const content = (
    <div className="flex flex-col items-center justify-center p-8">
      <Spinner />
      <motion.p
        className="mt-4 text-gray-500 text-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        {message}
      </motion.p>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        {content}
      </div>
    );
  }

  return content;
};

export const PageLoadingFallback: React.FC<{ pageName?: string }> = ({
  pageName,
}) => (
  <div className="min-h-screen flex flex-col bg-gray-50">
    <div className="h-16 bg-white shadow-sm flex items-center px-6">
      <div className="animate-pulse h-6 bg-gray-200 rounded w-32"></div>
    </div>
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <Spinner />
        <motion.p
          className="mt-4 text-gray-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {pageName ? `正在加载${pageName}...` : '正在加载页面...'}
        </motion.p>
      </div>
    </div>
  </div>
);

export const ComponentLoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center p-4 min-h-[100px]">
    <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent"></div>
  </div>
);

export const TableLoadingFallback: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 5,
  cols = 4,
}) => (
  <div className="animate-pulse">
    <div className="h-10 bg-gray-200 rounded mb-2"></div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="flex gap-2 mb-2">
        {Array.from({ length: cols }).map((_, j) => (
          <div key={j} className="h-8 bg-gray-100 rounded flex-1"></div>
        ))}
      </div>
    ))}
  </div>
);

export const CardLoadingFallback: React.FC<{ count?: number }> = ({ count = 3 }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="animate-pulse bg-white rounded-lg shadow p-4">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
        <div className="h-3 bg-gray-100 rounded w-1/2 mb-2"></div>
        <div className="h-3 bg-gray-100 rounded w-5/6"></div>
      </div>
    ))}
  </div>
);

export default LoadingFallback;
