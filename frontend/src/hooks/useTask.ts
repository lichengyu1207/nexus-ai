import { useState, useEffect, useCallback } from 'react';
import { taskApi } from '../api/tasks';
import { Task } from '../types';

export const useTask = (taskId: string | null) => {
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTask = useCallback(async () => {
    if (!taskId) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await taskApi.get(taskId);
      setTask(data);
    } catch (err: any) {
      setError(err?.detail || '获取任务失败');
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    fetchTask();
  }, [fetchTask]);

  return { task, loading, error, refetch: fetchTask };
};

export const useTasks = (params?: { status?: string; limit?: number }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await taskApi.list(params);
      setTasks(data.tasks || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      setError(err?.detail || '获取任务列表失败');
    } finally {
      setLoading(false);
    }
  }, [params?.status, params?.limit]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  return { tasks, total, loading, error, refetch: fetchTasks };
};

export const useTaskProgress = (taskId: string | null) => {
  const [steps, setSteps] = useState<any[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!taskId) return;

    const eventSource = taskApi.streamProgress(taskId);
    
    eventSource.onopen = () => {
      setConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'step') {
          setSteps(prev => [...prev, data.step]);
        } else if (data.type === 'complete') {
          eventSource.close();
          setConnected(false);
        }
      } catch (err) {
        console.error('Failed to parse SSE data:', err);
      }
    };

    eventSource.onerror = () => {
      setConnected(false);
      eventSource.close();
    };

    return () => {
      eventSource.close();
      setConnected(false);
    };
  }, [taskId]);

  return { steps, connected };
};

export default useTask;
