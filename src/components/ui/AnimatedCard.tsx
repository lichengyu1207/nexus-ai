import React from 'react';
import { motion, Variants } from 'framer-motion';
import clsx from 'clsx';

type CardVariant = 'default' | 'glass' | 'elevated' | 'bordered';

interface AnimatedCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  hoverScale?: number;
  hoverShadow?: boolean;
  glowOnHover?: boolean;
  delay?: number;
  animateOnMount?: boolean;
}

const variantClasses: Record<CardVariant, string> = {
  default: 'bg-bg-secondary',
  glass: 'bg-white/5 backdrop-blur-md border border-white/10',
  elevated: 'bg-bg-secondary shadow-lg',
  bordered: 'bg-bg-secondary border border-border-light',
};

const cardVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 20,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 25,
    },
  },
  hover: {
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 20,
    },
  },
  tap: {
    scale: 0.98,
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 20,
    },
  },
};

export const AnimatedCard: React.FC<AnimatedCardProps> = ({
  variant = 'default',
  hoverScale = 1.02,
  hoverShadow = true,
  glowOnHover = false,
  delay = 0,
  animateOnMount = true,
  children,
  className,
  onClick,
  ...props
}) => {
  const isClickable = !!onClick;

  const getHoverShadow = () => {
    if (!hoverShadow) return undefined;
    return glowOnHover
      ? '0 10px 40px -10px rgba(255, 217, 102, 0.3), 0 4px 20px -5px rgba(0, 0, 0, 0.3)'
      : '0 10px 25px -5px rgba(0, 0, 0, 0.3)';
  };

  return (
    <motion.div
      className={clsx(
        'rounded-xl p-4 transition-colors duration-200',
        variantClasses[variant],
        isClickable && 'cursor-pointer',
        className
      )}
      variants={cardVariants}
      initial={animateOnMount ? 'hidden' : 'visible'}
      animate="visible"
      whileHover={{
        scale: hoverScale,
        boxShadow: getHoverShadow(),
        borderColor: glowOnHover ? 'rgba(255, 217, 102, 0.3)' : undefined,
      }}
      whileTap={isClickable ? 'tap' : undefined}
      transition={{
        delay: animateOnMount ? delay : 0,
      }}
      onClick={onClick}
      {...props}
    >
      {children}
    </motion.div>
  );
};

interface AnimatedCardGridProps {
  children: React.ReactNode;
  className?: string;
  staggerDelay?: number;
}

export const AnimatedCardGrid: React.FC<AnimatedCardGridProps> = ({
  children,
  className,
  staggerDelay = 0.1,
}) => {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: staggerDelay,
      },
    },
  };

  return (
    <motion.div
      className={clsx('grid gap-4', className)}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {children}
    </motion.div>
  );
};

export default AnimatedCard;
