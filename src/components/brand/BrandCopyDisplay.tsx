import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import { brandCopy, CopyScenario } from '@/config/brand';

interface BrandCopyDisplayProps {
  scenario: CopyScenario;
  variant?: 'default' | 'minimal';
  className?: string;
  showSlogan?: boolean;
}

const scenarioConfig: Record<CopyScenario, { icon: string; gradient: string }> = {
  hero: {
    icon: '🏠',
    gradient: 'from-blue-600 to-purple-600',
  },
  consulting: {
    icon: '🎯',
    gradient: 'from-amber-500 to-orange-600',
  },
  brandManual: {
    icon: '📖',
    gradient: 'from-emerald-500 to-teal-600',
  },
};

export const BrandCopyDisplay: React.FC<BrandCopyDisplayProps> = ({
  scenario,
  variant = 'default',
  className,
  showSlogan = false,
}) => {
  const copy = brandCopy[scenario];
  const config = scenarioConfig[scenario];

  if (variant === 'minimal') {
    return (
      <div className={clsx('text-center', className)}>
        <h2 className="text-2xl font-bold text-text-primary mb-2">
          {copy.mainTitle}
        </h2>
        <p className="text-text-secondary">{copy.subTitle}</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx('text-center', className)}
    >
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-bg-secondary/60 backdrop-blur-md border border-border-light mb-6">
        <span className="text-3xl">{config.icon}</span>
      </div>

      <h2 className="text-3xl md:text-4xl font-extrabold text-text-primary mb-4">
        {copy.mainTitle}
      </h2>

      <p className={clsx(
        'text-lg md:text-xl',
        `bg-gradient-to-r ${config.gradient} bg-clip-text text-transparent`
      )}>
        {copy.subTitle}
      </p>

      {showSlogan && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8 pt-6 border-t border-border-light"
        >
          <p className="text-sm text-text-secondary uppercase tracking-wider mb-2">
            品牌口号
          </p>
          <p className="text-lg font-medium text-text-primary">
            {brandCopy.slogan.simplified}
          </p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default BrandCopyDisplay;
