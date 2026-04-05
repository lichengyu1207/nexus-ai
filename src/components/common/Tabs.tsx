import React from 'react';
import { motion } from 'framer-motion';

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'line' | 'pills' | 'enclosed';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

const sizeStyles = {
  sm: 'text-sm py-1.5 px-3',
  md: 'text-sm py-2 px-4',
  lg: 'text-base py-3 px-5',
};

const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  variant = 'line',
  size = 'md',
  fullWidth = false,
}) => {
  const baseStyles = 'relative font-medium transition-colors';
  const containerStyles = {
    line: 'border-b border-gray-200 dark:border-gray-700',
    pills: 'bg-gray-100 dark:bg-gray-800 rounded-xl p-1',
    enclosed: 'bg-gray-100 dark:bg-gray-800 rounded-t-xl',
  };

  const tabStyles = {
    line: {
      active: 'text-primary-600 dark:text-primary-400',
      inactive: 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200',
    },
    pills: {
      active: 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm',
      inactive: 'text-gray-500 hover:text-gray-700 dark:text-gray-400',
    },
    enclosed: {
      active: 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border-b-2 border-primary-500',
      inactive: 'text-gray-500 hover:text-gray-700 dark:text-gray-400',
    },
  };

  return (
    <div className={`${containerStyles[variant]} ${fullWidth ? 'flex' : 'inline-flex'}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => !tab.disabled && onChange(tab.id)}
          disabled={tab.disabled}
          className={`
            ${baseStyles} ${sizeStyles[size]}
            ${tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            ${activeTab === tab.id ? tabStyles[variant].active : tabStyles[variant].inactive}
            ${fullWidth ? 'flex-1' : ''}
            ${variant === 'pills' ? 'rounded-lg' : ''}
            ${variant === 'enclosed' ? 'rounded-t-lg px-4' : ''}
            flex items-center gap-2 justify-center
          `}
        >
          {tab.icon}
          {tab.label}
          {variant === 'line' && activeTab === tab.id && (
            <motion.div
              layoutId="activeTab"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            />
          )}
        </button>
      ))}
    </div>
  );
};

export default Tabs;
