export type MessageType =
  | 'task.updated'
  | 'task.progress'
  | 'task.log'
  | 'notification.new'
  | 'agent.status'
  | 'debug.callstack'
  | 'system.alert'
  | 'ping'
  | 'pong'
  | 'subscribe'
  | 'unsubscribe'
  | 'subscribed'
  | 'unsubscribed';

export interface WebSocketMessage<T = unknown> {
  id: string;
  type: MessageType;
  payload: T;
  timestamp: number;
  ack?: boolean;
}

export interface TaskUpdatedPayload {
  taskId: string;
  status: string;
  task?: Task;
}

export interface TaskProgressPayload {
  taskId: string;
  progress: number;
  currentStep?: string;
}

export interface TaskLogPayload {
  taskId: string;
  log: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  timestamp: number;
}

export interface NotificationPayload {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
}

export interface AgentStatusPayload {
  agentId: string;
  status: 'idle' | 'running' | 'error' | 'stopped';
  lastActive?: string;
}

export interface DebugCallstackPayload {
  agentId: string;
  callstack: DebugStackFrame[];
}

export interface DebugStackFrame {
  name: string;
  type: string;
  input?: unknown;
  output?: unknown;
  children?: DebugStackFrame[];
}

export interface SystemAlertPayload {
  alertId: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  component: string;
}

export interface SubscribePayload {
  topic: string;
}

export interface Task {
  id: string;
  userId: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  currentStep?: string;
  result?: unknown;
  error?: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  lastConnected?: number;
  error?: string;
}

export interface WebSocketContextValue {
  isConnected: boolean;
  isReconnecting: boolean;
  connectionError: string | null;
  subscribe: (topic: string) => void;
  unsubscribe: (topic: string) => void;
  send: <T>(type: MessageType, payload: T) => void;
  onMessage: (handler: MessageHandler) => () => void;
}

export type MessageHandler = (message: WebSocketMessage) => void;

export interface UseWebSocketOptions {
  url: string;
  token: string;
  onMessage?: (msg: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (err: Error) => void;
  autoReconnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export interface UseRealtimeUpdatesOptions {
  enabled?: boolean;
  topics?: string[];
}
