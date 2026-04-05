import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { governanceApi } from '@/api/governance';
import { useState, useEffect, useCallback } from 'react';

export interface GovernanceTask {
  task_id: string;
  query: string;
  status: 'queued' | 'planning' | 'reviewing' | 'executing' | 'completed' | 'failed';
  progress: number;
  current_province?: 'zhongshu' | 'menxia' | 'shangshu';
  current_department?: string;
  workflow_steps: WorkflowStep[];
  result?: Record<string, unknown>;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowStep {
  id: string;
  province: string;
  department?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  started_at?: string;
  completed_at?: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface GovernanceTaskEvent {
  type: 'status_update' | 'step_start' | 'step_complete' | 'progress' | 'error' | 'completed';
  task_id: string;
  data: {
    status?: string;
    progress?: number;
    current_province?: string;
    current_department?: string;
    step?: WorkflowStep;
    result?: Record<string, unknown>;
    error?: string;
  };
  timestamp: string;
}

export function useGovernanceTask() {
  const queryClient = useQueryClient();
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [taskData, setTaskData] = useState<GovernanceTask | null>(null);

  const createTask = useMutation({
    mutationFn: async (params: { query: string; style?: string }) => {
      const response = await governanceApi.submitTask({
        request: params.query,
        context: { style: params.style || 'balanced' }
      });
      return response;
    },
    onSuccess: (data) => {
      if (data.task_id) {
        setActiveTaskId(data.task_id);
        queryClient.invalidateQueries({ queryKey: ['governance-tasks'] });
      }
    },
  });

  const getTaskStatus = useQuery({
    queryKey: ['governance-task', activeTaskId],
    queryFn: () => governanceApi.getTaskStatus(activeTaskId!),
    enabled: !!activeTaskId && taskData?.status !== 'completed' && taskData?.status !== 'failed',
    refetchInterval: 2000,
  });

  useEffect(() => {
    if (getTaskStatus.data) {
      setTaskData(getTaskStatus.data as GovernanceTask);
    }
  }, [getTaskStatus.data]);

  const connectSSE = useCallback((taskId: string) => {
    const eventSource = new EventSource(`/api/sse/tasks/${taskId}/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data: GovernanceTaskEvent = JSON.parse(event.data);
        
        if (data.task_id === taskId) {
          setTaskData((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              status: data.data.status as GovernanceTask['status'] || prev.status,
              progress: data.data.progress ?? prev.progress,
              current_province: data.data.current_province as GovernanceTask['current_province'],
              current_department: data.data.current_department,
              workflow_steps: data.data.step 
                ? [...prev.workflow_steps.filter(s => s.id !== data.data.step!.id), data.data.step!]
                : prev.workflow_steps,
              result: data.data.result || prev.result,
              error: data.data.error || prev.error,
            };
          });
        }
      } catch (e) {
        console.error('Failed to parse SSE event:', e);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  useEffect(() => {
    if (activeTaskId) {
      const cleanup = connectSSE(activeTaskId);
      return cleanup;
    }
  }, [activeTaskId, connectSSE]);

  return {
    createTask: createTask.mutate,
    createTaskAsync: createTask.mutateAsync,
    isCreating: createTask.isPending,
    createError: createTask.error,
    taskData,
    activeTaskId,
    setActiveTaskId,
    isLoading: getTaskStatus.isLoading,
    refetch: getTaskStatus.refetch,
  };
}

export function useGovernanceTasks(limit: number = 20) {
  return useQuery({
    queryKey: ['governance-tasks', limit],
    queryFn: async () => {
      const response = await fetch('/api/governance/tasks?limit=' + limit);
      if (!response.ok) throw new Error('Failed to fetch tasks');
      return response.json();
    },
  });
}

export default useGovernanceTask;
