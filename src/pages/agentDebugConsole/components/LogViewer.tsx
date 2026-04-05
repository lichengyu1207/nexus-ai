import { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FixedSizeList as List } from 'react-window';
import { XMarkIcon, FunnelIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import type { LogEntry, LogLevel } from '../types';
import { LOG_LEVEL_CONFIG } from '../types';

interface LogViewerProps {
  logs: LogEntry[];
  onClear?: () => void;
  onExport?: () => void;
  isLoading?: boolean;
  maxLines?: number;
}

const LogLine = ({ log, style }: { log: LogEntry; style: React.CSSProperties }) => {
  const config = LOG_LEVEL_CONFIG[log.level];
  const timestamp = new Date(log.timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });

  return (
    <div style={style} className="flex items-start gap-3 px-3 py-1.5 hover:bg-slate-800/30">
      <span className={`text-xs font-mono ${config.color} w-16 flex-shrink-0`}>
        {config.label.pad(5)}
      </span>
      <span className="text-xs text-slate-500 font-mono w-24 flex-shrink-0">
        {timestamp}
      </span>
      <span className="text-xs text-slate-400 font-mono w-32 truncate flex-shrink-0" title={log.source}>
        {log.source}
      </span>
      <span className="text-sm text-slate-200 flex-1 break-all">
        {log.message}
      </span>
    </div>
  );
};

export function LogViewer({
  logs,
  onClear,
  onExport,
  isLoading = false,
  maxLines = 1000,
}: LogViewerProps) {
  const [filterLevel, setFilterLevel] = useState<LogLevel | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const listRef = useRef<List>(null);

  const filteredLogs = useMemo(() => {
    let result = logs;
    if (filterLevel) {
      result = result.filter((log) => log.level === filterLevel);
    }
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (log) =>
          log.message.toLowerCase().includes(term) ||
          log.source.toLowerCase().includes(term)
      );
    }
    return result.slice(-maxLines);
  }, [logs, filterLevel, searchTerm, maxLines]);

  useEffect(() => {
    if (autoScroll && listRef.current) {
      listRef.current.scrollToItem(filteredLogs.length - 1);
    }
  }, [filteredLogs.length, autoScroll]);

  const handleExport = () => {
    const content = filteredLogs
      .map((log) => `[${LOG_LEVEL_CONFIG[log.level].label}] ${log.timestamp} ${log.source}: ${log.message}`)
      .join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debug-logs-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    onExport?.();
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-900/50 rounded-xl border border-slate-700/50">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-white">
            日志 ({filteredLogs.length})
          </span>
          <div className="flex items-center gap-1">
            {(['debug', 'info', 'warning', 'error', 'critical'] as LogLevel[]).map((level) => (
              <button
                key={level}
                onClick={() => setFilterLevel(filterLevel === level ? null : level)}
                className={`
                  px-2 py-1 text-xs rounded-lg transition-colors
                  ${filterLevel === level 
                    ? `${LOG_LEVEL_CONFIG[level].bgColor} ${LOG_LEVEL_CONFIG[level].color}` 
                    : 'bg-slate-700/50 text-slate-400 hover:bg-slate-700'}
                `}
              >
                {LOG_LEVEL_CONFIG[level].label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="搜索日志..."
            className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700/50 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 w-40"
          />
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1.5 rounded-lg transition-colors ${autoScroll ? 'bg-amber-500/20 text-amber-400' : 'text-slate-400 hover:bg-slate-700/50'}`}
            title={autoScroll ? '停止自动滚动' : '开启自动滚动'}
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
          </button>
          {onExport && (
            <button
              onClick={handleExport}
              className="p-1.5 text-slate-400 hover:text-amber-400 transition-colors"
              title="导出日志"
            >
              <ArrowDownTrayIcon className="w-4 h-4 rotate-180" />
            </button>
          )}
          {onClear && (
            <button
              onClick={onClear}
              className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
              title="清空日志"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1">
        {filteredLogs.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500">
            {searchTerm || filterLevel ? '没有匹配的日志' : '暂无日志'}
          </div>
        ) : (
          <List
            ref={listRef}
            height={400}
            itemCount={filteredLogs.length}
            itemSize={32}
            width="100%"
            className="scrollbar-thin"
          >
            {({ index, style }) => (
              <LogLine log={filteredLogs[index]} style={style} />
            )}
          </List>
        )}
      </div>
    </div>
  );
}
