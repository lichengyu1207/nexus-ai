import { useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { useTaskStore } from '../stores/taskStore';
import { useNotificationStore } from '../stores/notificationStore';
import type { WebSocketMessage, UseRealtimeUpdatesOptions } from '../types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:3001';

function getToken(): string {
  return localStorage.getItem('token') || '';
}

export function useRealtimeUpdates(options: UseRealtimeUpdatesOptions = {}) {
  const { enabled = true, topics = [] } = options;

  const updateTask = useTaskStore((state) => state.updateTask);
  const updateTaskProgress = useTaskStore((state) => state.updateTaskProgress);
  const addTaskLog = useTaskStore((state) => state.addTaskLog);
  const addNotification = useNotificationStore((state) => state.addNotification);
  const incrementUnreadCount = useNotificationStore((state) => state.incrementUnreadCount);

  const subscribedTopicsRef = useRef<Set<string>>(new Set());

  const handleMessage = useCallback(
    (msg: WebSocketMessage) => {
      switch (msg.type) {
        case 'task.updated': {
          const payload = msg.payload as { taskId: string; status: string; task?: unknown };
          if (payload.task) {
            updateTask(payload.task as Parameters<typeof updateTask>[0]);
          } else {
            updateTask({
              id: payload.taskId,
              status: payload.status as Parameters<typeof updateTask>[0]['status'],
            });
          }
          break;
        }

        case 'task.progress': {
          const payload = msg.payload as { taskId: string; progress: number; currentStep?: string };
          updateTaskProgress(payload.taskId, payload.progress, payload.currentStep);
          break;
        }

        case 'task.log': {
          const payload = msg.payload as { taskId: string; log: string; level: string; timestamp: number };
          addTaskLog(payload.taskId, {
            message: payload.log,
            level: payload.level as 'info' | 'warn' | 'error' | 'debug',
            timestamp: payload.timestamp,
          });
          break;
        }

        case 'notification.new': {
          const payload = msg.payload as Parameters<typeof addNotification>[0];
          addNotification(payload);
          incrementUnreadCount();
          break;
        }

        case 'system.alert': {
          const payload = msg.payload as { severity: string; message: string; component: string };
          console.warn(`[${payload.severity.toUpperCase()}] ${payload.component}: ${payload.message}`);
          break;
        }

        default:
          break;
      }
    },
    [updateTask, updateTaskProgress, addTaskLog, addNotification, incrementUnreadCount]
  );

  const {
    isConnected,
    isReconnecting,
    connectionError,
    subscribe,
    unsubscribe,
    onMessage,
  } = useWebSocket({
    url: WS_URL,
    token: getToken(),
    onMessage: handleMessage,
    autoReconnect: true,
  });

  useEffect(() => {
    const cleanup = onMessage(handleMessage);
    return cleanup;
  }, [onMessage, handleMessage]);

  useEffect(() => {
    if (!isConnected || !enabled) return;

    const currentTopics = subscribedTopicsRef.current;

    subscribe('user:me');
    currentTopics.add('user:me');

    topics.forEach((topic) => {
      if (!currentTopics.has(topic)) {
        subscribe(topic);
        currentTopics.add(topic);
      }
    });

    return () => {
      currentTopics.forEach((topic) => {
        unsubscribe(topic);
      });
      currentTopics.clear();
    };
  }, [isConnected, enabled, topics, subscribe, unsubscribe]);

  const subscribeToTask = useCallback(
    (taskId: string) => {
      const topic = `task:${taskId}`;
      if (!subscribedTopicsRef.current.has(topic)) {
        subscribe(topic);
        subscribedTopicsRef.current.add(topic);
      }
    },
    [subscribe]
  );

  const unsubscribeFromTask = useCallback(
    (taskId: string) => {
      const topic = `task:${taskId}`;
      if (subscribedTopicsRef.current.has(topic)) {
        unsubscribe(topic);
        subscribedTopicsRef.current.delete(topic);
      }
    },
    [unsubscribe]
  );

  const subscribeToAgent = useCallback(
    (agentId: string) => {
      const topic = `agent:${agentId}`;
      if (!subscribedTopicsRef.current.has(topic)) {
        subscribe(topic);
        subscribedTopicsRef.current.add(topic);
      }
    },
    [subscribe]
  );

  const unsubscribeFromAgent = useCallback(
    (agentId: string) => {
      const topic = `agent:${agentId}`;
      if (subscribedTopicsRef.current.has(topic)) {
        unsubscribe(topic);
        subscribedTopicsRef.current.delete(topic);
      }
    },
    [unsubscribe]
  );

  return {
    isConnected,
    isReconnecting,
    connectionError,
    subscribeToTask,
    unsubscribeFromTask,
    subscribeToAgent,
    unsubscribeFromAgent,
  };
}

export default useRealtimeUpdates;
