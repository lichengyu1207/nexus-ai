import { useState, useCallback } from 'react';
import type { Agent, LogEntry, StackFrame } from '../types';

interface DebugSession {
  id: string;
  agentId: string;
  agentName: string;
  startTime: string;
  endTime?: string;
  status: 'active' | 'completed' | 'failed';
  logCount: number;
  errorCount: number;
  warningCount: number;
  duration?: number;
}

interface UseDebugHistoryOptions {
  agentId?: string;
  limit?: number;
}

export function useDebugHistory(options: UseDebugHistoryOptions = {}) {
  const { agentId, limit = 50 } = options;
  const [sessions, setSessions] = useState<DebugSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (agentId) params.append('agentId', agentId);
      params.append('limit', String(limit));
      
      const response = await fetch(`/api/debug/history?${params}`);
      if (!response.ok) throw new Error('Failed to fetch debug history');
      
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  }, [agentId, limit]);

  const getSessionDetails = useCallback(async (sessionId: string): Promise<{
    logs: LogEntry[];
    callStack: StackFrame[];
  }> => {
    const response = await fetch(`/api/debug/sessions/${sessionId}`);
    if (!response.ok) throw new Error('Failed to fetch session details');
    return response.json();
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    const response = await fetch(`/api/debug/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete session');
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
  }, []);

  const clearHistory = useCallback(async () => {
    const response = await fetch('/api/debug/history', {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to clear history');
    setSessions([]);
  }, []);

  return {
    sessions,
    isLoading,
    error,
    fetchHistory,
    getSessionDetails,
    deleteSession,
    clearHistory,
  };
}
