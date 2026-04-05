import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTaskList } from './useTaskList';
import { TaskListHeader } from './TaskListHeader';
import TaskListItem from './TaskListItem';
import VirtualList from './VirtualList';
import type { Task } from './types';

const ITEM_HEIGHT = 180;
const CONTAINER_HEIGHT = 600;

const TaskList: React.FC = () => {
  const navigate = useNavigate();
  const {
    tasks,
    isLoading,
    isFetchingNextPage,
    error,
    fetchNextPage,
    hasNextPage,
    deleteSelected,
    selectedIds,
    toggleSelect,
    selectAll,
  } = useTaskList();

  const handleViewReport = useCallback(
    (taskId: string) => {
      navigate(`/tasks/${taskId}/report`);
    },
    [navigate]
  );

  const handleRetry = useCallback((taskId: string) => {
    console.log('Retry task:', taskId);
  }, []);

  const handleSelectAll = useCallback(() => {
    const selectableIds = tasks
      .filter((t) => t.status === 'completed' || t.status === 'failed')
      .map((t) => t.id);
    selectAll(selectableIds);
  }, [tasks, selectAll]);

  const renderTask = useCallback(
    (task: Task, index: number) => (
      <div key={task.id} className="mb-4">
        <TaskListItem
          task={task}
          isSelected={selectedIds.includes(task.id)}
          onToggleSelect={toggleSelect}
          onViewReport={handleViewReport}
          onRetry={handleRetry}
        />
      </div>
    ),
    [selectedIds, toggleSelect, handleViewReport, handleRetry]
  );

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 text-center">
        <p className="text-red-600 dark:text-red-400">加载失败，请稍后重试</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-3 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          刷新页面
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <TaskListHeader
        onDeleteSelected={deleteSelected}
        selectedCount={selectedIds.length}
      />

      {tasks.length > 0 && (
        <div className="flex items-center justify-between mb-3 px-1">
          <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={
                selectedIds.length > 0 &&
                selectedIds.length ===
                  tasks.filter((t) => t.status === 'completed' || t.status === 'failed').length
              }
              onChange={handleSelectAll}
              className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500"
            />
            全选已完成/失败
          </label>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            共 {tasks.length} 个任务
          </span>
        </div>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent" />
        </div>
      ) : (
        <VirtualList<Task>
          items={tasks}
          itemHeight={ITEM_HEIGHT}
          containerHeight={CONTAINER_HEIGHT}
          renderItem={renderTask}
          onLoadMore={fetchNextPage}
          hasMore={hasNextPage}
          isLoading={isFetchingNextPage}
          emptyComponent={
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
              </div>
              <p className="text-lg text-gray-500 dark:text-gray-400">暂无任务</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                点击右上角"新建任务"开始
              </p>
            </div>
          }
        />
      )}
    </div>
  );
};

export default TaskList;
