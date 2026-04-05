import React from 'react';
import { useTaskStats } from './useTaskStats';
import { useTaskListStore } from './taskStore';
import type { TaskStatus } from './types';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

interface TaskListHeaderProps {
  onDeleteSelected: () => void;
  selectedCount: number;
}

export const TaskListHeader: React.FC<TaskListHeaderProps> = ({
  onDeleteSelected,
  selectedCount,
}) => {
  const navigate = useNavigate();
  const { data: stats } = useTaskStats();
  const { statusFilter, sortOrder, setStatusFilter, setSortOrder } = useTaskListStore();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-4 mb-4">
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{stats?.total ?? 0}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">总任务</div>
        </div>
        <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats?.completed ?? 0}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">已完成</div>
        </div>
        <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats?.processing ?? 0}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">进行中</div>
        </div>
        <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats?.failed ?? 0}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">失败</div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as TaskStatus | '')}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            aria-label="筛选任务状态"
          >
            <option value="">全部状态</option>
            <option value="pending">等待分析</option>
            <option value="processing">进行中</option>
            <option value="completed">已完成</option>
            <option value="failed">失败</option>
          </select>
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            aria-label="排序方式"
          >
            <option value="desc">最新优先</option>
            <option value="asc">最早优先</option>
          </select>
        </div>
        <div className="flex gap-2">
          {selectedCount > 0 && (
            <button
              onClick={onDeleteSelected}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg transition-colors"
              aria-label={`删除选中的 ${selectedCount} 个任务`}
            >
              <TrashIcon className="w-4 h-4" />
              删除所选 ({selectedCount})
            </button>
          )}
          <button
            onClick={() => navigate('/consult')}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-sm font-medium rounded-lg transition-colors shadow-md"
            aria-label="新建任务"
          >
            <PlusIcon className="w-4 h-4" />
            新建任务
          </button>
        </div>
      </div>
    </div>
  );
};

export default TaskListHeader;
