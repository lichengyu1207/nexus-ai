import React, { Suspense } from 'react';
import ErrorBoundary from './ErrorBoundary';

interface LazyComponentProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

const LoadingFallback: React.FC = () => (
  <div className="loading-container">
    <div className="loading-spinner"></div>
    <p>加载中...</p>
  </div>
);

export const LazyComponent: React.FC<LazyComponentProps> = ({
  children,
  fallback = <LoadingFallback />,
}) => {
  return (
    <ErrorBoundary>
      <Suspense fallback={fallback}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
};

export default LazyComponent;
