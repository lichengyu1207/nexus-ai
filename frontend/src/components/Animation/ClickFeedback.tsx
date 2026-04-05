/**
 * 点击反馈组件
 * Click Feedback Component
 * 
 * 为可点击元素提供统一的点击反馈效果
 */

import React, { useRef, useCallback, memo } from 'react';
import { motion } from 'framer-motion';

export type FeedbackType = 'scale' | 'ripple' | 'glow' | 'shake';

export interface ClickFeedbackProps {
  children: React.ReactNode;
  type?: FeedbackType;
  intensity?: 'light' | 'medium' | 'strong';
  soundEnabled?: boolean;
  soundUrl?: string;
  danger?: boolean;
  disabled?: boolean;
  className?: string;
  onClick?: () => void;
}

interface Ripple {
  id: number;
  x: number;
  y: number;
  size: number;
}

const intensityConfig = {
  light: { scale: 0.98, duration: 0.1 },
  medium: { scale: 0.95, duration: 0.15 },
  strong: { scale: 0.9, duration: 0.2 },
};

const ClickFeedback: React.FC<ClickFeedbackProps> = memo(({
  children,
  type = 'scale',
  intensity = 'medium',
  soundEnabled = false,
  soundUrl,
  danger = false,
  disabled = false,
  className = '',
  onClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const ripplesRef = useRef<Ripple[]>([]);
  const rippleIdRef = useRef(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const playSound = useCallback(() => {
    if (!soundEnabled) return;

    if (!audioRef.current && soundUrl) {
      audioRef.current = new Audio(soundUrl);
    }

    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
    }
  }, [soundEnabled, soundUrl]);

  const createRipple = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current || type !== 'ripple') return;

    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const size = Math.max(rect.width, rect.height) * 2;

    const ripple: Ripple = {
      id: rippleIdRef.current++,
      x,
      y,
      size,
    };

    ripplesRef.current = [...ripplesRef.current, ripple];

    setTimeout(() => {
      ripplesRef.current = ripplesRef.current.filter(r => r.id !== ripple.id);
    }, 600);
  }, [type]);

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (disabled) return;

    createRipple(e);
    playSound();
    onClick?.();
  }, [disabled, createRipple, playSound, onClick]);

  const config = intensityConfig[intensity];

  const getAnimationProps = () => {
    switch (type) {
      case 'scale':
        return {
          whileTap: { scale: disabled ? 1 : config.scale },
          transition: { duration: config.duration },
        };
      case 'glow':
        return {
          whileTap: {
            boxShadow: danger
              ? '0 0 20px rgba(239, 68, 68, 0.6)'
              : '0 0 20px rgba(59, 130, 246, 0.6)',
          },
        };
      case 'shake':
        return {
          whileTap: {
            x: [0, -5, 5, -5, 5, 0],
            transition: { duration: 0.3 },
          },
        };
      default:
        return {};
    }
  };

  return (
    <motion.div
      ref={containerRef}
      className={`relative overflow-hidden ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'} ${className}`}
      onClick={handleClick}
      {...getAnimationProps()}
      style={{
        borderColor: danger ? 'rgba(239, 68, 68, 0.3)' : undefined,
      }}
    >
      {children}

      {type === 'ripple' && ripplesRef.current.length > 0 && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {ripplesRef.current.map(ripple => (
            <motion.span
              key={ripple.id}
              className="absolute rounded-full"
              style={{
                left: ripple.x - ripple.size / 2,
                top: ripple.y - ripple.size / 2,
                width: ripple.size,
                height: ripple.size,
                backgroundColor: danger ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255, 255, 255, 0.3)',
              }}
              initial={{ scale: 0, opacity: 1 }}
              animate={{ scale: 1, opacity: 0 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />
          ))}
        </div>
      )}

      {danger && type !== 'ripple' && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          initial={{ opacity: 0 }}
          whileTap={{ opacity: 0.3 }}
          style={{ backgroundColor: '#EF4444' }}
        />
      )}
    </motion.div>
  );
});

ClickFeedback.displayName = 'ClickFeedback';

export const ClickableButton: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  className?: string;
}> = memo(({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  className = '',
}) => {
  const variantStyles = {
    primary: 'bg-blue-500 hover:bg-blue-600 text-white',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-700',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
    ghost: 'bg-transparent hover:bg-gray-100 text-gray-700',
  };

  const sizeStyles = {
    small: 'px-3 py-1.5 text-sm',
    medium: 'px-4 py-2 text-base',
    large: 'px-6 py-3 text-lg',
  };

  return (
    <ClickFeedback
      type="scale"
      danger={variant === 'danger'}
      disabled={disabled}
      onClick={onClick}
      className={`
        inline-flex items-center justify-center rounded-lg font-medium
        transition-colors duration-200
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
    >
      {children}
    </ClickFeedback>
  );
});

ClickableButton.displayName = 'ClickableButton';

export const ClickableCard: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  selected?: boolean;
  disabled?: boolean;
  className?: string;
}> = memo(({ children, onClick, selected = false, disabled = false, className = '' }) => (
  <ClickFeedback
    type="scale"
    disabled={disabled}
    onClick={onClick}
    className={`
      bg-white rounded-xl shadow-sm border-2 transition-all duration-200
      ${selected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-100 hover:border-gray-200'}
      ${disabled ? 'opacity-50' : ''}
      ${className}
    `}
  >
    {children}
  </ClickFeedback>
));

ClickableCard.displayName = 'ClickableCard';

export const ClickableIcon: React.FC<{
  icon: React.ReactNode;
  onClick?: () => void;
  size?: 'small' | 'medium' | 'large';
  danger?: boolean;
  disabled?: boolean;
  className?: string;
}> = memo(({
  icon,
  onClick,
  size = 'medium',
  danger = false,
  disabled = false,
  className = '',
}) => {
  const sizeStyles = {
    small: 'w-6 h-6',
    medium: 'w-8 h-8',
    large: 'w-10 h-10',
  };

  return (
    <ClickFeedback
      type="scale"
      intensity="light"
      danger={danger}
      disabled={disabled}
      onClick={onClick}
      className={`
        inline-flex items-center justify-center rounded-full
        bg-gray-100 hover:bg-gray-200
        ${danger ? 'hover:bg-red-100 text-red-500' : 'text-gray-600'}
        ${sizeStyles[size]}
        ${className}
      `}
    >
      {icon}
    </ClickFeedback>
  );
});

ClickableIcon.displayName = 'ClickableIcon';

export default ClickFeedback;
