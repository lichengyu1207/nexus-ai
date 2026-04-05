import { useRef, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { motion, AnimatePresence } from 'framer-motion';
import { TaskListItem } from './TaskListItem';
import type { Task, ViewMode } from '../types';

interface TaskListProps {
  tasks: Task[];
  isLoading: boolean;
  isFetching: boolean;
  hasNextPage: boolean;
  fetchNextPage: () => void;
  isFetchingNextPage: boolean;
  selectedIds: Set<string>;
  onSelectTask: (taskId: string, selected: boolean) => void;
  onTaskClick: (taskId: string) => void;
  onTaskRetry: (taskId: string) => void;
  onTaskDelete: (taskId: string) => void;
  viewMode: ViewMode;
}

const ITEM_HEIGHT = 100;
const TABLE_ROW_HEIGHT = 56;

export function TaskList({
  tasks,
  isLoading,
  isFetching,
  hasNextPage,
  fetchNextPage,
  isFetchingNextPage,
  selectedIds,
  onSelectTask,
  onTaskClick,
  onTaskRetry,
  onTaskDelete,
  viewMode,
}: TaskListProps) {
  const listRef = useRef<List>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  const useVirtualScroll = tasks.length > 50;
  const itemHeight = viewMode === 'card' ? ITEM_HEIGHT : TABLE_ROW_HEIGHT;

  const handleLoadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const Row = useCallback(
    ({ index, style }: { index: number; style: React.CSSProperties }) => {
      if (index === tasks.length) {
        return (
          <div style={style} className="flex items-center justify-center py-4">
            {isFetchingNextPage ? (
              <div className="flex items-center gap-2 text-gray-400">
                <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                <span>加载更多...</span>
              </div>
            ) : hasNextPage ? (
              <button
                onClick={handleLoadMore}
                className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300
                  hover:bg-slate-600 transition-colors"
              >
                加载更多
              </button>
            ) : null}
          </div>
        );
      }

      const task = tasks[index];
      return (
        <div style={style}>
          <TaskListItem
            task={task}
            isSelected={selectedIds.has(task.id)}
            onSelect={onSelectTask}
            onClick={onTaskClick}
            onRetry={onTaskRetry}
            onDelete={onTaskDelete}
            viewMode={viewMode}
          />
        </div>
      );
    },
    [tasks, selectedIds, onSelectTask, onTaskClick, onTaskRetry, onTaskDelete, viewMode, isFetchingNextPage, hasNextPage, handleLoadMore]
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-400">加载任务列表...</span>
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-gray-400 mb-2">暂无任务</p>
          <p className="text-gray-500 text-sm">点击"新建任务"创建您的第一个任务</p>
        </div>
      </div>
    );
  }

  if (useVirtualScroll) {
    return (
      <div className="h-full">
        <List
          ref={listRef}
          height={600}
          itemCount={tasks.length + (hasNextPage ? 1 : 0)}
          itemSize={itemHeight}
          width="100%"
          role="rowgroup"
        >
          {Row}
        </List>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4">
      <AnimatePresence mode="popLayout">
        {tasks.map((task) => (
          <motion.div
            key={task.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            layout
          >
            <TaskListItem
              task={task}
              isSelected={selectedIds.has(task.id)}
              onSelect={onSelectTask}
              onClick={onTaskClick}
              onRetry={onTaskRetry}
              onDelete={onTaskDelete}
              viewMode={viewMode}
            />
          </motion.div>
        ))}
      </AnimatePresence>

      {hasNextPage && (
        <div
          ref={loadMoreRef}
          className="flex items-center justify-center py-4"
        >
          {isFetchingNextPage ? (
            <div className="flex items-center gap-2 text-gray-400">
              <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
              <span>加载更多...</span>
            </div>
          ) : (
            <button
              onClick={handleLoadMore}
              className="px-4 py-2 rounded-lg bg-slate-700 text-gray-300
                hover:bg-slate-600 transition-colors"
            >
              加载更多
            </button>
          )}
        </div>
      )}
    </div>
  );
}
