type MessageType = 'message' | 'status' | 'workflow' | 'heartbeat' | 'connected' | 'error';

interface BaseEvent {
  type: MessageType;
  timestamp: string;
}

interface MessageEvent extends BaseEvent {
  type: 'message';
  id: string;
  taskId: string;
  agentId: string;
  agentName: string;
  content: string;
  messageType: 'log' | 'warning' | 'success' | 'info' | 'error';
  metadata?: Record<string, unknown>;
}

interface StatusEvent extends BaseEvent {
  type: 'status';
  taskId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep?: string;
  details?: Record<string, unknown>;
}

interface WorkflowEvent extends BaseEvent {
  type: 'workflow';
  taskId: string;
  step: string;
  agent: string;
  action: string;
  status: 'waiting' | 'processing' | 'completed' | 'failed';
  progress?: number;
  details?: Record<string, unknown>;
}

interface AgentStatusEvent extends BaseEvent {
  type: 'agent';
  taskId: string;
  agentId: string;
  agentName: string;
  status: 'waiting' | 'working' | 'done';
  progress?: number;
  currentTask?: string;
}

interface ConnectedEvent extends BaseEvent {
  type: 'connected';
  taskId: string;
  status: string;
}

interface HeartbeatEvent extends BaseEvent {
  type: 'heartbeat';
}

interface ErrorEvent extends BaseEvent {
  type: 'error';
  code: string;
  message: string;
}

type TaskStreamEvent = MessageEvent | StatusEvent | WorkflowEvent | AgentStatusEvent | ConnectedEvent | HeartbeatEvent | ErrorEvent;

type EventCallback<T extends TaskStreamEvent = TaskStreamEvent> = (event: T) => void;

interface TaskWebSocketOptions {
  taskId: string;
  onMessage?: (event: MessageEvent) => void;
  onStatus?: (event: StatusEvent) => void;
  onWorkflow?: (event: WorkflowEvent) => void;
  onAgent?: (event: AgentStatusEvent) => void;
  onConnected?: (event: ConnectedEvent) => void;
  onError?: (event: ErrorEvent) => void;
  onDisconnect?: () => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
}

class TaskWebSocket {
  private ws: WebSocket | null = null;
  private taskId: string;
  private callbacks: Map<MessageType, Set<EventCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private reconnectInterval: number;
  private heartbeatInterval: number;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isManualClose = false;
  private url: string;

  constructor(options: TaskWebSocketOptions) {
    this.taskId = options.taskId;
    this.maxReconnectAttempts = options.reconnectAttempts ?? 5;
    this.reconnectInterval = options.reconnectInterval ?? 2000;
    this.heartbeatInterval = options.heartbeatInterval ?? 30000;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = localStorage.getItem('token');
    this.url = `${protocol}//${host}/api/tasks/${this.taskId}/ws?token=${token}`;

    if (options.onMessage) this.on('message', options.onMessage);
    if (options.onStatus) this.on('status', options.onStatus);
    if (options.onWorkflow) this.on('workflow', options.onWorkflow);
    if (options.onAgent) this.on('agent', options.onAgent);
    if (options.onConnected) this.on('connected', options.onConnected);
    if (options.onError) this.on('error', options.onError);
    if (options.onDisconnect) {
      this.on('disconnect', options.onDisconnect as EventCallback);
    }
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isManualClose = false;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        console.log(`[TaskWebSocket] Connected to task ${this.taskId}`);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as TaskStreamEvent;
          this.handleEvent(data);
        } catch (error) {
          console.error('[TaskWebSocket] Failed to parse message:', error);
        }
      };

      this.ws.onclose = (event) => {
        this.stopHeartbeat();

        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        } else {
          this.emit('disconnect' as MessageType, { type: 'disconnect', timestamp: new Date().toISOString() } as TaskStreamEvent);
        }

        console.log(`[TaskWebSocket] Disconnected from task ${this.taskId}`, event.code, event.reason);
      };

      this.ws.onerror = (error) => {
        console.error('[TaskWebSocket] Error:', error);
        this.emit('error', {
          type: 'error',
          code: 'WEBSOCKET_ERROR',
          message: 'WebSocket connection error',
          timestamp: new Date().toISOString(),
        } as ErrorEvent);
      };
    } catch (error) {
      console.error('[TaskWebSocket] Failed to create WebSocket:', error);
      this.emit('error', {
        type: 'error',
        code: 'CONNECTION_FAILED',
        message: 'Failed to create WebSocket connection',
        timestamp: new Date().toISOString(),
      } as ErrorEvent);
    }
  }

  disconnect(): void {
    this.isManualClose = true;
    this.stopHeartbeat();
    this.clearReconnectTimer();

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('[TaskWebSocket] Cannot send message: WebSocket not connected');
    }
  }

  on<T extends TaskStreamEvent>(type: MessageType, callback: EventCallback<T>): () => void {
    if (!this.callbacks.has(type)) {
      this.callbacks.set(type, new Set());
    }
    this.callbacks.get(type)!.add(callback as EventCallback);

    return () => {
      this.callbacks.get(type)?.delete(callback as EventCallback);
    };
  }

  off(type: MessageType, callback: EventCallback): void {
    this.callbacks.get(type)?.delete(callback);
  }

  private handleEvent(event: TaskStreamEvent): void {
    this.emit(event.type, event);
  }

  private emit(type: MessageType, event: TaskStreamEvent): void {
    const callbacks = this.callbacks.get(type);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(event);
        } catch (error) {
          console.error(`[TaskWebSocket] Callback error for ${type}:`, error);
        }
      });
    }
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, this.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`[TaskWebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}

export function createTaskWebSocket(options: TaskWebSocketOptions): TaskWebSocket {
  return new TaskWebSocket(options);
}

export {
  TaskWebSocket,
  type TaskStreamEvent,
  type MessageEvent,
  type StatusEvent,
  type WorkflowEvent,
  type AgentStatusEvent,
  type ConnectedEvent,
  type HeartbeatEvent,
  type ErrorEvent,
  type EventCallback,
  type TaskWebSocketOptions,
};

export default TaskWebSocket;
