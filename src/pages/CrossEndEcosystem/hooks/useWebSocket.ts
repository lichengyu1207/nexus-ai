import { useEffect, useRef, useCallback, useState } from 'react';
import type { EndName, WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  endId: EndName;
  onMessage?: (data: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface WebSocketState {
  isConnected: boolean;
  isReconnecting: boolean;
  error: string | null;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    endId,
    onMessage,
    onConnect,
    onDisconnect,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isReconnecting: false,
    error: null,
  });

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/ends/${endId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setState({
          isConnected: true,
          isReconnecting: false,
          error: null,
        });
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          onMessage?.(data);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        setState((prev) => ({
          ...prev,
          isConnected: false,
        }));
        onDisconnect?.();

        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          setState((prev) => ({ ...prev, isReconnecting: true }));
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, reconnectInterval);
        } else {
          setState((prev) => ({
            ...prev,
            isReconnecting: false,
            error: 'Max reconnection attempts reached',
          }));
        }
      };

      ws.onerror = () => {
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
  }, [endId, onMessage, onConnect, onDisconnect, reconnectInterval, maxReconnectAttempts]);

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

  const sendMessage = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
  };
}
