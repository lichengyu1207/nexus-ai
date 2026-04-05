import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTaskDetail } from '../hooks/useTaskDetail';
import type { TaskStatus } from '../types';

interface TaskDetailSidebarProps {
  taskId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onViewFullDetail: (taskId: string) => void;
  onRetry: (taskId: string) => void;
  onDelete: (taskId: string) => void;
}

const statusConfig: Record<TaskStatus, { label: string; color: string }> = {
  pending: { label: '待处理', color: 'text-gray-400' },
  processing: { label: '处理中', color: 'text-blue-400' },
  completed: { label: '已完成', color: 'text-green-400' },
  failed: { label: '失败', color: 'text-red-400' },
};

export function TaskDetailSidebar({
  taskId,
  isOpen,
  onClose,
  onViewFullDetail,
  onRetry,
  onDelete,
}: TaskDetailSidebarProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const { data: task, isLoading, error } = useTaskDetail(taskId);

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

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('zh-CN');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 h-full w-[400px] bg-slate-900 border-l border-slate-700
              shadow-2xl z-50 overflow-y-auto"
            role="dialog"
            aria-modal="true"
            aria-labelledby="task-detail-title"
          >
            <div className="sticky top-0 bg-slate-900/95 backdrop-blur-sm border-b border-slate-700 p-4">
              <div className="flex items-center justify-between">
                <h2 id="task-detail-title" className="text-lg font-semibold text-white">
                  任务详情
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

            <div className="p-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : error ? (
                <div className="text-center text-red-400 py-8">
                  加载失败
                </div>
              ) : task ? (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">
                      {task.name}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-sm ${
                          statusConfig[task.status].color
                        } bg-slate-800`}
                      >
                        {statusConfig[task.status].label}
                      </span>
                      {task.priority && (
                        <span className="text-sm text-gray-400">
                          优先级: {task.priority}
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-gray-400">进度</span>
                      <span className="text-white">{task.progress}%</span>
                    </div>
                    <div className="h-3 rounded-full bg-slate-700 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${task.progress}%` }}
                        className="h-full bg-gradient-to-r from-amber-500 to-amber-400"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-slate-800/50">
                      <p className="text-xs text-gray-500 mb-1">开始时间</p>
                      <p className="text-sm text-white">{formatDate(task.startTime)}</p>
                    </div>
                    {task.estimatedEndTime && (
                      <div className="p-3 rounded-lg bg-slate-800/50">
                        <p className="text-xs text-gray-500 mb-1">预计完成</p>
                        <p className="text-sm text-white">{formatDate(task.estimatedEndTime)}</p>
                      </div>
                    )}
                  </div>

                  {task.resultSummary && (
                    <div className="p-3 rounded-lg bg-slate-800/50">
                      <p className="text-xs text-gray-500 mb-2">结果摘要</p>
                      <p className="text-sm text-gray-300">{task.resultSummary}</p>
                    </div>
                  )}

                  {task.errorMessage && (
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                      <p className="text-xs text-red-400 mb-1">错误信息</p>
                      <p className="text-sm text-red-300">{task.errorMessage}</p>
                    </div>
                  )}

                  {task.workflowSteps && task.workflowSteps.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-400 mb-3">工作流步骤</h4>
                      <div className="relative pl-4">
                        <div className="absolute left-1.5 top-0 bottom-0 w-0.5 bg-slate-700" />
                        {task.workflowSteps.map((step, index) => (
                          <div key={step.id} className="relative mb-3">
                            <div
                              className={`absolute left-[-10px] w-3 h-3 rounded-full ${
                                step.status === 'completed'
                                  ? 'bg-green-500'
                                  : step.status === 'processing'
                                  ? 'bg-blue-500'
                                  : 'bg-gray-500'
                              } ring-2 ring-slate-900`}
                            />
                            <div className="pl-2">
                              <p className="text-white text-sm">{step.name}</p>
                              <p className="text-xs text-gray-500">
                                {statusConfig[step.status].label}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {task.finalReport && (
                    <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                      <h4 className="text-sm font-medium text-amber-400 mb-2">
                        最终报告
                      </h4>
                      <p className="text-sm text-gray-300 mb-3">
                        {task.finalReport.summary}
                      </p>
                      <a
                        href={task.finalReport.downloadUrl}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded bg-amber-500
                          text-slate-900 text-sm font-medium hover:bg-amber-400"
                      >
                        📥 下载报告
                      </a>
                    </div>
                  )}

                  <div className="flex gap-2 pt-4 border-t border-slate-700">
                    <button
                      onClick={() => onViewFullDetail(task.id)}
                      className="flex-1 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
                        hover:bg-amber-400 transition-colors"
                    >
                      查看完整详情
                    </button>
                    {task.status === 'failed' && (
                      <button
                        onClick={() => onRetry(task.id)}
                        className="px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400
                          hover:bg-blue-500/30 transition-colors"
                      >
                        重试
                      </button>
                    )}
                    <button
                      onClick={() => onDelete(task.id)}
                      className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400
                        hover:bg-red-500/30 transition-colors"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
