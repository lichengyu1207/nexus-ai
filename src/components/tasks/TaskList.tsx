import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FunnelIcon,
  ArrowsUpDownIcon,
  PlusIcon,
  TrashIcon,
  Squares2X2Icon,
  ListBulletIcon,
} from '@heroicons/react/24/outline';
import TaskStatusCard, { TaskStatusCardData, TaskStatus } from './TaskStatusCard';

interface TaskListProps {
  tasks: TaskStatusCardData[];
  isLoading?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
  onCreateTask?: () => void;
  onViewReport?: (taskId: string) => void;
  onRetry?: (taskId: string) => void;
  onDelete?: (taskId: string) => void;
  onTaskClick?: (taskId: string) => void;
  onBatchDelete?: (taskIds: string[]) => void;
}

type FilterStatus = 'all' | TaskStatus;
type SortOrder = 'newest' | 'oldest';
type ViewMode = 'grid' | 'list';

const TaskList: React.FC<TaskListProps> = ({
  tasks,
  isLoading = false,
  hasMore = false,
  onLoadMore,
  onCreateTask,
  onViewReport,
  onRetry,
  onDelete,
  onTaskClick,
  onBatchDelete,
}) => {
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [sortOrder, setSortOrder] = useState<SortOrder>('newest');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const stats = useMemo(() => {
    const total = tasks.length;
    const completed = tasks.filter((t) => t.status === 'completed').length;
    const processing = tasks.filter((t) => t.status === 'processing' || t.status === 'pending').length;
    const failed = tasks.filter((t) => t.status === 'failed').length;
    return { total, completed, processing, failed };
  }, [tasks]);

  const filteredAndSortedTasks = useMemo(() => {
    let result = [...tasks];

    if (filterStatus !== 'all') {
      result = result.filter((t) => t.status === filterStatus);
    }

    result.sort((a, b) => {
      const dateA = new Date(a.startTime || a.created_at || 0).getTime();
      const dateB = new Date(b.startTime || b.created_at || 0).getTime();
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return result;
  }, [tasks, filterStatus, sortOrder]);

  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoading) {
          onLoadMore?.();
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      observerRef.current?.disconnect();
    };
  }, [hasMore, isLoading, onLoadMore]);

  const toggleTaskSelection = useCallback((taskId: string) => {
    setSelectedTasks((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedTasks(new Set(filteredAndSortedTasks.map((t) => t.taskId)));
  }, [filteredAndSortedTasks]);

  const clearSelection = useCallback(() => {
    setSelectedTasks(new Set());
  }, []);

  const handleBatchDelete = useCallback(() => {
    if (selectedTasks.size > 0) {
      onBatchDelete?.(Array.from(selectedTasks));
      setSelectedTasks(new Set());
      setShowDeleteConfirm(false);
    }
  }, [selectedTasks, onBatchDelete]);

  const filterOptions: { value: FilterStatus; label: string; count: number }[] = [
    { value: 'all', label: '全部', count: stats.total },
    { value: 'processing', label: '进行中', count: stats.processing },
    { value: 'completed', label: '已完成', count: stats.completed },
    { value: 'failed', label: '失败', count: stats.failed },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-4 border border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-6">
            {filterOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setFilterStatus(option.value)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  filterStatus === option.value
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <span>{option.label}</span>
                <span
                  className={`px-1.5 py-0.5 rounded-full text-xs ${
                    filterStatus === option.value
                      ? 'bg-primary-200 dark:bg-primary-800 text-primary-700 dark:text-primary-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {option.count}
                </span>
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setSortOrder((prev) => (prev === 'newest' ? 'oldest' : 'newest'))}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ArrowsUpDownIcon className="w-4 h-4" />
              {sortOrder === 'newest' ? '最新优先' : '最早优先'}
            </button>

            <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-md transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-white dark:bg-gray-600 text-primary-600 dark:text-primary-400 shadow-sm'
                    : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                <Squares2X2Icon className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-md transition-colors ${
                  viewMode === 'list'
                    ? 'bg-white dark:bg-gray-600 text-primary-600 dark:text-primary-400 shadow-sm'
                    : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                <ListBulletIcon className="w-4 h-4" />
              </button>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onCreateTask}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-primary-500 to-primary-600 text-white text-sm font-medium rounded-lg hover:shadow-lg transition-shadow"
            >
              <PlusIcon className="w-4 h-4" />
              新建任务
            </motion.button>
          </div>
        </div>

        {selectedTasks.size > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  已选择 <span className="font-semibold text-primary-600">{selectedTasks.size}</span> 个任务
                </span>
                <button
                  onClick={selectAll}
                  className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
                >
                  全选
                </button>
                <button
                  onClick={clearSelection}
                  className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400"
                >
                  取消选择
                </button>
              </div>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg transition-colors"
              >
                <TrashIcon className="w-4 h-4" />
                批量删除
              </motion.button>
            </div>
          </motion.div>
        )}
      </div>

      <AnimatePresence mode="wait">
        {filteredAndSortedTasks.length === 0 && !isLoading ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="text-center py-16"
          >
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
              <FunnelIcon className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              暂无任务
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {filterStatus === 'all'
                ? '点击上方按钮创建您的第一个分析任务'
                : '当前筛选条件下没有任务'}
            </p>
            {filterStatus === 'all' && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onCreateTask}
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              >
                <PlusIcon className="w-5 h-5" />
                创建任务
              </motion.button>
            )}
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={
              viewMode === 'grid'
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                : 'space-y-3'
            }
          >
            {filteredAndSortedTasks.map((task, index) => (
              <motion.div
                key={task.taskId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="relative"
              >
                {selectedTasks.size > 0 && (
                  <div className="absolute top-3 left-3 z-10">
                    <input
                      type="checkbox"
                      checked={selectedTasks.has(task.taskId)}
                      onChange={() => toggleTaskSelection(task.taskId)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                  </div>
                )}
                <div className={selectedTasks.size > 0 ? 'ml-8' : ''}>
                  <TaskStatusCard
                    task={task}
                    onViewReport={onViewReport}
                    onRetry={onRetry}
                    onDelete={onDelete}
                    onClick={onTaskClick}
                  />
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {isLoading && (
        <div className="flex justify-center py-8">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full"
          />
        </div>
      )}

      <div ref={loadMoreRef} className="h-4" />

      <AnimatePresence>
        {showDeleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowDeleteConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-md w-full shadow-2xl"
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                确认删除
              </h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">
                您确定要删除选中的 {selectedTasks.size} 个任务吗？此操作无法撤销。
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleBatchDelete}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
                >
                  确认删除
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TaskList;
