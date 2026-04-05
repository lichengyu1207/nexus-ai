import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import type {
  UseWebSocketOptions,
  WebSocketMessage,
  MessageType,
} from '../types';

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    url,
    token,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectAttempts = 10,
    reconnectDelay = 1000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const messageHandlersRef = useRef<Set<(msg: WebSocketMessage) => void>>(new Set());
  const reconnectCountRef = useRef(0);

  useEffect(() => {
    if (!token) {
      setConnectionError('No authentication token provided');
      return;
    }

    const socket = io(url, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: autoReconnect,
      reconnectionAttempts,
      reconnectionDelay,
      reconnectionDelayMax: reconnectDelay * 5,
    });

    socket.on('connect', () => {
      setIsConnected(true);
      setIsReconnecting(false);
      setConnectionError(null);
      reconnectCountRef.current = 0;
      onConnect?.();
    });

    socket.on('disconnect', (reason) => {
      setIsConnected(false);
      if (reason === 'io server disconnect') {
        setConnectionError('Server disconnected');
      }
      onDisconnect?.();
    });

    socket.on('connect_error', (err) => {
      setConnectionError(err.message);
      setIsReconnecting(socket.active);
      onError?.(err);
    });

    socket.on('reconnect_attempt', (attempt) => {
      setIsReconnecting(true);
      reconnectCountRef.current = attempt;
    });

    socket.on('reconnect_failed', () => {
      setIsReconnecting(false);
      setConnectionError('Reconnection failed after maximum attempts');
    });

    socket.on('message', (msg: WebSocketMessage) => {
      messageHandlersRef.current.forEach((handler) => {
        try {
          handler(msg);
        } catch (e) {
          console.error('Error in message handler:', e);
        }
      });
      onMessage?.(msg);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [url, token, autoReconnect, reconnectAttempts, reconnectDelay, onMessage, onConnect, onDisconnect, onError]);

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
    if (socketRef.current?.connected) {
      socketRef.current.emit('message', {
        type: 'subscribe',
        payload: { topic },
      });
    }
  }, []);

  const unsubscribe = useCallback((topic: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('message', {
        type: 'unsubscribe',
        payload: { topic },
      });
    }
  }, []);

  const onMessageHandler = useCallback((handler: (msg: WebSocketMessage) => void) => {
    messageHandlersRef.current.add(handler);
    return () => {
      messageHandlersRef.current.delete(handler);
    };
  }, []);

  const disconnect = useCallback(() => {
    socketRef.current?.disconnect();
  }, []);

  const reconnect = useCallback(() => {
    if (socketRef.current && !socketRef.current.connected) {
      socketRef.current.connect();
    }
  }, []);

  return {
    isConnected,
    isReconnecting,
    connectionError,
    send,
    subscribe,
    unsubscribe,
    onMessage: onMessageHandler,
    disconnect,
    reconnect,
  };
}

export default useWebSocket;
