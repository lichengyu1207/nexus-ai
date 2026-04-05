import { useState, useEffect, useCallback, useRef } from 'react';
import type { DebugWebSocketMessage, LogEntry, StackFrame, Variable, FlameGraphNode, PerformanceMetric } from '../types';

interface UseDebugWebSocketOptions {
  agentId: string;
  onLog?: (entry: LogEntry) => void;
  onStateChange?: (state: unknown) => void;
  onStackUpdate?: (stack: StackFrame[]) => void;
  onVariableUpdate?: (variables: Variable[]) => void;
  onMetricUpdate?: (metrics: PerformanceMetric[]) => void;
  onFlameUpdate?: (flameGraph: FlameGraphNode) => void;
}

interface DebugState {
  isConnected: boolean;
  error: string | null;
  logs: LogEntry[];
  callStack: StackFrame[];
  variables: Variable[];
  metrics: PerformanceMetric[];
  flameGraph: FlameGraphNode | null;
}

export function useDebugWebSocket(options: UseDebugWebSocketOptions) {
  const { agentId, onLog, onStateChange, onStackUpdate, onVariableUpdate, onMetricUpdate, onFlameUpdate } = options;
  
  const [state, setState] = useState<DebugState>({
    isConnected: false,
    error: null,
    logs: [],
    callStack: [],
    variables: [],
    metrics: [],
    flameGraph: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/debug/${agentId}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setState((prev) => ({ ...prev, isConnected: true, error: null }));
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message: DebugWebSocketMessage = JSON.parse(event.data);
          
          switch (message.type) {
            case 'log':
              const logEntry = message.payload as LogEntry;
              setState((prev) => ({
                ...prev,
                logs: [...prev.logs.slice(-999), logEntry],
              }));
              onLog?.(logEntry);
              break;
              
            case 'state_change':
              onStateChange?.(message.payload);
              break;
              
            case 'stack_update':
              const stack = message.payload as StackFrame[];
              setState((prev) => ({ ...prev, callStack: stack }));
              onStackUpdate?.(stack);
              break;
              
            case 'variable_update':
              const variables = message.payload as Variable[];
              setState((prev) => ({ ...prev, variables }));
              onVariableUpdate?.(variables);
              break;
              
            case 'metric_update':
              const metrics = message.payload as PerformanceMetric[];
              setState((prev) => ({ ...prev, metrics }));
              onMetricUpdate?.(metrics);
              break;
              
            case 'flame_update':
              const flameGraph = message.payload as FlameGraphNode;
              setState((prev) => ({ ...prev, flameGraph }));
              onFlameUpdate?.(flameGraph);
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState((prev) => ({ ...prev, error: 'WebSocket connection error' }));
      };

      ws.onclose = () => {
        setState((prev) => ({ ...prev, isConnected: false }));
        wsRef.current = null;
        
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch (e) {
      setState((prev) => ({ ...prev, error: 'Failed to connect to debug server' }));
    }
  }, [agentId, onLog, onStateChange, onStackUpdate, onVariableUpdate, onMetricUpdate, onFlameUpdate]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  const sendCommand = useCallback((command: string, payload?: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        command,
        payload,
        timestamp: new Date().toISOString(),
      }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const clearLogs = useCallback(() => {
    setState((prev) => ({ ...prev, logs: [] }));
  }, []);

  return {
    ...state,
    connect,
    disconnect,
    sendCommand,
    clearLogs,
  };
}
