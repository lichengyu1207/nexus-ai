export interface DashboardStats {
  totalTasks: number;
  todayTasks: number;
  activeTasks: number;
  totalAgents: number;
  healthyAgents: number;
  busyAgents: number;
  errorAgents: number;
  crossEndEventsToday: number;
  healthScore: number;
}

export interface TaskSnapshot {
  id: string;
  name: string;
  progress: number;
  currentAgent: string;
  estimatedEnd: string;
}

export interface CollaborationEvent {
  id: string;
  timestamp: string;
  fromEnd: string;
  toEnd: string;
  description: string;
  actionable: boolean;
}

export interface TopologyNode {
  id: string;
  name: string;
  busyLevel: number;
  taskCount: number;
}

export interface TopologyLink {
  source: string;
  target: string;
  value: number;
}

export interface TopologyData {
  nodes: TopologyNode[];
  links: TopologyLink[];
}

export type UserRole = 'requester' | 'provider';

export const END_LABELS: Record<string, string> = {
  school: '院校端',
  enterprise: '企业端',
  government: '政府端',
  research: '科研端',
  public: '公众端',
};

export const ROLE_CONFIG: Record<UserRole, { label: string; description: string }> = {
  requester: { label: '需求方', description: '发布任务、招募人才' },
  provider: { label: '供应方', description: '执行任务、提供服务' },
};
