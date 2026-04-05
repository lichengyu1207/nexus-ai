import React from 'react';

interface AlertProps {
  variant?: 'default' | 'destructive';
  children: React.ReactNode;
  className?: string;
}

const Alert: React.FC<AlertProps> = ({ variant = 'default', children, className = '' }) => {
  const variants = {
    default: 'bg-gray-50 border-gray-200 text-gray-800',
    destructive: 'bg-red-50 border-red-200 text-red-800',
  };

  return (
    <div
      className={`relative w-full rounded-lg border p-4 ${variants[variant]} ${className}`}
      role="alert"
    >
      {children}
    </div>
  );
};

const AlertDescription: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`text-sm [&_p]:leading-relaxed ${className}`}>
    {children}
  </div>
);

export default Alert;
export { Alert, AlertDescription };
