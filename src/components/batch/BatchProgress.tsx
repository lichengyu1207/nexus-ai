import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  StopIcon,
  PlayIcon,
  PauseIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import useWebSocket from '@/hooks/useWebSocket';

type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

interface SubTaskProgress {
  id: string;
  type: string;
  typeLabel: string;
  status: TaskStatus;
  progress: number;
  message?: string;
  startTime?: string;
  endTime?: string;
}

interface BatchProgressData {
  parentTaskId: string;
  total: number;
  completed: number;
  failed: number;
  running: number;
  pending: number;
  progressPercent: number;
  tasks: SubTaskProgress[];
}

interface BatchProgressProps {
  parentTaskId: string;
  initialTasks?: SubTaskProgress[];
  onComplete?: (data: BatchProgressData) => void;
  onCancel?: () => void;
  wsUrl?: string;
}

const TASK_TYPE_LABELS: Record<string, string> = {
  property_analysis: '房产分析',
  policy_query: '政策查询',
  mingpan: '命理咨询',
  emotion: '情感陪伴',
  report_generation: '报告生成',
};

const STATUS_CONFIG: Record<TaskStatus, { label: string; icon: typeof CheckCircleIcon; color: string; bgColor: string }> = {
  pending: { label: '等待中', icon: ClockIcon, color: 'text-gray-400', bgColor: 'bg-gray-100 dark:bg-gray-800' },
  running: { label: '执行中', icon: ArrowPathIcon, color: 'text-blue-500', bgColor: 'bg-blue-50 dark:bg-blue-900/20' },
  completed: { label: '已完成', icon: CheckCircleIcon, color: 'text-green-500', bgColor: 'bg-green-50 dark:bg-green-900/20' },
  failed: { label: '失败', icon: XCircleIcon, color: 'text-red-500', bgColor: 'bg-red-50 dark:bg-red-900/20' },
};

