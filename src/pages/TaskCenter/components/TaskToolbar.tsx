import { motion } from 'framer-motion';
import type { ViewMode, TaskSortField, TaskSortOrder } from '../types';

interface TaskToolbarProps {
  selectedCount: number;
  onBatchRetry: () => void;
  onBatchDelete: () => void;
  onBatchExport: () => void;
  onCompare: () => void;
  onNewTask: () => void;
  onSearch: (text: string) => void;
  onSortChange: (field: TaskSortField, order: TaskSortOrder) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  sortField: TaskSortField;
  sortOrder: TaskSortOrder;
  canCompare: boolean;
}

const sortOptions: { field: TaskSortField; label: string }[] = [
  { field: 'createdAt', label: '创建时间' },
  { field: 'progress', label: '进度' },
  { field: 'priority', label: '优先级' },
];

export function TaskToolbar({
  selectedCount,
  onBatchRetry,
  onBatchDelete,
  onBatchExport,
  onCompare,
  onNewTask,
  onSearch,
  onSortChange,
  viewMode,
  onViewModeChange,
  sortField,
  sortOrder,
  canCompare,
}: TaskToolbarProps) {
  const hasSelection = selectedCount > 0;

  return (
    <div className="flex items-center justify-between p-4 bg-slate-800/30 border-b border-slate-700/50">
      <div className="flex items-center gap-3">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onNewTask}
          className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium
            hover:bg-amber-400 transition-colors flex items-center gap-2"
        >
          <span>+</span>
          <span>新建任务</span>
        </motion.button>

        <div className="h-6 w-px bg-slate-700" />

        <motion.button
          whileHover={{ scale: hasSelection ? 1.02 : 1 }}
          whileTap={{ scale: hasSelection ? 0.98 : 1 }}
          onClick={onBatchRetry}
          disabled={!hasSelection}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1
            ${hasSelection
              ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
              : 'bg-slate-700/50 text-gray-500 cursor-not-allowed'
            }`}
        >
          🔄 重试
          {hasSelection && (
            <span className="px-1.5 py-0.5 rounded-full bg-blue-500/30 text-xs">
              {selectedCount}
            </span>
          )}
        </motion.button>

        <motion.button
          whileHover={{ scale: hasSelection ? 1.02 : 1 }}
          whileTap={{ scale: hasSelection ? 0.98 : 1 }}
          onClick={onBatchDelete}
          disabled={!hasSelection}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1
            ${hasSelection
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
              : 'bg-slate-700/50 text-gray-500 cursor-not-allowed'
            }`}
        >
          🗑️ 删除
          {hasSelection && (
            <span className="px-1.5 py-0.5 rounded-full bg-red-500/30 text-xs">
              {selectedCount}
            </span>
          )}
        </motion.button>

        <motion.button
          whileHover={{ scale: hasSelection ? 1.02 : 1 }}
          whileTap={{ scale: hasSelection ? 0.98 : 1 }}
          onClick={onBatchExport}
          disabled={!hasSelection}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1
            ${hasSelection
              ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
              : 'bg-slate-700/50 text-gray-500 cursor-not-allowed'
            }`}
        >
          📥 导出
        </motion.button>

        <motion.button
          whileHover={{ scale: canCompare ? 1.02 : 1 }}
          whileTap={{ scale: canCompare ? 0.98 : 1 }}
          onClick={onCompare}
          disabled={!canCompare}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1
            ${canCompare
              ? 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30'
              : 'bg-slate-700/50 text-gray-500 cursor-not-allowed'
            }`}
        >
          ⚖️ 对比
          {hasSelection > 0 && (
            <span className="text-xs text-gray-500">(2-5个)</span>
          )}
        </motion.button>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative">
          <input
            type="text"
            placeholder="搜索任务..."
            onChange={(e) => onSearch(e.target.value)}
            className="w-48 px-3 py-1.5 pl-8 rounded-lg bg-slate-800 border border-slate-700
              text-gray-300 text-sm focus:outline-none focus:border-amber-500"
          />
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500">
            🔍
          </span>
        </div>

        <select
          value={sortField}
          onChange={(e) => onSortChange(e.target.value as TaskSortField, sortOrder)}
          className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700
            text-gray-300 text-sm focus:outline-none focus:border-amber-500"
        >
          {sortOptions.map((option) => (
            <option key={option.field} value={option.field}>
              {option.label}
            </option>
          ))}
        </select>

        <button
          onClick={() => onSortChange(sortField, sortOrder === 'asc' ? 'desc' : 'asc')}
          className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-gray-400
            hover:text-white hover:border-amber-500 transition-colors"
          aria-label={sortOrder === 'asc' ? '降序排列' : '升序排列'}
        >
          {sortOrder === 'asc' ? '↑' : '↓'}
        </button>

        <div className="flex rounded-lg overflow-hidden border border-slate-700">
          <button
            onClick={() => onViewModeChange('card')}
            className={`px-3 py-1.5 text-sm transition-colors ${
              viewMode === 'card'
                ? 'bg-amber-500 text-slate-900'
                : 'bg-slate-800 text-gray-400 hover:text-white'
            }`}
            aria-label="卡片视图"
          >
            ▦
          </button>
          <button
            onClick={() => onViewModeChange('table')}
            className={`px-3 py-1.5 text-sm transition-colors ${
              viewMode === 'table'
                ? 'bg-amber-500 text-slate-900'
                : 'bg-slate-800 text-gray-400 hover:text-white'
            }`}
            aria-label="表格视图"
          >
            ≡
          </button>
        </div>
      </div>
    </div>
  );
}
