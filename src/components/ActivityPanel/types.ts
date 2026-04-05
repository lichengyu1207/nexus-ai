export type AgentHealthStatus = 'healthy' | 'busy' | 'error';
export type QueueTaskStatus = 'pending' | 'processing';
export type CallResult = 'success' | 'failure';

export interface AgentStatus {
  id: string;
  name: string;
  status: AgentHealthStatus;
  currentTasks: number;
}

export interface QueueTask {
  id: string;
  name: string;
  status: QueueTaskStatus;
  progress?: number;
  startTime?: string;
}

export interface CallLog {
  id: string;
  timestamp: string;
  agentId: string;
  agentName: string;
  toolId: string;
  toolName: string;
  result: CallResult;
  duration?: number;
  details?: {
    request?: unknown;
    response?: unknown;
    error?: string;
  };
}

export interface ActivitySnapshot {
  agents: AgentStatus[];
  tasks: QueueTask[];
  logs: CallLog[];
}

export type WsMessageType = 'agent_status_update' | 'task_queue_update' | 'new_call_log';

export interface WsMessage {
  type: WsMessageType;
  data: AgentStatus | QueueTask[] | CallLog;
}

export type ActivityTab = 'agents' | 'tasks' | 'logs';

export interface ActivityPanelState {
  isOpen: boolean;
  activeTab: ActivityTab;
  agents: AgentStatus[];
  tasks: QueueTask[];
  logs: CallLog[];
  unreadCount: number;
  isConnected: boolean;
  isReconnecting: boolean;
}
