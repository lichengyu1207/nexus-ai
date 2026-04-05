import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaperAirplaneIcon, ClockIcon } from '@heroicons/react/24/outline';
import type { DebugCommand } from '../types';

interface CommandPanelProps {
  onExecute: (command: string, payload?: unknown) => void;
  history?: string[];
  isLoading?: boolean;
  placeholder?: string;
}

export function CommandPanel({
  onExecute,
  history = [],
  isLoading = false,
  placeholder = '输入调试命令...',
}: CommandPanelProps) {
  const [input, setInput] = useState('');
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [showHistory, setShowHistory] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const historyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (history.length > 0) {
          const newIndex = historyIndex < history.length - 1 ? historyIndex + 1 : historyIndex;
          setHistoryIndex(newIndex);
          setInput(history[history.length - 1 - newIndex] || '');
        }
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (historyIndex > 0) {
          const newIndex = historyIndex - 1;
          setHistoryIndex(newIndex);
          setInput(history[history.length - 1 - newIndex] || '');
        } else if (historyIndex === 0) {
          setHistoryIndex(-1);
          setInput('');
        }
      }
    };

    inputRef.current?.addEventListener('keydown', handleKeyDown);
    return () => {
      inputRef.current?.removeEventListener('keydown', handleKeyDown);
    };
  }, [history, historyIndex]);

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    onExecute(input.trim());
    setInput('');
    setHistoryIndex(-1);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleHistoryClick = (cmd: string) => {
    setInput(cmd);
    setShowHistory(false);
    inputRef.current?.focus();
  };

  const quickCommands = [
    { label: '查看状态', command: 'state' },
    { label: '查看变量', command: 'vars' },
    { label: '查看调用栈', command: 'stack' },
    { label: '继续执行', command: 'continue' },
  ];

  return (
    <div className="flex flex-col bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-700/50">
        <span className="text-xs text-slate-500">快捷命令:</span>
        <div className="flex items-center gap-1">
          {quickCommands.map((cmd) => (
            <button
              key={cmd.command}
              onClick={() => onExecute(cmd.command)}
              className="px-2 py-0.5 text-xs bg-slate-700/50 text-slate-400 rounded hover:bg-slate-700 hover:text-white transition-colors"
            >
              {cmd.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2 p-3">
        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            onFocus={() => history.length > 0 && setShowHistory(true)}
            onBlur={() => setTimeout(() => setShowHistory(false), 200)}
            placeholder={placeholder}
            disabled={isLoading}
            className="w-full px-4 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 disabled:opacity-50"
          />

          <AnimatePresence>
            {showHistory && history.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                ref={historyRef}
                className="absolute bottom-full left-0 right-0 mb-1 bg-slate-800 border border-slate-700/50 rounded-lg shadow-xl max-h-40 overflow-y-auto"
              >
                {history.slice(-10).reverse().map((cmd, index) => (
                  <button
                    key={index}
                    onClick={() => handleHistoryClick(cmd)}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-slate-700/50 transition-colors"
                  >
                    <ClockIcon className="w-4 h-4 text-slate-500 flex-shrink-0" />
                    <span className="text-slate-300 truncate">{cmd}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-slate-900 font-medium rounded-lg hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-slate-900 border-t-transparent" />
          ) : (
            <PaperAirplaneIcon className="w-4 h-4" />
          )}
          <span className="hidden sm:inline">执行</span>
        </motion.button>
      </div>
    </div>
  );
}
