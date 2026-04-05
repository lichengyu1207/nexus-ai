import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRightIcon, ChevronDownIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import type { Variable } from '../types';

interface VariableInspectorProps {
  variables: Variable[];
  onVariableClick?: (variable: Variable) => void;
  searchPlaceholder?: string;
}

const VariableValue = ({ value, depth = 0 }: { value: unknown; depth?: number }) => {
  const [isExpanded, setIsExpanded] = useState(depth < 2);

  if (value === null) {
    return <span className="text-slate-500 italic">null</span>;
  }

  if (value === undefined) {
    return <span className="text-slate-500 italic">undefined</span>;
  }

  if (typeof value === 'boolean') {
    return <span className={value ? 'text-green-400' : 'text-red-400'}>{String(value)}</span>;
  }

  if (typeof value === 'number') {
    return <span className="text-blue-400">{String(value)}</span>;
  }

  if (typeof value === 'string') {
    const displayValue = value.length > 100 ? `${value.slice(0, 100)}...` : value;
    return <span className="text-amber-400">"{displayValue}"</span>;
  }

  if (Array.isArray(value)) {
    return (
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-slate-400 hover:text-white transition-colors"
        >
          {isExpanded ? <ChevronDownIcon className="w-3 h-3" /> : <ChevronRightIcon className="w-3 h-3" />}
          <span className="text-slate-500">Array({value.length})</span>
        </button>
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="ml-4 overflow-hidden"
            >
              {value.map((item, index) => (
                <div key={index} className="flex items-start gap-2 py-0.5">
                  <span className="text-slate-500 text-xs">{index}:</span>
                  <VariableValue value={item} depth={depth + 1} />
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value);
    return (
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-slate-400 hover:text-white transition-colors"
        >
          {isExpanded ? <ChevronDownIcon className="w-3 h-3" /> : <ChevronRightIcon className="w-3 h-3" />}
          <span className="text-slate-500">Object({entries.length})</span>
        </button>
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="ml-4 overflow-hidden"
            >
              {entries.map(([key, val]) => (
                <div key={key} className="flex items-start gap-2 py-0.5">
                  <span className="text-amber-400 text-xs">{key}:</span>
                  <VariableValue value={val} depth={depth + 1} />
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return <span className="text-slate-300">{String(value)}</span>;
};

export function VariableInspector({
  variables,
  onVariableClick,
  searchPlaceholder = '搜索变量...',
}: VariableInspectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedScopes, setExpandedScopes] = useState<Set<string>>(new Set(['global']));

  const filteredVariables = useMemo(() => {
    if (!searchTerm) return variables;
    const term = searchTerm.toLowerCase();
    return variables.filter(
      (v) =>
        v.name.toLowerCase().includes(term) ||
        String(v.value).toLowerCase().includes(term)
    );
  }, [variables, searchTerm]);

  const groupedVariables = useMemo(() => {
    const groups: Record<string, Variable[]> = {};
    filteredVariables.forEach((v) => {
      if (!groups[v.scope]) {
        groups[v.scope] = [];
      }
      groups[v.scope].push(v);
    });
    return groups;
  }, [filteredVariables]);

  const toggleScope = (scope: string) => {
    setExpandedScopes((prev) => {
      const next = new Set(prev);
      if (next.has(scope)) {
        next.delete(scope);
      } else {
        next.add(scope);
      }
      return next;
    });
  };

  const getScopeColor = (scope: string) => {
    switch (scope) {
      case 'global':
        return 'text-amber-400';
      case 'local':
        return 'text-blue-400';
      case 'closure':
        return 'text-purple-400';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/50 rounded-xl border border-slate-700/50">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700/50">
        <MagnifyingGlassIcon className="w-4 h-4 text-slate-500" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={searchPlaceholder}
          className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none"
        />
        <span className="text-xs text-slate-500">{variables.length} 个变量</span>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {Object.entries(groupedVariables).map(([scope, vars]) => (
          <div key={scope}>
            <button
              onClick={() => toggleScope(scope)}
              className="flex items-center gap-2 w-full px-4 py-2 text-sm font-medium hover:bg-slate-800/50 transition-colors"
            >
              {expandedScopes.has(scope) ? (
                <ChevronDownIcon className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronRightIcon className="w-4 h-4 text-slate-400" />
              )}
              <span className={getScopeColor(scope)}>{scope}</span>
              <span className="text-slate-500 text-xs">({vars.length})</span>
            </button>

            <AnimatePresence>
              {expandedScopes.has(scope) && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  {vars.map((variable) => (
                    <div
                      key={variable.name}
                      onClick={() => onVariableClick?.(variable)}
                      className={`
                        flex items-start gap-3 px-4 py-1.5 cursor-pointer transition-colors
                        ${variable.modified ? 'bg-amber-500/5' : 'hover:bg-slate-800/50'}
                      `}
                    >
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <span className="text-sm text-white truncate">{variable.name}</span>
                        <span className="text-xs text-slate-500">{variable.type}</span>
                        {variable.modified && (
                          <span className="text-xs text-amber-400">modified</span>
                        )}
                      </div>
                      <div className="text-xs max-w-[200px] truncate">
                        <VariableValue value={variable.value} />
                      </div>
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </div>
  );
}
