import { useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FixedSizeList as List } from 'react-window';
import type { CallLog, CallResult } from '../types';

interface CallLogListProps {
  logs: CallLog[];
  onLogClick: (log: CallLog) => void;
  autoScroll?: boolean;
}

const resultConfig: Record<CallResult, { icon: string; color: string }> = {
  success: { icon: '✓', color: 'text-green-400' },
  failure: { icon: '✗', color: 'text-red-400' },
};

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatDuration(ms?: number): string {
  if (!ms) return '-';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function CallLogList({ logs, onLogClick, autoScroll = true }: CallLogListProps) {
  const listRef = useRef<List>(null);
  const prevLogsLengthRef = useRef(0);

  useEffect(() => {
    if (autoScroll && logs.length > prevLogsLengthRef.current && listRef.current) {
      listRef.current.scrollToItem(logs.length - 1, 'end');
    }
    prevLogsLengthRef.current = logs.length;
  }, [logs.length, autoScroll]);

  const Row = useCallback(
    ({ index, style }: { index: number; style: React.CSSProperties }) => {
      const log = logs[index];
      const config = resultConfig[log.result];

      return (
        <div style={style}>
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            onClick={() => onLogClick(log)}
            className="mx-2 mb-2 p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50
              cursor-pointer transition-colors border border-transparent hover:border-amber-500/30"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500">{formatTime(log.timestamp)}</span>
              <div className="flex items-center gap-2">
                {log.duration && (
                  <span className="text-xs text-gray-500">{formatDuration(log.duration)}</span>
                )}
                <span className={`text-sm font-bold ${config.color}`}>
                  {config.icon}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-white text-sm truncate">{log.agentName}</span>
              <span className="text-gray-500">→</span>
              <span className="text-amber-400 text-sm truncate">{log.toolName}</span>
            </div>
          </motion.div>
        </div>
      );
    },
    [logs, onLogClick]
  );

  if (logs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        暂无调用日志
      </div>
    );
  }

  return (
    <div role="log" aria-live="polite" aria-label="调用日志列表">
      <List
        ref={listRef}
        height={300}
        itemCount={logs.length}
        itemSize={72}
        width="100%"
        className="scrollbar-thin scrollbar-thumb-amber-500/30 scrollbar-track-slate-800"
      >
        {Row}
      </List>
    </div>
  );
}
