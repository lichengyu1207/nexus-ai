import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ClockIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  DocumentTextIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';
import ProgressBar from './ProgressBar';
import Tooltip from './Tooltip';

export interface Task {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  startTime: string;
  estimatedEndTime?: string;
  resultSummary?: string;
  errorMessage?: string;
  inputParams?: Record<string, unknown>;
  agentsUsed?: string[];
  fullProcessLog?: string[];
}

interface TaskStatusCardProps {
  task: Task;
  onViewReport?: (taskId: string) => void;
  onRetry?: (taskId: string) => void;
  className?: string;
}

const statusConfig = {
  pending: {
    borderColor: 'border-gray-300 dark:border-gray-600',
    icon: ClockIcon,
    iconColor: 'text-gray-400',
    label: '等待分析',
    labelColor: 'text-gray-500',
  },
  processing: {
    borderColor: 'border-blue-400 dark:border-blue-500',
    icon: ArrowPathIcon,
    iconColor: 'text-blue-500',
    label: '分析中',
    labelColor: 'text-blue-500',
  },
  completed: {
    borderColor: 'border-green-500 dark:border-green-400',
    icon: CheckCircleIcon,
    iconColor: 'text-green-500',
    label: '分析完成',
    labelColor: 'text-green-500',
  },
  failed: {
    borderColor: 'border-red-500 dark:border-red-400',
    icon: XCircleIcon,
    iconColor: 'text-red-500',
    label: '分析失败',
    labelColor: 'text-red-500',
  },
};

const formatTime = (isoString: string): string => {
  const date = new Date(isoString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

const TaskStatusCard: React.FC<TaskStatusCardProps> = ({
  task,
  onViewReport,
  onRetry,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const config = statusConfig[task.status];
  const StatusIcon = config.icon;

  const tooltipContent = (
    <div className="space-y-2">
      {task.inputParams && Object.keys(task.inputParams).length > 0 && (
        <div>
          <p className="font-semibold text-xs text-gray-300 mb-1">输入参数：</p>
          <pre className="text-xs bg-gray-800 p-2 rounded overflow-auto max-h-24">
            {JSON.stringify(task.inputParams, null, 2)}
          </pre>
        </div>
      )}
      {task.agentsUsed && task.agentsUsed.length > 0 && (
        <div>
          <p className="font-semibold text-xs text-gray-300 mb-1">使用的智能体：</p>
          <ul className="text-xs space-y-0.5">
            {task.agentsUsed.map((agent) => (
              <li key={agent} className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
                {agent}
              </li>
            ))}
          </ul>
        </div>
      )}
      {!task.inputParams && (!task.agentsUsed || task.agentsUsed.length === 0) && (
        <p className="text-xs text-gray-400">暂无详细信息</p>
      )}
    </div>
  );

  const handleCardClick = () => {
    setIsExpanded(!isExpanded);
  };

  const handleViewReport = (e: React.MouseEvent) => {
    e.stopPropagation();
    onViewReport?.(task.id);
  };

  const handleRetry = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRetry?.(task.id);
  };

  return (
    <motion.div
      className={`
        relative rounded-xl border-2 ${config.borderColor}
        bg-white dark:bg-gray-800 shadow-md
        overflow-hidden
        ${className}
      `}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01, boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)' }}
      transition={{ duration: 0.2 }}
      data-testid="task-status-card"
    >
      <Tooltip content={tooltipContent}>
        <div
          onClick={handleCardClick}
          className="p-4 cursor-pointer"
          role="button"
          tabIndex={0}
          aria-expanded={isExpanded}
          aria-label={`${task.name} - ${config.label}`}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleCardClick();
            }
          }}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <StatusIcon
                className={`w-5 h-5 ${config.iconColor} ${
                  task.status === 'processing' ? 'animate-spin' : ''
                }`}
              />
              <h3 className="font-semibold text-gray-900 dark:text-white text-sm md:text-base">
                {task.name}
              </h3>
            </div>
            <span className={`text-xs font-medium ${config.labelColor}`}>
              {config.label}
            </span>
          </div>

          <div className="space-y-2 mb-3">
            <ProgressBar progress={task.progress} status={task.status} />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>进度</span>
              <span data-testid="progress-text">{task.progress}%</span>
            </div>
          </div>

          {task.status === 'completed' && task.resultSummary && (
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
              {task.resultSummary}
            </p>
          )}

          {task.status === 'failed' && task.errorMessage && (
            <p className="text-sm text-red-500 mb-3 line-clamp-2">
              {task.errorMessage}
            </p>
          )}

          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>开始: {formatTime(task.startTime)}</span>
            {task.estimatedEndTime && (
              <span>预计完成: {formatTime(task.estimatedEndTime)}</span>
            )}
          </div>

          {(task.status === 'completed' || task.status === 'failed') && (
            <div className="flex gap-2 mt-3">
              {task.status === 'completed' && (
                <button
                  onClick={handleViewReport}
                  className="flex items-center gap-1 px-3 py-1.5 bg-gradient-to-r from-yellow-500 to-orange-500 text-white text-xs font-medium rounded-lg hover:shadow-md transition-shadow"
                  aria-label="查看报告"
                >
                  <DocumentTextIcon className="w-4 h-4" />
                  查看报告
                </button>
              )}
              {task.status === 'failed' && (
                <button
                  onClick={handleRetry}
                  className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  aria-label="重试"
                >
                  <ArrowPathIcon className="w-4 h-4" />
                  重试
                </button>
              )}
            </div>
          )}

          {task.fullProcessLog && task.fullProcessLog.length > 0 && (
            <div className="flex items-center justify-center mt-2">
              <ChevronDownIcon
                className={`w-4 h-4 text-gray-400 transition-transform ${
                  isExpanded ? 'rotate-180' : ''
                }`}
              />
            </div>
          )}
        </div>
      </Tooltip>

      <AnimatePresence>
        {isExpanded && task.fullProcessLog && task.fullProcessLog.length > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700 pt-3">
              <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">
                分析过程
              </h4>
              <ul className="space-y-1.5 max-h-40 overflow-y-auto">
                {task.fullProcessLog.map((log, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-xs text-gray-600 dark:text-gray-300"
                  >
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center text-xs font-medium">
                      {index + 1}
                    </span>
                    <span className="pt-0.5">{log}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default TaskStatusCard;
