import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import type { UnreadCountResponse } from '../types';

const API_BASE = '/api/notifications';

async function fetchUnreadCount(): Promise<number> {
  const response = await fetch(`${API_BASE}/unread-count`);
  if (!response.ok) {
    throw new Error('Failed to fetch unread count');
  }
  const data: UnreadCountResponse = await response.json();
  return data.count;
}

export function useUnreadCount() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: fetchUnreadCount,
    refetchInterval: 30000,
    staleTime: 10000,
  });

  const incrementUnread = useCallback(() => {
    queryClient.setQueryData<number>(
      ['notifications', 'unread-count'],
      (old) => (old ?? 0) + 1
    );
  }, [queryClient]);

  const decrementUnread = useCallback(() => {
    queryClient.setQueryData<number>(
      ['notifications', 'unread-count'],
      (old) => Math.max((old ?? 1) - 1, 0)
    );
  }, [queryClient]);

  const setUnreadCount = useCallback(
    (count: number) => {
      queryClient.setQueryData(['notifications', 'unread-count'], count);
    },
    [queryClient]
  );

  const resetUnreadCount = useCallback(() => {
    queryClient.setQueryData(['notifications', 'unread-count'], 0);
  }, [queryClient]);

  return {
    unreadCount: query.data ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    incrementUnread,
    decrementUnread,
    setUnreadCount,
    resetUnreadCount,
    refetch: query.refetch,
  };
}
