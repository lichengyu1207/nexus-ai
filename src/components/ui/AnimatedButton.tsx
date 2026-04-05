import React, { useRef, useState, useCallback } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import clsx from 'clsx';

type ButtonVariant = 'primary' | 'secondary' | 'text' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface RippleType {
  id: number;
  x: number;
  y: number;
  size: number;
}

interface AnimatedButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  rippleEnabled?: boolean;
  glowEnabled?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-gray-900 shadow-sm',
  secondary: 'bg-transparent border border-primary text-primary',
  text: 'bg-transparent text-primary',
  danger: 'bg-transparent border border-status-error text-status-error',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
};

const glowColors: Record<ButtonVariant, string> = {
  primary: '0 0 20px rgba(255, 217, 102, 0.4)',
  secondary: '0 0 15px rgba(255, 217, 102, 0.2)',
  text: '0 0 10px rgba(255, 217, 102, 0.15)',
  danger: '0 0 15px rgba(239, 68, 68, 0.3)',
};

export const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  rippleEnabled = true,
  glowEnabled = true,
  children,
  className,
  disabled,
  onClick,
  ...props
}) => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [ripples, setRipples] = useState<RippleType[]>([]);
  const scale = useMotionValue(1);
  const boxShadow = useTransform(scale, [0.95, 1], ['0 0 0 rgba(0,0,0,0)', glowEnabled ? glowColors[variant] : '0 0 0 rgba(0,0,0,0)']);

  const createRipple = useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
    if (!rippleEnabled || !buttonRef.current) return;

    const button = buttonRef.current;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 2;
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    const newRipple: RippleType = {
      id: Date.now(),
      x,
      y,
      size,
    };

    setRipples((prev) => [...prev, newRipple]);

    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
    }, 600);
  }, [rippleEnabled]);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    createRipple(event);
    onClick?.(event);
  };

  const handleMouseDown = () => {
    animate(scale, 0.95, { type: 'spring', stiffness: 400, damping: 20 });
  };

  const handleMouseUp = () => {
    animate(scale, 1, { type: 'spring', stiffness: 400, damping: 20 });
  };

  const handleMouseEnter = () => {
    if (!disabled) {
      animate(scale, 1.02, { type: 'spring', stiffness: 300, damping: 15 });
    }
  };

  const handleMouseLeave = () => {
    animate(scale, 1, { type: 'spring', stiffness: 300, damping: 15 });
  };

  return (
    <motion.button
      ref={buttonRef}
      className={clsx(
        'relative inline-flex items-center justify-center font-medium rounded-lg',
        'overflow-hidden transition-colors duration-200',
        'focus:outline-none focus:ring-2 focus:ring-primary/50',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        variant === 'primary' && 'hover:bg-primary-dark',
        variant === 'secondary' && 'hover:bg-primary/10',
        variant === 'text' && 'hover:underline',
        variant === 'danger' && 'hover:bg-status-error/10',
        className
      )}
      style={{ scale, boxShadow }}
      disabled={disabled || isLoading}
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      whileTap={{ scale: 0.95 }}
      {...props}
    >
      {ripples.map((ripple) => (
        <motion.span
          key={ripple.id}
          initial={{ scale: 0, opacity: 0.5 }}
          animate={{ scale: 1, opacity: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="absolute rounded-full bg-white/30 pointer-events-none"
          style={{
            left: ripple.x,
            top: ripple.y,
            width: ripple.size,
            height: ripple.size,
          }}
        />
      ))}

      {isLoading && (
        <motion.svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 0114.707"
          />
        </motion.svg>
      )}

      {!isLoading && leftIcon && (
        <motion.span
          className="mr-2"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.2 }}
        >
          {leftIcon}
        </motion.span>
      )}

      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.span>

      {!isLoading && rightIcon && (
        <motion.span
          className="ml-2"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.2 }}
        >
          {rightIcon}
        </motion.span>
      )}
    </motion.button>
  );
};

export default AnimatedButton;
