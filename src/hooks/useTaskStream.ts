import { useEffect, useRef, useCallback, useState } from 'react';

interface MessageEvent {
  id: string;
  task_id: string;
  sender: string;
  recipient: string | null;
  type: string;
  content: Record<string, unknown>;
  timestamp: string;
}

interface StatusEvent {
  task_id: string;
  status: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

interface WorkflowEvent {
  task_id: string;
  step: string;
  agent: string;
  action: string;
  status: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

interface TaskStreamState {
  isConnected: boolean;
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  messages: MessageEvent[];
  workflowSteps: WorkflowEvent[];
  lastStatus: StatusEvent | null;
  error: string | null;
}

interface UseTaskStreamOptions {
  taskId: string | undefined;
  onMessage?: (message: MessageEvent) => void;
  onStatus?: (status: StatusEvent) => void;
  onWorkflow?: (workflow: WorkflowEvent) => void;
  onComplete?: () => void;
  onError?: (error: string) => void;
  fallbackPolling?: boolean;
  pollingInterval?: number;
}

const useTaskStream = (options: UseTaskStreamOptions) => {
  const {
    taskId,
    onMessage,
    onStatus,
    onWorkflow,
    onComplete,
    onError,
    fallbackPolling = true,
    pollingInterval = 3000,
  } = options;

  const [state, setState] = useState<TaskStreamState>({
    isConnected: false,
    status: 'disconnected',
    messages: [],
    workflowSteps: [],
    lastStatus: null,
    error: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!taskId) return;

    setState(prev => ({ ...prev, status: 'connecting', error: null }));

    const token = localStorage.getItem('token');
    const url = `/api/tasks/${taskId}/stream?token=${token}`;

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setState(prev => ({ ...prev, isConnected: true, status: 'connected' }));
        reconnectAttempts.current = 0;
      };

      eventSource.addEventListener('connected', (event) => {
        try {
          const data = JSON.parse(event.data);
          setState(prev => ({
            ...prev,
            lastStatus: {
              task_id: data.task_id,
              status: data.status,
              timestamp: new Date().toISOString(),
            },
          }));
        } catch (e) {
          console.error('Failed to parse connected event:', e);
        }
      });

      eventSource.addEventListener('message', (event) => {
        try {
          const data = JSON.parse(event.data);
          const message: MessageEvent = {
            id: data.id || crypto.randomUUID(),
            task_id: data.task_id || taskId,
            sender: data.sender,
            recipient: data.recipient,
            type: data.type,
            content: data.content || {},
            timestamp: data.timestamp || new Date().toISOString(),
          };
          
          setState(prev => ({
            ...prev,
            messages: [...prev.messages, message],
          }));
          
          onMessage?.(message);
        } catch (e) {
          console.error('Failed to parse message event:', e);
        }
      });

      eventSource.addEventListener('status', (event) => {
        try {
          const data = JSON.parse(event.data);
          const status: StatusEvent = {
            task_id: data.task_id,
            status: data.status,
            details: data.details,
            timestamp: data.timestamp || new Date().toISOString(),
          };
          
          setState(prev => ({ ...prev, lastStatus: status }));
          onStatus?.(status);
          
          if (status.status === 'completed' || status.status === 'failed') {
            onComplete?.();
          }
        } catch (e) {
          console.error('Failed to parse status event:', e);
        }
      });

      eventSource.addEventListener('workflow', (event) => {
        try {
          const data = JSON.parse(event.data);
          const workflow: WorkflowEvent = {
            task_id: data.task_id,
            step: data.step,
            agent: data.agent,
            action: data.action,
            status: data.status,
            details: data.details,
            timestamp: data.timestamp || new Date().toISOString(),
          };
          
          setState(prev => ({
            ...prev,
            workflowSteps: [...prev.workflowSteps, workflow],
          }));
          
          onWorkflow?.(workflow);
        } catch (e) {
          console.error('Failed to parse workflow event:', e);
        }
      });

      eventSource.addEventListener('heartbeat', () => {
        // Heartbeat received, connection is alive
      });

      eventSource.onerror = () => {
        eventSource.close();
        eventSourceRef.current = null;
        
        setState(prev => ({
          ...prev,
          isConnected: false,
          status: 'error',
          error: 'SSE连接失败',
        }));

        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          setTimeout(() => connect(), 2000 * reconnectAttempts.current);
        } else if (fallbackPolling) {
          startPolling();
        }
        
        onError?.('SSE连接失败，尝试轮询模式');
      };
    } catch (error) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: '无法创建SSE连接',
      }));
      
      if (fallbackPolling) {
        startPolling();
      }
    }
  }, [taskId, onMessage, onStatus, onWorkflow, onComplete, onError, fallbackPolling]);

  const startPolling = useCallback(() => {
    if (!taskId || pollingRef.current) return;

    const poll = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/tasks/${taskId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        
        if (!response.ok) throw new Error('Polling failed');
        
        const data = await response.json();
        
        const status: StatusEvent = {
          task_id: data.id,
          status: data.status,
          details: { progress: data.progress },
          timestamp: new Date().toISOString(),
        };
        
        setState(prev => ({
          ...prev,
          lastStatus: status,
          status: 'connected',
        }));
        
        onStatus?.(status);
        
        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling();
          onComplete?.();
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    };

    poll();
    pollingRef.current = setInterval(poll, pollingInterval);
  }, [taskId, pollingInterval, onStatus, onComplete]);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    stopPolling();
    setState(prev => ({ ...prev, isConnected: false, status: 'disconnected' }));
  }, [stopPolling]);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempts.current = 0;
    connect();
  }, [disconnect, connect]);

  useEffect(() => {
    if (taskId) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [taskId, connect, disconnect]);

  return {
    ...state,
    reconnect,
    disconnect,
  };
};

export default useTaskStream;
export type { MessageEvent, StatusEvent, WorkflowEvent, TaskStreamState, UseTaskStreamOptions };
