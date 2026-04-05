import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { BatchAction, BatchActionPayload } from '../types';

async function batchRetry(taskIds: string[]): Promise<void> {
  const response = await fetch('/api/tasks/batch/retry', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ taskIds }),
  });
  if (!response.ok) {
    throw new Error('Failed to retry tasks');
  }
}

async function batchDelete(taskIds: string[]): Promise<void> {
  const response = await fetch('/api/tasks/batch/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ taskIds }),
  });
  if (!response.ok) {
    throw new Error('Failed to delete tasks');
  }
}

async function exportTasks(taskIds: string[]): Promise<Blob> {
  const params = new URLSearchParams();
  params.append('taskIds', taskIds.join(','));

  const response = await fetch(`/api/tasks/export?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to export tasks');
  }
  return response.blob();
}

export function useBatchActions() {
  const queryClient = useQueryClient();

  const retryMutation = useMutation<void, Error, string[]>({
    mutationFn: batchRetry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const deleteMutation = useMutation<void, Error, string[]>({
    mutationFn: batchDelete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const exportMutation = useMutation<Blob, Error, string[]>({
    mutationFn: exportTasks,
  });

  const executeBatchAction = async (action: BatchAction, taskIds: string[]) => {
    switch (action) {
      case 'retry':
        return retryMutation.mutateAsync(taskIds);
      case 'delete':
        return deleteMutation.mutateAsync(taskIds);
      case 'export':
        const blob = await exportMutation.mutateAsync(taskIds);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tasks_export_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        break;
    }
  };

  return {
    executeBatchAction,
    isRetrying: retryMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isExporting: exportMutation.isPending,
    isPending: retryMutation.isPending || deleteMutation.isPending || exportMutation.isPending,
  };
}
