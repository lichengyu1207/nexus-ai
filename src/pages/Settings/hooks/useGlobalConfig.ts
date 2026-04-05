import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { GlobalConfig } from '../types';

async function fetchGlobalConfig(): Promise<GlobalConfig> {
  const response = await fetch('/api/admin/config');
  if (!response.ok) {
    throw new Error('Failed to fetch global config');
  }
  return response.json();
}

async function updateGlobalConfig(config: Partial<GlobalConfig>): Promise<GlobalConfig> {
  const response = await fetch('/api/admin/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    throw new Error('Failed to update global config');
  }
  return response.json();
}

export function useGlobalConfig() {
  const queryClient = useQueryClient();

  const query = useQuery<GlobalConfig, Error>({
    queryKey: ['globalConfig'],
    queryFn: fetchGlobalConfig,
    staleTime: 60000,
  });

  const updateMutation = useMutation<GlobalConfig, Error, Partial<GlobalConfig>>({
    mutationFn: updateGlobalConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['globalConfig'] });
    },
  });

  return {
    config: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateConfig: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
  };
}
