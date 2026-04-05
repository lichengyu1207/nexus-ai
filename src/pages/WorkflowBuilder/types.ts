export type NodeType = 'agent' | 'tool' | 'condition' | 'loop' | 'subflow' | 'trigger';

export type NodeStatus = 'pending' | 'running' | 'completed' | 'failed';

export type WorkflowStatus = 'running' | 'completed' | 'failed';

export type TriggerType = 'cron' | 'webhook' | 'event';

export type ErrorHandlingStrategy = 'fail' | 'retry' | 'ignore';

export interface WorkflowNodeData {
  label: string;
  config: Record<string, unknown>;
  inputs?: Record<string, string>;
  outputs?: Record<string, string>;
  errorHandling?: ErrorHandlingStrategy;
}

export interface WorkflowNode {
  id: string;
  type: NodeType;
  position: { x: number; y: number };
  data: WorkflowNodeData;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
}

export interface TriggerConfig {
  cron?: string;
  webhookUrl?: string;
  eventFilter?: string;
}

export interface Trigger {
  id: string;
  type: TriggerType;
  config: TriggerConfig;
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  version: number;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  triggers: Trigger[];
  createdAt: string;
  updatedAt: string;
  published: boolean;
}

export interface NodeExecution {
  nodeId: string;
  status: NodeStatus;
  startedAt: string;
  endedAt?: string;
  input?: unknown;
  output?: unknown;
  error?: string;
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  status: WorkflowStatus;
  startedAt: string;
  endedAt?: string;
  inputs: unknown;
  outputs?: unknown;
  nodeExecutions: NodeExecution[];
}

export interface WorkflowVersion {
  id: string;
  workflowId: string;
  version: number;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  triggers: Trigger[];
  createdAt: string;
  publishedAt?: string;
  published: boolean;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description?: string;
  thumbnail?: string;
  workflow: Omit<Workflow, 'id' | 'createdAt' | 'updatedAt'>;
  author?: string;
  downloads: number;
  rating: number;
  createdAt: string;
}

export interface NodeTemplate {
  type: NodeType;
  label: string;
  icon: string;
  description: string;
  category: 'agent' | 'tool' | 'control' | 'trigger';
  defaultConfig?: Record<string, unknown>;
}

export const NODE_TEMPLATES: NodeTemplate[] = [
  {
    type: 'agent',
    label: '智能体节点',
    icon: 'agent',
    description: '调用智能体执行任务',
    category: 'agent',
  },
  {
    type: 'tool',
    label: '工具节点',
    icon: 'tool',
    description: '调用 MCP 工具',
    category: 'tool',
  },
  {
    type: 'condition',
    label: '条件分支',
    icon: 'condition',
    description: '根据条件选择执行路径',
    category: 'control',
  },
  {
    type: 'loop',
    label: '循环节点',
    icon: 'loop',
    description: '循环执行子任务',
    category: 'control',
  },
  {
    type: 'subflow',
    label: '子流程',
    icon: 'subflow',
    description: '调用其他工作流',
    category: 'control',
  },
  {
    type: 'trigger',
    label: '触发器',
    icon: 'trigger',
    description: '定时或事件触发',
    category: 'trigger',
  },
];

export const AGENT_NODES = [
  { id: 'bingbu', label: '兵部', description: '军事与安全智能体' },
  { id: 'hubu', label: '户部', description: '财务与税务智能体' },
  { id: 'libu', label: '吏部', description: '人事与组织智能体' },
  { id: 'gongbu', label: '工部', description: '工程与建设智能体' },
  { id: 'libu2', label: '礼部', description: '礼仪与外交智能体' },
  { id: 'xingbu', label: '刑部', description: '司法与刑律智能体' },
];

export const TOOL_NODES = [
  { id: 'valuation', label: '估值工具', description: '房产估值分析' },
  { id: 'gis', label: 'GIS工具', description: '地理信息分析' },
  { id: 'report', label: '报告生成', description: '自动生成报告' },
  { id: 'notification', label: '通知服务', description: '发送通知消息' },
];

export const CONTROL_NODES = [
  { type: 'condition', label: '条件分支', description: 'if-else 条件判断' },
  { type: 'loop', label: '循环', description: 'for/while 循环' },
  { type: 'subflow', label: '子流程', description: '调用其他工作流' },
];

export const TRIGGER_NODES = [
  { type: 'cron', label: '定时触发', description: '按 cron 表达式触发' },
  { type: 'webhook', label: 'Webhook', description: 'HTTP 请求触发' },
  { type: 'event', label: '事件触发', description: '系统事件触发' },
];
