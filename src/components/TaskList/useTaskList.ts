import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { fetchTasks, deleteTasks } from './api';
import { useTaskListStore } from './taskStore';
import { useEffect } from 'react';
import type { Task } from './types';

const LIMIT = 20;

export const useTaskList = () => {
  const { statusFilter, sortOrder, setHasMore, selectedIds, clearSelected } = useTaskListStore();
  const queryClient = useQueryClient();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    error,
    refetch,
  } = useInfiniteQuery({
    queryKey: ['tasks', statusFilter, sortOrder],
    queryFn: ({ pageParam = 1 }) =>
      fetchTasks({
        status: statusFilter,
        sort: sortOrder,
        page: pageParam,
        limit: LIMIT,
      }),
    getNextPageParam: (lastPage, allPages) => {
      const totalLoaded = allPages.reduce((sum, page) => sum + page.tasks.length, 0);
      if (totalLoaded < lastPage.total) {
        return allPages.length + 1;
      }
      return undefined;
    },
    initialPageParam: 1,
  });

  const tasks: Task[] = data?.pages.flatMap((page) => page.tasks) ?? [];

  useEffect(() => {
    setHasMore(!!hasNextPage);
  }, [hasNextPage, setHasMore]);

  const deleteSelected = async () => {
    if (selectedIds.size === 0) return;
    if (confirm(`确定删除 ${selectedIds.size} 个任务吗？`)) {
      await deleteTasks(Array.from(selectedIds));
      clearSelected();
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['taskStats'] });
    }
  };

  useEffect(() => {
    const hasProcessing = tasks.some((task) => task.status === 'processing');
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      refetch();
    }, 5000);

    return () => clearInterval(interval);
  }, [tasks, refetch]);

  return {
    tasks,
    isLoading,
    isFetchingNextPage,
    error,
    fetchNextPage,
    hasNextPage,
    deleteSelected,
    selectedIds: Array.from(selectedIds),
    toggleSelect: useTaskListStore.getState().toggleSelect,
    selectAll: useTaskListStore.getState().selectAll,
    clearSelected,
  };
};
