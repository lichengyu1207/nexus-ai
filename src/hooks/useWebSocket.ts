import { useState, useEffect, useCallback, useRef } from 'react';

export type MessageType = 
  | 'thinking'
  | 'response_chunk'
  | 'complete'
  | 'agent_status'
  | 'memory_invoked'
  | 'error';

export interface WebSocketMessage {
  type: MessageType;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface AgentStatusData {
  agentId: string;
  agentName: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
}

export interface MemoryInvokedData {
  memoryId: string;
  summary: string;
  relevance: number;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onThinking?: () => void;
  onResponseChunk?: (chunk: string) => void;
  onComplete?: (fullResponse: string) => void;
  onAgentStatus?: (data: AgentStatusData) => void;
  onMemoryInvoked?: (data: MemoryInvokedData) => void;
  onError?: (error: Error) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: Error | null;
  sendMessage: (data: unknown) => void;
  disconnect: () => void;
  reconnect: () => void;
  currentResponse: string;
  isThinking: boolean;
}

export const useWebSocket = (options: UseWebSocketOptions): UseWebSocketReturn => {
  const {
    url,
    onMessage,
    onThinking,
    onResponseChunk,
    onComplete,
    onAgentStatus,
    onMemoryInvoked,
    onError,
    onConnect,
    onDisconnect,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const responseBufferRef = useRef<string>('');

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || isConnecting) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectCountRef.current = 0;
        responseBufferRef.current = '';
        setCurrentResponse('');
        setIsThinking(false);
        onConnect?.();
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnect?.();

        if (!event.wasClean && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (event) => {
        const err = new Error('WebSocket connection error');
        setError(err);
        setIsConnecting(false);
        onError?.(err);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          onMessage?.(message);

          switch (message.type) {
            case 'thinking':
              setIsThinking(true);
              responseBufferRef.current = '';
              setCurrentResponse('');
              onThinking?.();
              break;

            case 'response_chunk':
              const chunk = message.data.chunk as string || '';
              responseBufferRef.current += chunk;
              setCurrentResponse(responseBufferRef.current);
              onResponseChunk?.(chunk);
              break;

            case 'complete':
              setIsThinking(false);
              const fullResponse = responseBufferRef.current;
              onComplete?.(fullResponse);
              responseBufferRef.current = '';
              break;

            case 'agent_status':
              onAgentStatus?.(message.data as AgentStatusData);
              break;

            case 'memory_invoked':
              onMemoryInvoked?.(message.data as MemoryInvokedData);
              break;

            case 'error':
              const errMsg = new Error(message.data.message as string || 'Unknown error');
              setError(errMsg);
              onError?.(errMsg);
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      wsRef.current = ws;
    } catch (e) {
      const err = e instanceof Error ? e : new Error('Failed to create WebSocket');
      setError(err);
      setIsConnecting(false);
      onError?.(err);
    }
  }, [url, isConnecting, onMessage, onThinking, onResponseChunk, onComplete, onAgentStatus, onMemoryInvoked, onError, onConnect, onDisconnect, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    reconnectCountRef.current = reconnectAttempts;
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnect');
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
  }, [clearReconnectTimeout, reconnectAttempts]);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectCountRef.current = 0;
    connect();
  }, [disconnect, connect]);

  const sendMessage = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    error,
    sendMessage,
    disconnect,
    reconnect,
    currentResponse,
    isThinking,
  };
};

export default useWebSocket;
