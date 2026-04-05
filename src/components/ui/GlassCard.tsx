import React from 'react';
import clsx from 'clsx';
import { motion, HTMLMotionProps } from 'framer-motion';

interface GlassCardProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode;
  hover?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className,
  hover = true,
  ...props
}) => {
  return (
    <motion.div
      className={clsx(
        'bg-bg-glass backdrop-blur-md border border-white/10 rounded-xl shadow-md p-5',
        hover && 'hover:border-primary/30 hover:shadow-lg',
        'transition-all duration-200',
        className
      )}
      whileHover={hover ? { scale: 1.01 } : undefined}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default GlassCard;
