import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { RunLog } from '../types';
import { useRunLogs } from '../hooks/useRunLogs';

interface RunLogsViewProps {
  agentId: string;
}

const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  return `${(ms / 60000).toFixed(2)}min`;
};

const LogDetailPanel: React.FC<{
  log: RunLog;
  onClose: () => void;
}> = ({ log, onClose }) => {
  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      className="overflow-hidden border-t border-border-light"
    >
      <div className="p-4 bg-bg-tertiary/30">
        <div className="flex justify-between items-start mb-3">
          <h4 className="text-sm font-medium text-text-primary">详细信息</h4>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <span className="text-xs text-text-secondary">任务ID</span>
            <p className="text-sm text-text-primary font-mono">{log.taskId}</p>
          </div>
          <div>
            <span className="text-xs text-text-secondary">耗时</span>
            <p className="text-sm text-text-primary">{formatDuration(log.duration)}</p>
          </div>
        </div>

        <div className="mb-4">
          <span className="text-xs text-text-secondary">输出摘要</span>
          <p className="text-sm text-text-primary mt-1 p-2 bg-bg-secondary/50 rounded-lg">
            {log.outputSummary}
          </p>
        </div>

        {log.fullOutput && (
          <div className="mb-4">
            <span className="text-xs text-text-secondary">完整输出</span>
            <pre className="text-xs text-text-primary mt-1 p-2 bg-bg-secondary/50 rounded-lg overflow-x-auto max-h-40 scrollbar-thin">
              {log.fullOutput}
            </pre>
          </div>
        )}

        {log.error && (
          <div>
            <span className="text-xs text-red-400">错误信息</span>
            <pre className="text-xs text-red-400 mt-1 p-2 bg-red-500/10 rounded-lg overflow-x-auto max-h-40 scrollbar-thin">
              {log.error}
            </pre>
          </div>
        )}
      </div>
    </motion.div>
  );
};

const LoadingSpinner: React.FC = () => (
  <div className="flex justify-center py-8">
    <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
  </div>
);

export const RunLogsView: React.FC<RunLogsViewProps> = ({ agentId }) => {
  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useRunLogs(agentId);

  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const lastLogElementRef = useCallback(
    (node: HTMLDivElement) => {
      if (isLoading) return;

      if (observerRef.current) {
        observerRef.current.disconnect();
      }

      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      });

      if (node) {
        observerRef.current.observe(node);
      }
    },
    [isLoading, hasNextPage, isFetchingNextPage, fetchNextPage]
  );

  const allLogs = data?.pages.flatMap((page) => page.logs) ?? [];

  if (isLoading) {
    return (
      <div className="p-4">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-400">
        <p>加载运行日志失败</p>
      </div>
    );
  }

  if (allLogs.length === 0) {
    return (
      <div className="p-8 text-center text-text-secondary">
        <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p>暂无运行日志</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-bg-tertiary scrollbar-track-transparent">
      <div className="divide-y divide-border-light">
        <AnimatePresence>
          {allLogs.map((log, index) => {
            const isExpanded = expandedLogId === log.id;
            const isLast = index === allLogs.length - 1;

            return (
              <div key={log.id} ref={isLast ? lastLogElementRef : undefined}>
                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                  className={clsx(
                    'w-full text-left p-4 hover:bg-bg-tertiary/30 transition-colors',
                    isExpanded && 'bg-bg-tertiary/20'
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span
                        className={clsx(
                          'w-2 h-2 rounded-full',
                          log.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                        )}
                      />
                      <span className="font-mono text-sm text-text-primary">
                        {log.taskId.slice(0, 8)}...
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-text-secondary">
                      <span>{formatDuration(log.duration)}</span>
                      <span>{formatDateTime(log.startTime)}</span>
                      <motion.svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        animate={{ rotate: isExpanded ? 180 : 0 }}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </motion.svg>
                    </div>
                  </div>

                  <p className="text-sm text-text-secondary line-clamp-1">
                    {log.outputSummary}
                  </p>
                </motion.button>

                <AnimatePresence>
                  {isExpanded && (
                    <LogDetailPanel
                      log={log}
                      onClose={() => setExpandedLogId(null)}
                    />
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </AnimatePresence>
      </div>

      {isFetchingNextPage && (
        <div className="py-4">
          <LoadingSpinner />
        </div>
      )}

      {!hasNextPage && allLogs.length > 0 && (
        <div className="py-4 text-center text-xs text-text-secondary">
          已加载全部日志
        </div>
      )}
    </div>
  );
};

export default RunLogsView;
