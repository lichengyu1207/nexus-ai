import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { brandCopy } from '@/config/brand';

interface BrandStoryProps {
  variant?: 'full' | 'compact';
  className?: string;
}

export const BrandStory: React.FC<BrandStoryProps> = ({
  variant = 'full',
  className,
}) => {
  const storyLines = brandCopy.story.filter((line) => line.length > 0);

  if (variant === 'compact') {
    return (
      <div className={clsx('text-center', className)}>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-lg text-text-secondary max-w-2xl mx-auto"
        >
          {brandCopy.story[0]}
          <br />
          <span className="text-primary font-semibold">
            {brandCopy.story[1]}
          </span>
        </motion.p>
      </div>
    );
  }

  return (
    <div className={clsx('max-w-3xl mx-auto', className)}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="relative"
      >
        <div className="absolute left-0 top-0 bottom-0 w-px bg-gradient-to-b from-primary/50 via-primary/30 to-transparent" />
        
        <div className="pl-6 space-y-4">
          {storyLines.map((line, index) => (
            <motion.p
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={clsx(
                'text-lg leading-relaxed',
                line.includes('房都督') && line.includes('第六个选择')
                  ? 'text-primary font-semibold text-xl'
                  : 'text-text-secondary',
                line.startsWith('我们') && 'pl-4 border-l-2 border-primary/30',
                line.startsWith('你的') && 'pl-4 border-l-2 border-blue-400/30',
                line.startsWith('报告') && 'pl-4 border-l-2 border-green-400/30',
                line.startsWith('这不是') && 'mt-6 text-primary font-medium'
              )}
            >
              {line}
            </motion.p>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="mt-12 text-center"
      >
        <p className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          {brandCopy.slogan.alternative}
        </p>
      </motion.div>
    </div>
  );
};

export default BrandStory;
