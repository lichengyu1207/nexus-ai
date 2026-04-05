/**
 * 页面过渡动画组件
 * Page Transition Component
 * 
 * 在不同页面切换时提供平滑的过渡动画
 */

import React, { memo, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export type TransitionType = 'slide' | 'fade' | 'scale' | 'flip' | 'blur';

export interface PageTransitionProps {
  children: ReactNode;
  transitionKey: string;
  type?: TransitionType;
  duration?: number;
  className?: string;
}

const transitionVariants = {
  slide: {
    initial: { opacity: 0, x: 100 },
    enter: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -100 },
  },
  fade: {
    initial: { opacity: 0 },
    enter: { opacity: 1 },
    exit: { opacity: 0 },
  },
  scale: {
    initial: { opacity: 0, scale: 0.9 },
    enter: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 1.1 },
  },
  flip: {
    initial: { opacity: 0, rotateY: -90 },
    enter: { opacity: 1, rotateY: 0 },
    exit: { opacity: 0, rotateY: 90 },
  },
  blur: {
    initial: { opacity: 0, filter: 'blur(10px)' },
    enter: { opacity: 1, filter: 'blur(0px)' },
    exit: { opacity: 0, filter: 'blur(10px)' },
  },
};

const PageTransition: React.FC<PageTransitionProps> = memo(({
  children,
  transitionKey,
  type = 'slide',
  duration = 0.3,
  className = '',
}) => {
  const variants = transitionVariants[type];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={transitionKey}
        initial="initial"
        animate="enter"
        exit="exit"
        variants={variants}
        transition={{
          type: 'tween',
          duration,
          ease: [0.4, 0, 0.2, 1],
        }}
        className={className}
        style={{ 
          perspective: type === 'flip' ? 1000 : undefined,
          transformStyle: type === 'flip' ? 'preserve-3d' : undefined,
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
});

PageTransition.displayName = 'PageTransition';

export const PageTransitionWrapper: React.FC<{
  children: ReactNode;
  className?: string;
}> = memo(({ children, className = '' }) => (
  <div className={`relative overflow-hidden ${className}`}>
    {children}
  </div>
));

PageTransitionWrapper.displayName = 'PageTransitionWrapper';

export const SlideTransition: React.FC<{
  children: ReactNode;
  direction?: 'left' | 'right' | 'up' | 'down';
  duration?: number;
}> = memo(({ children, direction = 'right', duration = 0.3 }) => {
  const directionOffset = {
    left: { x: -100, y: 0 },
    right: { x: 100, y: 0 },
    up: { x: 0, y: -100 },
    down: { x: 0, y: 100 },
  };

  const offset = directionOffset[direction];

  return (
    <motion.div
      initial={{ opacity: 0, ...offset }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      exit={{ opacity: 0, x: -offset.x, y: -offset.y }}
      transition={{ type: 'tween', duration, ease: [0.4, 0, 0.2, 1] }}
    >
      {children}
    </motion.div>
  );
});

SlideTransition.displayName = 'SlideTransition';

export const FadeTransition: React.FC<{
  children: ReactNode;
  duration?: number;
}> = memo(({ children, duration = 0.2 }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    transition={{ duration }}
  >
    {children}
  </motion.div>
));

FadeTransition.displayName = 'FadeTransition';

export const ScaleTransition: React.FC<{
  children: ReactNode;
  duration?: number;
  scale?: number;
}> = memo(({ children, duration = 0.3, scale = 0.95 }) => (
  <motion.div
    initial={{ opacity: 0, scale }}
    animate={{ opacity: 1, scale: 1 }}
    exit={{ opacity: 0, scale }}
    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
  >
    {children}
  </motion.div>
));

ScaleTransition.displayName = 'ScaleTransition';

export const ModalTransition: React.FC<{
  children: ReactNode;
  isOpen: boolean;
  onClose: () => void;
}> = memo(({ children, isOpen, onClose }) => (
  <AnimatePresence>
    {isOpen && (
      <>
        <motion.div
          className="fixed inset-0 bg-black/50 z-40"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        />
        <motion.div
          className="fixed inset-0 flex items-center justify-center z-50 p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-auto"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            {children}
          </motion.div>
        </motion.div>
      </>
    )}
  </AnimatePresence>
));

ModalTransition.displayName = 'ModalTransition';

export const ListTransition: React.FC<{
  items: ReactNode[];
  staggerDelay?: number;
}> = memo(({ items, staggerDelay = 0.1 }) => (
  <div className="space-y-2">
    {items.map((item, index) => (
      <motion.div
        key={index}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{
          type: 'spring',
          stiffness: 300,
          damping: 30,
          delay: index * staggerDelay,
        }}
      >
        {item}
      </motion.div>
    ))}
  </div>
));

ListTransition.displayName = 'ListTransition';

export default PageTransition;
