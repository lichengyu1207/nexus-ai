import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MagnifyingGlassIcon, XMarkIcon, DocumentTextIcon, ClipboardDocumentListIcon } from '@heroicons/react/24/outline';
import api from '@/services/api';

interface Suggestion {
  id: string;
  type: string;
  title: string;
}

const SearchBar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const navigate = useNavigate();

  const fetchSuggestions = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setSuggestions([]);
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.get('/search/suggestions', {
        params: { q: searchQuery, limit: 5 },
      });
      setSuggestions(response.data || []);
    } catch {
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (query.trim()) {
      debounceRef.current = setTimeout(() => {
        fetchSuggestions(query);
      }, 500);
    } else {
      setSuggestions([]);
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [query, fetchSuggestions]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
        const activeElement = document.activeElement;
        if (activeElement?.tagName !== 'INPUT' && activeElement?.tagName !== 'TEXTAREA') {
          e.preventDefault();
          inputRef.current?.focus();
        }
      }
      
      if (e.key === 'Escape') {
        setIsOpen(false);
        inputRef.current?.blur();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  const handleSuggestionClick = (suggestion: Suggestion) => {
    if (suggestion.type === 'task') {
      navigate(`/tasks/${suggestion.id}`);
    } else if (suggestion.type === 'report') {
      navigate(`/reports?highlight=${suggestion.id}`);
    }
    setIsOpen(false);
    setQuery('');
  };

  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    inputRef.current?.focus();
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'task':
        return ClipboardDocumentListIcon;
      case 'report':
        return DocumentTextIcon;
      default:
        return DocumentTextIcon;
    }
  };

  return (
    <div className="relative">
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsOpen(true)}
            onBlur={() => setTimeout(() => setIsOpen(false), 200)}
            placeholder="搜索任务、报告... (按 / 快捷键)"
            className="w-64 lg:w-80 pl-9 pr-8 py-2 text-sm bg-gray-100 dark:bg-gray-700 border border-transparent rounded-lg focus:bg-white dark:focus:bg-gray-800 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors"
          />
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </form>

      {isOpen && (suggestions.length > 0 || isLoading) && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-50">
          {isLoading ? (
            <div className="px-4 py-3 text-sm text-gray-500 flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
              搜索中...
            </div>
          ) : (
            <ul>
              {suggestions.map((suggestion) => {
                const Icon = getTypeIcon(suggestion.type);
                return (
                  <li key={suggestion.id}>
                    <button
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full px-4 py-2 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                    >
                      <Icon className="w-4 h-4 text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 dark:text-gray-100 truncate">
                          {suggestion.title}
                        </p>
                        <p className="text-xs text-gray-500">
                          {suggestion.type === 'task' ? '任务' : '报告'}
                        </p>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          
          {query.trim() && !isLoading && (
            <div className="border-t border-gray-100 dark:border-gray-700">
              <button
                onClick={handleSubmit}
                className="w-full px-4 py-2 text-sm text-primary-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
              >
                查看全部结果...
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
