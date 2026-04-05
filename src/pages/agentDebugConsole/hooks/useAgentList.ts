import { useState, useEffect, useCallback } from 'react';
import type { Agent } from '../types';

interface UseAgentListOptions {
  status?: Agent['status'];
  type?: string;
  search?: string;
}

export function useAgentList(options: UseAgentListOptions = {}) {
  const { status, type, search } = options;
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchAgents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      if (type) params.append('type', type);
      if (search) params.append('search', search);
      
      const response = await fetch(`/api/agents?${params}`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      
      const data = await response.json();
      setAgents(data.agents || []);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  }, [status, type, search]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const startAgent = useCallback(async (agentId: string) => {
    const response = await fetch(`/api/agents/${agentId}/start`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to start agent');
    setAgents((prev) =>
      prev.map((a) => (a.id === agentId ? { ...a, status: 'running' } : a))
    );
  }, []);

  const stopAgent = useCallback(async (agentId: string) => {
    const response = await fetch(`/api/agents/${agentId}/stop`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to stop agent');
    setAgents((prev) =>
      prev.map((a) => (a.id === agentId ? { ...a, status: 'stopped' } : a))
    );
  }, []);

  const restartAgent = useCallback(async (agentId: string) => {
    const response = await fetch(`/api/agents/${agentId}/restart`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to restart agent');
    setAgents((prev) =>
      prev.map((a) => (a.id === agentId ? { ...a, status: 'running' } : a))
    );
  }, []);

  return {
    agents,
    isLoading,
    error,
    fetchAgents,
    startAgent,
    stopAgent,
    restartAgent,
  };
}
