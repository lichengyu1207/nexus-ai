import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { CallLog } from '../types';

interface LogDetailModalProps {
  log: CallLog | null;
  isOpen: boolean;
  onClose: () => void;
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString('zh-CN');
}

function formatDuration(ms?: number): string {
  if (!ms) return '-';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function LogDetailModal({ log, isOpen, onClose }: LogDetailModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        closeButtonRef.current?.focus();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!log) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50
              w-full max-w-lg max-h-[80vh] overflow-hidden
              bg-slate-800 border border-slate-700 rounded-xl shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="log-detail-title"
          >
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 p-4">
              <div className="flex items-center justify-between">
                <h2 id="log-detail-title" className="text-lg font-semibold text-white">
                  调用详情
                </h2>
                <button
                  ref={closeButtonRef}
                  onClick={onClose}
                  className="p-1 rounded text-gray-400 hover:text-white hover:bg-slate-700"
                  aria-label="关闭"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-4 overflow-y-auto max-h-[60vh] space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500 mb-1">时间</p>
                  <p className="text-white text-sm">{formatTime(log.timestamp)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">耗时</p>
                  <p className="text-white text-sm">{formatDuration(log.duration)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">智能体</p>
                  <p className="text-white text-sm">{log.agentName}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">工具</p>
                  <p className="text-amber-400 text-sm">{log.toolName}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">结果</p>
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      log.result === 'success'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {log.result === 'success' ? '成功' : '失败'}
                  </span>
                </div>
              </div>

              {log.details?.request && (
                <div>
                  <p className="text-xs text-gray-500 mb-2">请求参数</p>
                  <pre className="p-3 rounded-lg bg-slate-900/50 text-gray-300 text-xs overflow-x-auto">
                    {JSON.stringify(log.details.request, null, 2)}
                  </pre>
                </div>
              )}

              {log.details?.response && (
                <div>
                  <p className="text-xs text-gray-500 mb-2">响应结果</p>
                  <pre className="p-3 rounded-lg bg-slate-900/50 text-gray-300 text-xs overflow-x-auto">
                    {JSON.stringify(log.details.response, null, 2)}
                  </pre>
                </div>
              )}

              {log.details?.error && (
                <div>
                  <p className="text-xs text-red-400 mb-2">错误信息</p>
                  <pre className="p-3 rounded-lg bg-red-500/10 border border-red-500/20
                    text-red-300 text-xs overflow-x-auto whitespace-pre-wrap">
                    {log.details.error}
                  </pre>
                </div>
              )}
            </div>

            <div className="sticky bottom-0 bg-slate-800 border-t border-slate-700 p-4">
              <button
                onClick={onClose}
                className="w-full py-2 rounded-lg bg-slate-700 text-gray-300 hover:bg-slate-600"
              >
                关闭
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
