import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  PlayIcon,
  DocumentTextIcon,
  TrashIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';

export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface TaskStatusCardData {
  taskId: string;
  name: string;
  status: TaskStatus;
  progress: number;
  startTime?: string;
  estimatedFinish?: string;
  result?: {
    summary?: string;
    keyMetrics?: Record<string, string | number>;
  };
  error?: string;
  inputParams?: Record<string, unknown>;
  agentsUsed?: string[];
  cost?: number;
  query?: string;
  created_at?: string;
}

interface TaskStatusCardProps {
  task: TaskStatusCardData;
  onViewReport?: (taskId: string) => void;
  onRetry?: (taskId: string) => void;
  onDelete?: (taskId: string) => void;
  onClick?: (taskId: string) => void;
  showDetails?: boolean;
}

const statusConfigs = {
  pending: {
    icon: ClockIcon,
    text: '等待分析',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    textColor: 'text-gray-600 dark:text-gray-400',
    borderColor: 'border-gray-300 dark:border-gray-600',
    gradientColor: 'from-gray-400 to-gray-500',
    glowColor: 'rgba(156, 163, 175, 0.3)',
  },
  processing: {
    icon: ArrowPathIcon,
    text: '分析中',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    textColor: 'text-blue-600 dark:text-blue-400',
    borderColor: 'border-blue-400 dark:border-blue-500',
    gradientColor: 'from-blue-500 to-cyan-500',
    glowColor: 'rgba(59, 130, 246, 0.4)',
  },
  completed: {
    icon: CheckCircleIcon,
    text: '分析完成',
    bgColor: 'bg-green-50 dark:bg-green-900/20',
    textColor: 'text-green-600 dark:text-green-400',
    borderColor: 'border-green-400 dark:border-green-500',
    gradientColor: 'from-green-500 to-emerald-500',
    glowColor: 'rgba(34, 197, 94, 0.3)',
  },
  failed: {
    icon: ExclamationCircleIcon,
    text: '分析失败',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    textColor: 'text-red-600 dark:text-red-400',
    borderColor: 'border-red-400 dark:border-red-500',
    gradientColor: 'from-red-500 to-rose-500',
    glowColor: 'rgba(239, 68, 68, 0.3)',
  },
};

