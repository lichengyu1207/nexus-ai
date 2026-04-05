import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { AgentPermission } from '../types';

async function fetchAgentPermissions(): Promise<AgentPermission[]> {
  const response = await fetch('/api/admin/agents/permissions');
  if (!response.ok) {
    throw new Error('Failed to fetch agent permissions');
  }
  return response.json();
}

async function updateAgentPermission(
  agentId: string,
  toolIds: string[]
): Promise<AgentPermission> {
  const response = await fetch(`/api/admin/agents/${agentId}/permissions`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ toolIds }),
  });
  if (!response.ok) {
    throw new Error('Failed to update agent permission');
  }
  return response.json();
}

async function batchUpdatePermissions(payload: {
  agentIds: string[];
  toolIds: string[];
}): Promise<void> {
  const response = await fetch('/api/admin/agents/permissions/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('Failed to batch update permissions');
  }
}

export function useAgentPermissions() {
  const queryClient = useQueryClient();

  const query = useQuery<AgentPermission[], Error>({
    queryKey: ['agentPermissions'],
    queryFn: fetchAgentPermissions,
    staleTime: 60000,
  });

  const updateMutation = useMutation<
    AgentPermission,
    Error,
    { agentId: string; toolIds: string[] }
  >({
    mutationFn: ({ agentId, toolIds }) => updateAgentPermission(agentId, toolIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agentPermissions'] });
    },
  });

  const batchMutation = useMutation<
    void,
    Error,
    { agentIds: string[]; toolIds: string[] }
  >({
    mutationFn: batchUpdatePermissions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agentPermissions'] });
    },
  });

  return {
    permissions: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    updatePermission: updateMutation.mutateAsync,
    batchUpdate: batchMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    isBatchUpdating: batchMutation.isPending,
  };
}
