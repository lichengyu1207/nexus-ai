/**
 * 悬停提示组件
 * Hover Tip Component
 * 
 * 统一的鼠标悬停提示组件
 */

import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export type TipPosition = 'top' | 'bottom' | 'left' | 'right';

export interface HoverTipProps {
  content: React.ReactNode;
  position?: TipPosition;
  delay?: number;
  children: React.ReactNode;
  className?: string;
  maxWidth?: number;
  disabled?: boolean;
}

interface TipCoordinates {
  x: number;
  y: number;
  arrowX: number;
  arrowY: number;
  actualPosition: TipPosition;
}

const tipOffset = 8;

const calculatePosition = (
  triggerRect: DOMRect,
  tipRect: DOMRect,
  position: TipPosition,
  viewportWidth: number,
  viewportHeight: number
): TipCoordinates => {
  let x = 0;
  let y = 0;
  let actualPosition = position;

  const positions: TipPosition[] = [position];
  
  if (position === 'top') positions.push('bottom', 'left', 'right');
  else if (position === 'bottom') positions.push('top', 'left', 'right');
  else if (position === 'left') positions.push('right', 'top', 'bottom');
  else positions.push('left', 'top', 'bottom');

  for (const pos of positions) {
    actualPosition = pos;
    
    switch (pos) {
      case 'top':
        x = triggerRect.left + (triggerRect.width - tipRect.width) / 2;
        y = triggerRect.top - tipRect.height - tipOffset;
        break;
      case 'bottom':
        x = triggerRect.left + (triggerRect.width - tipRect.width) / 2;
        y = triggerRect.bottom + tipOffset;
        break;
      case 'left':
        x = triggerRect.left - tipRect.width - tipOffset;
        y = triggerRect.top + (triggerRect.height - tipRect.height) / 2;
        break;
      case 'right':
        x = triggerRect.right + tipOffset;
        y = triggerRect.top + (triggerRect.height - tipRect.height) / 2;
        break;
    }

    if (x >= 0 && x + tipRect.width <= viewportWidth && 
        y >= 0 && y + tipRect.height <= viewportHeight) {
      break;
    }
  }

  x = Math.max(0, Math.min(x, viewportWidth - tipRect.width));
  y = Math.max(0, Math.min(y, viewportHeight - tipRect.height));

  let arrowX = 0;
  let arrowY = 0;

  switch (actualPosition) {
    case 'top':
      arrowX = triggerRect.left + triggerRect.width / 2 - x;
      arrowY = tipRect.height;
      break;
    case 'bottom':
      arrowX = triggerRect.left + triggerRect.width / 2 - x;
      arrowY = -6;
      break;
    case 'left':
      arrowX = tipRect.width;
      arrowY = triggerRect.top + triggerRect.height / 2 - y;
      break;
    case 'right':
      arrowX = -6;
      arrowY = triggerRect.top + triggerRect.height / 2 - y;
      break;
  }

  return { x, y, arrowX, arrowY, actualPosition };
};

const Arrow: React.FC<{ position: TipPosition; x: number; y: number }> = memo(({ position, x, y }) => {
  const rotation = {
    top: 180,
    bottom: 0,
    left: 90,
    right: -90,
  };

  return (
    <div
      className="absolute w-3 h-3 bg-gray-800 transform rotate-45"
      style={{
        left: x - 6,
        top: y - 6,
        transform: `rotate(${rotation[position]}deg)`,
      }}
    />
  );
});

Arrow.displayName = 'Arrow';

const HoverTip: React.FC<HoverTipProps> = memo(({
  content,
  position = 'top',
  delay = 200,
  children,
  className = '',
  maxWidth = 300,
  disabled = false,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [coordinates, setCoordinates] = useState<TipCoordinates | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);
  const tipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const touchStartTimeRef = useRef<number>(0);

  const showTip = useCallback(() => {
    if (disabled) return;

    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current && tipRef.current) {
        const triggerRect = triggerRef.current.getBoundingClientRect();
        const tipRect = tipRef.current.getBoundingClientRect();
        const coords = calculatePosition(
          triggerRect,
          tipRect,
          position,
          window.innerWidth,
          window.innerHeight
        );
        setCoordinates(coords);
        setIsVisible(true);
      }
    }, delay);
  }, [delay, position, disabled]);

  const hideTip = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleTouchStart = useCallback(() => {
    touchStartTimeRef.current = Date.now();
  }, []);

  const handleTouchEnd = useCallback(() => {
    const touchDuration = Date.now() - touchStartTimeRef.current;
    if (touchDuration > 500) {
      showTip();
    }
  }, [showTip]);

  const handleTouchMove = useCallback(() => {
    hideTip();
  }, [hideTip]);

  const animationVariants = {
    top: { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 10 } },
    bottom: { initial: { opacity: 0, y: -10 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -10 } },
    left: { initial: { opacity: 0, x: 10 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: 10 } },
    right: { initial: { opacity: 0, x: -10 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: -10 } },
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTip}
        onMouseLeave={hideTip}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        onTouchMove={handleTouchMove}
        className={`inline-block ${className}`}
      >
        {children}
      </div>

      <AnimatePresence>
        {isVisible && coordinates && (
          <motion.div
            ref={tipRef}
            className="fixed z-[9999] pointer-events-none"
            style={{
              left: coordinates.x,
              top: coordinates.y,
              maxWidth,
            }}
            initial={animationVariants[coordinates.actualPosition].initial}
            animate={animationVariants[coordinates.actualPosition].animate}
            exit={animationVariants[coordinates.actualPosition].exit}
            transition={{ duration: 0.15 }}
          >
            <div className="relative bg-gray-800 text-white text-sm px-3 py-2 rounded-lg shadow-lg">
              <Arrow
                position={coordinates.actualPosition}
                x={coordinates.arrowX}
                y={coordinates.arrowY}
              />
              <div className="relative z-10">{content}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
});

HoverTip.displayName = 'HoverTip';

export const QuickTip: React.FC<{
  text: string;
  children: React.ReactNode;
  position?: TipPosition;
}> = memo(({ text, children, position = 'top' }) => (
  <HoverTip content={text} position={position}>
    {children}
  </HoverTip>
));

QuickTip.displayName = 'QuickTip';

export const RichTip: React.FC<{
  title: string;
  description?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  position?: TipPosition;
}> = memo(({ title, description, icon, children, position = 'top' }) => (
  <HoverTip
    content={
      <div className="flex gap-2">
        {icon && <div className="flex-shrink-0">{icon}</div>}
        <div>
          <div className="font-medium">{title}</div>
          {description && (
            <div className="text-gray-300 text-xs mt-1">{description}</div>
          )}
        </div>
      </div>
    }
    position={position}
  >
    {children}
  </HoverTip>
));

RichTip.displayName = 'RichTip';

export default HoverTip;
