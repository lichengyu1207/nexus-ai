import React, { useState, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: (query: string) => void;
  placeholder?: string;
  debounceMs?: number;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onSearch,
  placeholder = '搜索记忆内容...',
  debounceMs = 300,
}) => {
  const [localValue, setLocalValue] = useState(value);
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (localValue !== value) {
        onChange(localValue);
        if (localValue.length >= 2 || localValue.length === 0) {
          onSearch(localValue);
        }
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [localValue, debounceMs, onChange, onSearch, value]);

  const handleClear = useCallback(() => {
    setLocalValue('');
    onChange('');
    onSearch('');
  }, [onChange, onSearch]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        onSearch(localValue);
      } else if (e.key === 'Escape') {
        handleClear();
      }
    },
    [localValue, onSearch, handleClear]
  );

  return (
    <motion.div
      className={clsx(
        'relative flex items-center',
        'bg-bg-secondary/60 backdrop-blur-md rounded-lg border transition-all',
        isFocused
          ? 'border-primary/50 shadow-lg shadow-primary/5'
          : 'border-border-light'
      )}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <svg
        className="absolute left-3 w-5 h-5 text-text-secondary"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>

      <input
        type="text"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-full pl-10 pr-10 py-2.5 text-sm bg-transparent text-text-primary placeholder-text-secondary focus:outline-none"
        aria-label="搜索记忆"
      />

      {localValue && (
        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          onClick={handleClear}
          className="absolute right-3 p-1 text-text-secondary hover:text-text-primary transition-colors"
          aria-label="清除搜索"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </motion.button>
      )}
    </motion.div>
  );
};

export default SearchBar;