const TaskStatusCard: React.FC<TaskStatusCardProps> = ({
  task,
  onViewReport,
  onRetry,
  onDelete,
  onClick,
  showDetails = false,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const config = statusConfigs[task.status];
  const StatusIcon = config.icon;

  const formatTime = (dateStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const calculateDuration = () => {
    if (!task.startTime) return '-';
    const start = new Date(task.startTime);
    const end = task.status === 'completed' && task.estimatedFinish
      ? new Date(task.estimatedFinish)
      : new Date();
    const diff = Math.floor((end.getTime() - start.getTime()) / 1000);
    if (diff < 60) return `${diff}秒`;
    if (diff < 3600) return `${Math.floor(diff / 60)}分钟`;
    return `${Math.floor(diff / 3600)}小时`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -2 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={() => onClick?.(task.taskId)}
      className={`
        relative rounded-2xl border-2 overflow-hidden cursor-pointer
        transition-all duration-300
        ${config.bgColor} ${config.borderColor}
        ${isHovered ? 'shadow-xl' : 'shadow-md'}
      `}
      style={{
        boxShadow: isHovered ? `0 10px 40px ${config.glowColor}` : undefined,
      }}
    >
      {task.status === 'processing' && (
        <motion.div
          className="absolute inset-0 opacity-20"
          style={{
            background: `linear-gradient(90deg, transparent, ${config.glowColor}, transparent)`,
          }}
          animate={{
            x: ['-100%', '100%'],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      )}

      <div className="relative p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3">
              <motion.div
                animate={task.status === 'processing' ? { rotate: 360 } : {}}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                className={`p-1.5 rounded-lg bg-gradient-to-r ${config.gradientColor}`}
              >
                <StatusIcon className="w-4 h-4 text-white" />
              </motion.div>
              <span className={`text-sm font-medium ${config.textColor}`}>
                {config.text}
              </span>
              {task.cost !== undefined && (
                <span className="text-xs text-gray-400 dark:text-gray-500">
                  · {task.cost} 积分
                </span>
              )}
            </div>

            <h3 className="text-base font-semibold text-gray-900 dark:text-white line-clamp-2 mb-2">
              {task.name || task.query || '未命名任务'}
            </h3>

            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1">
                <ClockIcon className="w-3.5 h-3.5" />
                {formatTime(task.startTime || task.created_at)}
              </span>
              {task.status === 'processing' && (
                <span className="flex items-center gap-1">
                  <PlayIcon className="w-3.5 h-3.5" />
                  预计 {formatTime(task.estimatedFinish)}
                </span>
              )}
              {task.status !== 'pending' && task.status !== 'processing' && (
                <span>耗时 {calculateDuration()}</span>
              )}
            </div>
          </div>

          {(task.status === 'processing' || task.status === 'pending') && (
            <div className="flex-shrink-0 w-16">
              <div className="text-right mb-1">
                <span className={`text-lg font-bold bg-gradient-to-r ${config.gradientColor} bg-clip-text text-transparent`}>
                  {task.progress}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${task.progress}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                  className={`h-full rounded-full bg-gradient-to-r ${config.gradientColor}`}
                />
              </div>
            </div>
          )}
        </div>

        {task.status === 'completed' && task.result?.summary && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg"
          >
            <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">
              {task.result.summary}
            </p>
          </motion.div>
        )}

        {task.status === 'failed' && task.error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-4 p-3 bg-red-100/50 dark:bg-red-900/20 rounded-lg"
          >
            <p className="text-sm text-red-600 dark:text-red-400 line-clamp-2">
              {task.error}
            </p>
          </motion.div>
        )}

        <AnimatePresence>
          {showTooltip && isHovered && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="absolute left-0 right-0 -bottom-2 translate-y-full z-50 p-4 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700"
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                任务详情
              </h4>
              {task.inputParams && Object.keys(task.inputParams).length > 0 && (
                <div className="mb-2">
                  <span className="text-xs text-gray-500">输入参数:</span>
                  <div className="mt-1 text-xs text-gray-600 dark:text-gray-300">
                    {JSON.stringify(task.inputParams, null, 2).slice(0, 100)}...
                  </div>
                </div>
              )}
              {task.agentsUsed && task.agentsUsed.length > 0 && (
                <div>
                  <span className="text-xs text-gray-500">使用智能体:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {task.agentsUsed.map((agent, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs"
                      >
                        {agent}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {(task.status === 'completed' || task.status === 'failed') && isHovered && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-200 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-800/80 backdrop-blur-sm"
          >
            <div className="flex items-center justify-end gap-2 p-3">
              {task.status === 'completed' && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewReport?.(task.taskId);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-green-500 to-emerald-500 text-white text-sm rounded-lg hover:shadow-lg transition-shadow"
                >
                  <DocumentTextIcon className="w-4 h-4" />
                  查看报告
                </motion.button>
              )}
              {task.status === 'failed' && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRetry?.(task.taskId);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-sm rounded-lg hover:shadow-lg transition-shadow"
                >
                  <ArrowPathIcon className="w-4 h-4" />
                  重试
                </motion.button>
              )}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete?.(task.taskId);
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-sm rounded-lg hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/50 dark:hover:text-red-400 transition-colors"
              >
                <TrashIcon className="w-4 h-4" />
                删除
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {showDetails && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute top-2 right-2"
        >
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowTooltip(!showTooltip);
            }}
            className="p-1.5 rounded-lg bg-gray-200/50 dark:bg-gray-700/50 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            <EyeIcon className="w-4 h-4 text-gray-500" />
          </button>
        </motion.div>
      )}
    </motion.div>
  );
};

export default TaskStatusCard;
