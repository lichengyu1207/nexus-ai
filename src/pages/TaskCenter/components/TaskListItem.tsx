import { memo } from 'react';
import { motion } from 'framer-motion';
import type { Task, TaskStatus } from '../types';

interface TaskListItemProps {
  task: Task;
  isSelected: boolean;
  onSelect: (taskId: string, selected: boolean) => void;
  onClick: (taskId: string) => void;
  onRetry: (taskId: string) => void;
  onDelete: (taskId: string) => void;
  viewMode: 'card' | 'table';
}

const statusConfig: Record<TaskStatus, { label: string; color: string; bgColor: string }> = {
  pending: { label: '待处理', color: 'text-gray-400', bgColor: 'bg-gray-500/20' },
  processing: { label: '处理中', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
  completed: { label: '已完成', color: 'text-green-400', bgColor: 'bg-green-500/20' },
  failed: { label: '失败', color: 'text-red-400', bgColor: 'bg-red-500/20' },
};

const priorityConfig: Record<string, { label: string; color: string }> = {
  low: { label: '低', color: 'text-gray-400' },
  medium: { label: '中', color: 'text-yellow-400' },
  high: { label: '高', color: 'text-red-400' },
};

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const TaskListItemComponent = ({
  task,
  isSelected,
  onSelect,
  onClick,
  onRetry,
  onDelete,
  viewMode,
}: TaskListItemProps) => {
  const status = statusConfig[task.status];
  const priority = task.priority ? priorityConfig[task.priority] : null;

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation();
    onSelect(task.id, e.target.checked);
  };

  const handleRetry = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRetry(task.id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(task.id);
  };

  if (viewMode === 'card') {
    return (
      <motion.div
        whileHover={{ y: -2, boxShadow: '0 8px 30px rgba(0,0,0,0.3)' }}
        onClick={() => onClick(task.id)}
        className={`relative p-4 rounded-xl cursor-pointer transition-all
          ${isSelected
            ? 'bg-amber-500/10 border-2 border-amber-500/50'
            : 'bg-slate-800/50 border border-slate-700/50 hover:border-amber-500/30'
          }`}
        role="row"
      >
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={handleCheckboxChange}
            onClick={(e) => e.stopPropagation()}
            className="mt-1 w-4 h-4 rounded border-slate-600 bg-slate-800 text-amber-500
              focus:ring-amber-500 focus:ring-offset-0"
            aria-label={`选择任务 ${task.name}`}
          />

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h4 className="text-white font-medium truncate">{task.name}</h4>
              <span
                className={`px-2 py-0.5 rounded text-xs ${status.bgColor} ${status.color}`}
                aria-label={`状态: ${status.label}`}
              >
                {status.label}
              </span>
              {priority && (
                <span className={`text-xs ${priority.color}`}>
                  优先级: {priority.label}
                </span>
              )}
            </div>

            <div className="mb-3">
              <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                <span>进度</span>
                <span>{task.progress}%</span>
              </div>
              <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${task.progress}%` }}
                  className="h-full bg-gradient-to-r from-amber-500 to-amber-400"
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{formatTime(task.startTime)}</span>
              <div className="flex items-center gap-2">
                {task.agentsUsed && task.agentsUsed.length > 0 && (
                  <span className="flex items-center gap-1">
                    🤖 {task.agentsUsed.length}
                  </span>
                )}
                {task.status === 'failed' && (
                  <button
                    onClick={handleRetry}
                    className="text-blue-400 hover:text-blue-300"
                  >
                    重试
                  </button>
                )}
              </div>
            </div>

            {task.errorMessage && (
              <p className="mt-2 text-xs text-red-400 truncate">
                ⚠️ {task.errorMessage}
              </p>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      whileHover={{ backgroundColor: 'rgba(255,255,255,0.02)' }}
      onClick={() => onClick(task.id)}
      className={`flex items-center gap-4 px-4 py-3 border-b border-slate-700/30 cursor-pointer
        ${isSelected ? 'bg-amber-500/10' : ''}`}
      role="row"
    >
      <input
        type="checkbox"
        checked={isSelected}
        onChange={handleCheckboxChange}
        onClick={(e) => e.stopPropagation()}
        className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-amber-500
          focus:ring-amber-500 focus:ring-offset-0"
        aria-label={`选择任务 ${task.name}`}
      />

      <div className="flex-1 min-w-0">
        <span className="text-white truncate">{task.name}</span>
      </div>

      <span
        className={`px-2 py-0.5 rounded text-xs ${status.bgColor} ${status.color}`}
        aria-label={`状态: ${status.label}`}
      >
        {status.label}
      </span>

      <div className="w-32">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-slate-700 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${task.progress}%` }}
              className="h-full bg-gradient-to-r from-amber-500 to-amber-400"
            />
          </div>
          <span className="text-xs text-gray-500 w-8">{task.progress}%</span>
        </div>
      </div>

      {priority && (
        <span className={`text-xs ${priority.color} w-12`}>{priority.label}</span>
      )}

      <span className="text-xs text-gray-500 w-24">
        {formatTime(task.startTime)}
      </span>

      <div className="flex items-center gap-2 w-20">
        {task.status === 'failed' && (
          <button
            onClick={handleRetry}
            className="text-blue-400 hover:text-blue-300 text-xs"
          >
            重试
          </button>
        )}
        <button
          onClick={handleDelete}
          className="text-red-400 hover:text-red-300 text-xs"
        >
          删除
        </button>
      </div>
    </motion.div>
  );
};

export const TaskListItem = memo(TaskListItemComponent);
