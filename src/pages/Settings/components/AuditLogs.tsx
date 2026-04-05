import { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { FixedSizeList as List } from 'react-window';
import { useAuditLogs } from '../hooks/useAuditLogs';
import type { AuditLogEntry, AuditLogFilters, ActionResult } from '../types';

const resultConfig: Record<ActionResult, { label: string; color: string }> = {
  success: { label: '成功', color: 'text-green-400 bg-green-500/20' },
  failure: { label: '失败', color: 'text-red-400 bg-red-500/20' },
};

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString('zh-CN');
}

export function AuditLogs() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AuditLogFilters>({});
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const listRef = useRef<List>(null);

  const { logs, total, isLoading, exportLogs } = useAuditLogs({ page, filters });

  const handleFilterChange = (key: keyof AuditLogFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
    setPage(1);
  };

  const Row = useCallback(
    ({ index, style }: { index: number; style: React.CSSProperties }) => {
      const log = logs[index];
      if (!log) return null;

      return (
        <div
          style={style}
          onClick={() => setSelectedLog(log)}
          className="flex items-center px-4 py-3 border-b border-slate-700/30 cursor-pointer
            hover:bg-slate-700/30 transition-colors"
        >
          <div className="w-40 text-sm text-gray-400">
            {formatTimestamp(log.timestamp)}
          </div>
          <div className="w-32">
            <span className="text-white">{log.actor}</span>
            <span className="text-xs text-gray-500 ml-1">
              ({log.actorType === 'user' ? '用户' : '智能体'})
            </span>
          </div>
          <div className="flex-1 text-gray-300 truncate">{log.action}</div>
          <div className="w-32 text-gray-400 truncate">{log.target}</div>
          <div className="w-20">
            <span className={`px-2 py-0.5 rounded text-xs ${resultConfig[log.result].color}`}>
              {resultConfig[log.result].label}
            </span>
          </div>
          <div className="w-28 text-gray-500 text-sm">{log.ipAddress || '-'}</div>
        </div>
      );
    },
    [logs]
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-700/50 pb-4">
        <h2 className="text-xl font-semibold text-white">审计日志</h2>
        <p className="text-gray-400 text-sm mt-1">查看所有操作记录</p>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <input
          type="date"
          value={filters.startDate || ''}
          onChange={(e) => handleFilterChange('startDate', e.target.value)}
          className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm"
          placeholder="开始日期"
        />
        <input
          type="date"
          value={filters.endDate || ''}
          onChange={(e) => handleFilterChange('endDate', e.target.value)}
          className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm"
          placeholder="结束日期"
        />
        <input
          type="text"
          value={filters.actor || ''}
          onChange={(e) => handleFilterChange('actor', e.target.value)}
          placeholder="操作人"
          className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm"
        />
        <select
          value={filters.result || ''}
          onChange={(e) => handleFilterChange('result', e.target.value as ActionResult)}
          className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm"
        >
          <option value="">全部结果</option>
          <option value="success">成功</option>
          <option value="failure">失败</option>
        </select>
        <button
          onClick={exportLogs}
          className="px-4 py-2 rounded-lg bg-green-500/20 text-green-400 text-sm
            hover:bg-green-500/30 transition-colors"
        >
          📥 导出
        </button>
      </div>

      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="flex items-center px-4 py-3 bg-slate-900/50 border-b border-slate-700/50">
          <div className="w-40 text-sm font-medium text-gray-400">时间</div>
          <div className="w-32 text-sm font-medium text-gray-400">操作人</div>
          <div className="flex-1 text-sm font-medium text-gray-400">动作</div>
          <div className="w-32 text-sm font-medium text-gray-400">对象</div>
          <div className="w-20 text-sm font-medium text-gray-400">结果</div>
          <div className="w-28 text-sm font-medium text-gray-400">IP地址</div>
        </div>

        {logs.length > 100 ? (
          <List
            ref={listRef}
            height={400}
            itemCount={logs.length}
            itemSize={56}
            width="100%"
          >
            {Row}
          </List>
        ) : (
          <div className="divide-y divide-slate-700/30">
            {logs.map((log, index) => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.02 }}
                onClick={() => setSelectedLog(log)}
                className="flex items-center px-4 py-3 cursor-pointer hover:bg-slate-700/30 transition-colors"
              >
                <div className="w-40 text-sm text-gray-400">
                  {formatTimestamp(log.timestamp)}
                </div>
                <div className="w-32">
                  <span className="text-white">{log.actor}</span>
                  <span className="text-xs text-gray-500 ml-1">
                    ({log.actorType === 'user' ? '用户' : '智能体'})
                  </span>
                </div>
                <div className="flex-1 text-gray-300 truncate">{log.action}</div>
                <div className="w-32 text-gray-400 truncate">{log.target}</div>
                <div className="w-20">
                  <span className={`px-2 py-0.5 rounded text-xs ${resultConfig[log.result].color}`}>
                    {resultConfig[log.result].label}
                  </span>
                </div>
                <div className="w-28 text-gray-500 text-sm">{log.ipAddress || '-'}</div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-gray-400 text-sm">共 {total} 条记录</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 rounded-lg bg-slate-700 text-gray-300 text-sm
              disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600"
          >
            上一页
          </button>
          <span className="px-3 py-1.5 text-gray-400 text-sm">第 {page} 页</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={logs.length < 20}
            className="px-3 py-1.5 rounded-lg bg-slate-700 text-gray-300 text-sm
              disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-600"
          >
            下一页
          </button>
        </div>
      </div>

      {selectedLog && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 flex items-center justify-center"
          onClick={() => setSelectedLog(null)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-slate-800 rounded-xl p-6 w-full max-w-lg border border-slate-700"
          >
            <h3 className="text-lg font-semibold text-white mb-4">日志详情</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">时间</span>
                <span className="text-white">{formatTimestamp(selectedLog.timestamp)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">操作人</span>
                <span className="text-white">{selectedLog.actor}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">动作</span>
                <span className="text-white">{selectedLog.action}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">对象</span>
                <span className="text-white">{selectedLog.target}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">结果</span>
                <span className={`px-2 py-0.5 rounded text-xs ${resultConfig[selectedLog.result].color}`}>
                  {resultConfig[selectedLog.result].label}
                </span>
              </div>
              {selectedLog.details && (
                <div>
                  <span className="text-gray-400">详情</span>
                  <p className="text-gray-300 mt-1 p-3 bg-slate-900/50 rounded-lg text-sm">
                    {selectedLog.details}
                  </p>
                </div>
              )}
            </div>
            <button
              onClick={() => setSelectedLog(null)}
              className="mt-6 w-full py-2 rounded-lg bg-slate-700 text-gray-300 hover:bg-slate-600"
            >
              关闭
            </button>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
