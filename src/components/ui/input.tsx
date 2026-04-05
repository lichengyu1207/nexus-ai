import React from 'react';
import clsx from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  className,
  id,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-text-secondary text-sm mb-1.5 font-medium"
        >
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-secondary">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          className={clsx(
            'w-full bg-bg-tertiary border rounded-lg px-3 py-2.5',
            'text-text-primary placeholder:text-text-disabled',
            'focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary',
            'transition-all duration-200',
            error && 'border-status-error focus:border-status-error focus:ring-status-error',
            !error && 'border-border-light',
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            className
          )}
          {...props}
        />
        {rightIcon && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-text-secondary">
            {rightIcon}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-1.5 text-status-error text-xs">{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1.5 text-text-secondary text-xs">{helperText}</p>
      )}
    </div>
  );
};

export default Input;
