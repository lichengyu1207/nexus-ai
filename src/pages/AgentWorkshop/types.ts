export interface Agent {
  id: string;
  name: string;
  department: 'san' | 'liu';
  description: string;
  currentTasks: number;
  status: 'healthy' | 'busy' | 'error';
  icon?: string;
}

export interface WorkflowNode {
  id: string;
  type: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  position?: { x: number; y: number };
  data?: {
    input?: unknown;
    output?: unknown;
    duration?: number;
    logs?: string[];
  };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  animated?: boolean;
}

export interface WorkflowData {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  callCount: number;
  lastCalled: string;
  enabled: boolean;
  parameters?: Record<string, unknown>;
}

export interface RunLog {
  id: string;
  taskId: string;
  startTime: string;
  duration: number;
  status: 'success' | 'failure';
  outputSummary: string;
  fullOutput?: string;
  error?: string;
}

export interface PaginatedLogs {
  logs: RunLog[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}
