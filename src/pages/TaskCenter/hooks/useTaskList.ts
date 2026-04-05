import { useInfiniteQuery } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import type { Task, TaskFilters, TaskSort, TaskListResponse } from '../types';

interface UseTaskListParams {
  filters: TaskFilters;
  sort: TaskSort;
  enabled?: boolean;
}

async function fetchTasks(
  page: number,
  filters: TaskFilters,
  sort: TaskSort
): Promise<TaskListResponse> {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('limit', '20');

  if (filters.status.length > 0) {
    params.append('status', filters.status.join(','));
  }
  if (filters.dateRange) {
    params.append('startDate', filters.dateRange.start);
    params.append('endDate', filters.dateRange.end);
  }
  if (filters.agentIds && filters.agentIds.length > 0) {
    params.append('agentIds', filters.agentIds.join(','));
  }
  if (filters.tags && filters.tags.length > 0) {
    params.append('tags', filters.tags.join(','));
  }
  if (filters.searchText) {
    params.append('search', filters.searchText);
  }
  if (filters.progressMin !== undefined) {
    params.append('progressMin', String(filters.progressMin));
  }
  if (filters.progressMax !== undefined) {
    params.append('progressMax', String(filters.progressMax));
  }

  params.append('sortField', sort.field);
  params.append('sortOrder', sort.order);

  const response = await fetch(`/api/tasks?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch tasks');
  }
  return response.json();
}

export function useTaskList({ filters, sort, enabled = true }: UseTaskListParams) {
  const query = useInfiniteQuery<TaskListResponse, Error>({
    queryKey: ['tasks', filters, sort],
    queryFn: ({ pageParam = 1 }) => fetchTasks(pageParam, filters, sort),
    getNextPageParam: (lastPage) => lastPage.nextPage,
    initialPageParam: 1,
    enabled,
  });

  const tasks = query.data?.pages.flatMap((page) => page.items) ?? [];
  const total = query.data?.pages[0]?.total ?? 0;
  const hasProcessing = tasks.some((task) => task.status === 'processing');

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (hasProcessing && enabled) {
      intervalRef.current = setInterval(() => {
        query.refetch();
      }, 5000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [hasProcessing, enabled, query]);

  return {
    tasks,
    total,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    error: query.error,
    hasNextPage: query.hasNextPage,
    fetchNextPage: query.fetchNextPage,
    isFetchingNextPage: query.isFetchingNextPage,
    refetch: query.refetch,
  };
}
