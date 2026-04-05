import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { MCPTool, MCPToolPayload } from '../types';

async function fetchMCPTools(): Promise<MCPTool[]> {
  const response = await fetch('/api/admin/tools');
  if (!response.ok) {
    throw new Error('Failed to fetch MCP tools');
  }
  return response.json();
}

async function createMCPTool(tool: MCPToolPayload): Promise<MCPTool> {
  const response = await fetch('/api/admin/tools', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tool),
  });
  if (!response.ok) {
    throw new Error('Failed to create MCP tool');
  }
  return response.json();
}

async function updateMCPTool(toolId: string, tool: Partial<MCPToolPayload>): Promise<MCPTool> {
  const response = await fetch(`/api/admin/tools/${toolId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tool),
  });
  if (!response.ok) {
    throw new Error('Failed to update MCP tool');
  }
  return response.json();
}

async function deleteMCPTool(toolId: string): Promise<void> {
  const response = await fetch(`/api/admin/tools/${toolId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete MCP tool');
  }
}

async function toggleMCPTool(toolId: string): Promise<MCPTool> {
  const response = await fetch(`/api/admin/tools/${toolId}/toggle`, {
    method: 'PATCH',
  });
  if (!response.ok) {
    throw new Error('Failed to toggle MCP tool');
  }
  return response.json();
}

export function useMCPTools() {
  const queryClient = useQueryClient();

  const query = useQuery<MCPTool[], Error>({
    queryKey: ['mcpTools'],
    queryFn: fetchMCPTools,
    staleTime: 60000,
  });

  const createMutation = useMutation<MCPTool, Error, MCPToolPayload>({
    mutationFn: createMCPTool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcpTools'] });
    },
  });

  const updateMutation = useMutation<MCPTool, Error, { toolId: string; tool: Partial<MCPToolPayload> }>({
    mutationFn: ({ toolId, tool }) => updateMCPTool(toolId, tool),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcpTools'] });
    },
  });

  const deleteMutation = useMutation<void, Error, string>({
    mutationFn: deleteMCPTool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcpTools'] });
    },
  });

  const toggleMutation = useMutation<MCPTool, Error, string>({
    mutationFn: toggleMCPTool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcpTools'] });
    },
  });

  return {
    tools: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    createTool: createMutation.mutateAsync,
    updateTool: updateMutation.mutateAsync,
    deleteTool: deleteMutation.mutateAsync,
    toggleTool: toggleMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isToggling: toggleMutation.isPending,
  };
}
