import { useEffect, useRef, useCallback, useState } from 'react';
import type { WsMessage, AgentStatus, QueueTask, CallLog } from '../types';

interface UseActivityWebSocketOptions {
  onAgentStatusUpdate: (agent: AgentStatus) => void;
  onTaskQueueUpdate: (tasks: QueueTask[]) => void;
  onNewCallLog: (log: CallLog) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  enabled?: boolean;
}

interface WebSocketState {
  isConnected: boolean;
  isReconnecting: boolean;
  error: string | null;
}

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 3000;

export function useActivityWebSocket(options: UseActivityWebSocketOptions) {
  const {
    onAgentStatusUpdate,
    onTaskQueueUpdate,
    onNewCallLog,
    onConnect,
    onDisconnect,
    enabled = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isReconnecting: false,
    error: null,
  });

  const connect = useCallback(() => {
    if (!enabled || !mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/activity`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (!mountedRef.current) return;
        reconnectAttemptsRef.current = 0;
        setState({
          isConnected: true,
          isReconnecting: false,
          error: null,
        });
        onConnect?.();
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const message: WsMessage = JSON.parse(event.data);
          switch (message.type) {
            case 'agent_status_update':
              onAgentStatusUpdate(message.data as AgentStatus);
              break;
            case 'task_queue_update':
              onTaskQueueUpdate(message.data as QueueTask[]);
              break;
            case 'new_call_log':
              onNewCallLog(message.data as CallLog);
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setState((prev) => ({ ...prev, isConnected: false }));
        onDisconnect?.();

        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          setState((prev) => ({ ...prev, isReconnecting: true }));
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, RECONNECT_INTERVAL);
        } else {
          setState((prev) => ({
            ...prev,
            isReconnecting: false,
            error: 'Max reconnection attempts reached',
          }));
        }
      };

      ws.onerror = () => {
        if (!mountedRef.current) return;
        setState((prev) => ({
          ...prev,
          error: 'WebSocket connection error',
        }));
      };

      wsRef.current = ws;
    } catch (e) {
      setState((prev) => ({
        ...prev,
        error: 'Failed to create WebSocket connection',
      }));
    }
  }, [enabled, onAgentStatusUpdate, onTaskQueueUpdate, onNewCallLog, onConnect, onDisconnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setState({
      isConnected: false,
      isReconnecting: false,
      error: null,
    });
  }, []);

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    disconnect();
    connect();
  }, [connect, disconnect]);

  useEffect(() => {
    mountedRef.current = true;
    if (enabled) {
      connect();
    }
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    reconnect,
  };
}
