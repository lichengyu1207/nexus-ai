import React, { createContext, useContext, useCallback, useRef, useState, useEffect } from 'react';
import { io, Socket } from 'socket.io-client';
import type {
  WebSocketMessage,
  MessageType,
  WebSocketContextValue,
  ConnectionStatus,
} from './types';

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:3001';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

interface WebSocketProviderProps {
  children: React.ReactNode;
  url?: string;
  token?: string;
  autoConnect?: boolean;
}

export function WebSocketProvider({
  children,
  url = WS_URL,
  token,
  autoConnect = true,
}: WebSocketProviderProps) {
  const [status, setStatus] = useState<ConnectionStatus>({
    connected: false,
    reconnecting: false,
  });

  const socketRef = useRef<Socket | null>(null);
  const messageHandlersRef = useRef<Set<(msg: WebSocketMessage) => void>>(new Set());
  const subscribedTopicsRef = useRef<Set<string>>(new Set());

  const getToken = useCallback(() => {
    return token || localStorage.getItem('token') || '';
  }, [token]);

  useEffect(() => {
    if (!autoConnect) return;

    const authToken = getToken();
    if (!authToken) {
      setStatus({
        connected: false,
        reconnecting: false,
        error: 'No authentication token',
      });
      return;
    }

    const socket = io(url, {
      auth: { token: authToken },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
    });

    socket.on('connect', () => {
      setStatus({
        connected: true,
        reconnecting: false,
        lastConnected: Date.now(),
        error: undefined,
      });

      subscribedTopicsRef.current.forEach((topic) => {
        socket.emit('message', {
          type: 'subscribe',
          payload: { topic },
        });
      });
    });

    socket.on('disconnect', (reason) => {
      setStatus((prev) => ({
        ...prev,
        connected: false,
        reconnecting: socket.active,
        error: reason === 'io server disconnect' ? 'Server disconnected' : undefined,
      }));
    });

    socket.on('connect_error', (err) => {
      setStatus((prev) => ({
        ...prev,
        connected: false,
        reconnecting: socket.active,
        error: err.message,
      }));
    });

    socket.on('reconnect_attempt', () => {
      setStatus((prev) => ({
        ...prev,
        reconnecting: true,
      }));
    });

    socket.on('message', (msg: WebSocketMessage) => {
      messageHandlersRef.current.forEach((handler) => {
        try {
          handler(msg);
        } catch (e) {
          console.error('Error in message handler:', e);
        }
      });
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [url, autoConnect, getToken]);

  const send = useCallback(<T,>(type: MessageType, payload: T) => {
    if (socketRef.current?.connected) {
      const message: Omit<WebSocketMessage, 'id' | 'timestamp'> = {
        type,
        payload,
      };
      socketRef.current.emit('message', message);
    }
  }, []);

  const subscribe = useCallback((topic: string) => {
    subscribedTopicsRef.current.add(topic);
    if (socketRef.current?.connected) {
      socketRef.current.emit('message', {
        type: 'subscribe',
        payload: { topic },
      });
    }
  }, []);

  const unsubscribe = useCallback((topic: string) => {
    subscribedTopicsRef.current.delete(topic);
    if (socketRef.current?.connected) {
      socketRef.current.emit('message', {
        type: 'unsubscribe',
        payload: { topic },
      });
    }
  }, []);

  const onMessage = useCallback((handler: (msg: WebSocketMessage) => void) => {
    messageHandlersRef.current.add(handler);
    return () => {
      messageHandlersRef.current.delete(handler);
    };
  }, []);

  const value: WebSocketContextValue = {
    isConnected: status.connected,
    isReconnecting: status.reconnecting,
    connectionError: status.error || null,
    subscribe,
    unsubscribe,
    send,
    onMessage,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext(): WebSocketContextValue {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}

export { WebSocketContext };