const BatchProgress: React.FC<BatchProgressProps> = ({
  parentTaskId,
  initialTasks = [],
  onComplete,
  onCancel,
  wsUrl,
}) => {
  const [tasks, setTasks] = useState<SubTaskProgress[]>(initialTasks);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isCancelling, setIsCancelling] = useState(false);

  const defaultWsUrl = wsUrl || `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/batch/${parentTaskId}`;

  const handleBatchProgress = useCallback((data: BatchProgressData) => {
    setTasks(data.tasks);

    if (data.progressPercent >= 100) {
      onComplete?.(data);
    }
  }, [onComplete]);

  const { isConnected, sendMessage } = useWebSocket({
    url: defaultWsUrl,
    onMessage: (message) => {
      if (message.type === 'batch_progress') {
        handleBatchProgress(message.data as BatchProgressData);
      }
    },
    onConnect: () => {
      sendMessage({ type: 'subscribe', parentTaskId });
    },
  });

  const stats = useMemo(() => {
    const total = tasks.length;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const failed = tasks.filter(t => t.status === 'failed').length;
    const running = tasks.filter(t => t.status === 'running').length;
    const pending = tasks.filter(t => t.status === 'pending').length;
    const progressPercent = total > 0 ? Math.round((completed / total) * 100) : 0;

    return { total, completed, failed, running, pending, progressPercent };
  }, [tasks]);

  const handleCancel = async () => {
    if (isCancelling) return;
    
    setIsCancelling(true);
    try {
      const response = await fetch(`/api/tasks/batch/${parentTaskId}/cancel`, {
        method: 'POST',
      });
      
      if (response.ok) {
        onCancel?.();
      }
    } catch (error) {
      console.error('Failed to cancel batch tasks:', error);
    } finally {
      setIsCancelling(false);
    }
  };

  const getOverallStatus = (): 'idle' | 'running' | 'completed' | 'failed' | 'partial' => {
    if (tasks.length === 0) return 'idle';
    if (stats.running > 0) return 'running';
    if (stats.completed === stats.total) return 'completed';
    if (stats.failed === stats.total) return 'failed';
    if (stats.completed + stats.failed === stats.total) return 'partial';
    return 'idle';
  };

  const overallStatus = getOverallStatus();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <svg className="w-12 h-12 transform -rotate-90">
                <circle
                  cx="24"
                  cy="24"
                  r="20"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                  className="text-gray-200 dark:text-gray-700"
                />
                <circle
                  cx="24"
                  cy="24"
                  r="20"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                  strokeDasharray={`${stats.progressPercent * 1.256} 125.6`}
                  className={`transition-all duration-500 ${
                    overallStatus === 'failed'
                      ? 'text-red-500'
                      : overallStatus === 'completed'
                      ? 'text-green-500'
                      : 'text-blue-500'
                  }`}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-bold text-gray-900 dark:text-white">
                  {stats.progressPercent}%
                </span>
              </div>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">
                批量任务进度
              </h3>
              <div className="flex items-center gap-4 mt-1 text-sm text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <CheckCircleIcon className="w-4 h-4 text-green-500" />
                  {stats.completed} 完成
                </span>
                <span className="flex items-center gap-1">
                  <ArrowPathIcon className="w-4 h-4 text-blue-500" />
                  {stats.running} 执行中
                </span>
                <span className="flex items-center gap-1">
                  <XCircleIcon className="w-4 h-4 text-red-500" />
                  {stats.failed} 失败
                </span>
                <span className="flex items-center gap-1">
                  <ClockIcon className="w-4 h-4 text-gray-400" />
                  {stats.pending} 等待
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {overallStatus === 'running' && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleCancel}
                disabled={isCancelling}
                className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50"
              >
                <StopIcon className="w-4 h-4" />
                {isCancelling ? '取消中...' : '取消全部'}
              </motion.button>
            )}

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              {isExpanded ? (
                <ChevronUpIcon className="w-5 h-5" />
              ) : (
                <ChevronDownIcon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        <div className="mt-4">
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${stats.progressPercent}%` }}
              transition={{ duration: 0.5 }}
              className={`h-full rounded-full ${
                overallStatus === 'failed'
                  ? 'bg-red-500'
                  : overallStatus === 'completed'
                  ? 'bg-green-500'
                  : 'bg-gradient-to-r from-blue-500 to-purple-500'
              }`}
            />
          </div>
        </div>

        <div className="flex items-center gap-2 mt-3">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`} />
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {isConnected ? '实时连接中' : '离线'}
          </span>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {tasks.map((task, index) => {
                const statusConfig = STATUS_CONFIG[task.status];
                const StatusIcon = statusConfig.icon;

                return (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`flex items-center justify-between px-4 py-3 ${statusConfig.bgColor}`}
                  >
                    <div className="flex items-center gap-3">
                      <StatusIcon className={`w-5 h-5 ${statusConfig.color} ${task.status === 'running' ? 'animate-spin' : ''}`} />
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white text-sm">
                          {TASK_TYPE_LABELS[task.type] || task.typeLabel || task.type}
                        </div>
                        {task.message && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {task.message}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {task.status === 'running' && (
                        <div className="w-24">
                          <div className="h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${task.progress}%` }}
                              className="h-full bg-blue-500 rounded-full"
                            />
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 text-right mt-1">
                            {task.progress}%
                          </div>
                        </div>
                      )}
                      <span className={`text-xs font-medium ${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {overallStatus === 'completed' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-green-50 dark:bg-green-900/20 border-t border-green-200 dark:border-green-800"
        >
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircleIcon className="w-5 h-5" />
            <span className="font-medium">所有任务已完成</span>
          </div>
        </motion.div>
      )}

      {overallStatus === 'failed' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800"
        >
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
            <XCircleIcon className="w-5 h-5" />
            <span className="font-medium">所有任务已失败</span>
          </div>
        </motion.div>
      )}

      {overallStatus === 'partial' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-t border-yellow-200 dark:border-yellow-800"
        >
          <div className="flex items-center gap-2 text-yellow-600 dark:text-yellow-400">
            <CheckCircleIcon className="w-5 h-5" />
            <span className="font-medium">
              任务执行完成（{stats.completed} 成功，{stats.failed} 失败）
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default BatchProgress;
