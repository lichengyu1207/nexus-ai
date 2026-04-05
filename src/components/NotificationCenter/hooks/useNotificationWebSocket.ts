import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Notification, WsNotificationMessage } from '../types';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/notifications`;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 3000;

export interface UseNotificationWebSocketOptions {
  onNewNotification?: (notification: Notification) => void;
  enabled?: boolean;
}

export function useNotificationWebSocket(options: UseNotificationWebSocketOptions = {}) {
  const { onNewNotification, enabled = true } = options;
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        console.log('Notification WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const message: WsNotificationMessage = JSON.parse(event.data);

          if (message.type === 'new_notification') {
            const notification = message.payload;

            queryClient.setQueryData<{ pages: { notifications: Notification[] }[] } | undefined>(
              ['notifications', { readStatus: 'all' }],
              (old) => {
                if (!old) return old;
                return {
                  ...old,
                  pages: old.pages.map((page, index) =>
                    index === 0
                      ? { ...page, notifications: [notification, ...page.notifications] }
                      : page
                  ),
                };
              }
            );

            queryClient.setQueryData<{ pages: { notifications: Notification[] }[] } | undefined>(
              ['notifications', { readStatus: 'unread' }],
              (old) => {
                if (!old) return old;
                return {
                  ...old,
                  pages: old.pages.map((page, index) =>
                    index === 0
                      ? { ...page, notifications: [notification, ...page.notifications] }
                      : page
                  ),
                };
              }
            );

            queryClient.setQueryData<number>(
              ['notifications', 'unread-count'],
              (old) => (old ?? 0) + 1
            );

            onNewNotification?.(notification);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('Notification WebSocket disconnected');

        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current++;
          console.log(
            `Attempting to reconnect (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})...`
          );
          reconnectTimeoutRef.current = setTimeout(connect, RECONNECT_INTERVAL);
        } else {
          setError('WebSocket connection failed after maximum attempts');
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('WebSocket connection error');
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [enabled, queryClient, onNewNotification]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    isConnected,
    error,
    connect,
    disconnect,
  };
}
