import React from 'react';

interface ProgressProps {
  value: number;
  className?: string;
}

const Progress: React.FC<ProgressProps> = ({ value, className = '' }) => (
  <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${className}`}>
    <div
      className="h-full bg-primary-600 transition-all duration-300 rounded-full"
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);

export default Progress;
export { Progress };
