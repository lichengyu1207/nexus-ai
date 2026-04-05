import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle: React.FC = () => {
  const { actualTheme, toggleTheme } = useTheme();

  return (
    <button
      className="theme-toggle"
      onClick={toggleTheme}
      aria-label={actualTheme === 'light' ? '切换到深色模式' : '切换到浅色模式'}
    >
      {actualTheme === 'light' ? '🌙' : '☀️'}
    </button>
  );
};

export default ThemeToggle;
