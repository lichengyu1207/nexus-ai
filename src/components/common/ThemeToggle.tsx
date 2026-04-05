import React from 'react';
import { motion } from 'framer-motion';
import { SunIcon, MoonIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

type Theme = 'light' | 'dark' | 'system';

interface ThemeToggleProps {
  variant?: 'icon' | 'dropdown' | 'buttons';
  className?: string;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({
  variant = 'icon',
  className = '',
}) => {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useTheme();

  if (variant === 'icon') {
    return (
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={toggleTheme}
        className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${className}`}
        title={`当前主题: ${resolvedTheme === 'dark' ? '深色' : '浅色'}`}
      >
        <motion.div
          initial={false}
          animate={{ rotate: resolvedTheme === 'dark' ? 180 : 0 }}
          transition={{ duration: 0.3 }}
        >
          {resolvedTheme === 'dark' ? (
            <MoonIcon className="w-5 h-5 text-yellow-400" />
          ) : (
            <SunIcon className="w-5 h-5 text-yellow-500" />
          )}
        </motion.div>
      </motion.button>
    );
  }

  if (variant === 'buttons') {
    const options: { value: Theme; icon: React.ReactNode; label: string }[] = [
      { value: 'light', icon: <SunIcon className="w-4 h-4" />, label: '浅色' },
      { value: 'dark', icon: <MoonIcon className="w-4 h-4" />, label: '深色' },
      { value: 'system', icon: <ComputerDesktopIcon className="w-4 h-4" />, label: '系统' },
    ];

    return (
      <div className={`flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl ${className}`}>
        {options.map((option) => (
          <motion.button
            key={option.value}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setTheme(option.value)}
            className={`
              flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
              ${theme === option.value
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }
            `}
          >
            {option.icon}
            {option.label}
          </motion.button>
        ))}
      </div>
    );
  }

  return null;
};

export default ThemeToggle;
