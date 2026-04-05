export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

export type AgentStatus = 'running' | 'paused' | 'stopped' | 'error';

export type ExecutionPhase = 'initialization' | 'planning' | 'execution' | 'tool_call' | 'reasoning' | 'completed' | 'failed';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
  details?: Record<string, unknown>;
  stackTrace?: string;
}

export interface StackFrame {
  id: string;
  name: string;
  type: 'function' | 'tool_call' | 'api_call' | 'llm_call';
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  startTime: string;
  endTime?: string;
  duration?: number;
  status: 'running' | 'completed' | 'failed';
  children?: StackFrame[];
  metadata?: Record<string, unknown>;
}

export interface Variable {
  name: string;
  type: string;
  value: unknown;
  size?: number;
  modified: boolean;
  scope: 'global' | 'local' | 'closure';
}

export interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: string;
}

export interface FlameGraphNode {
  name: string;
  value: number;
  children?: FlameGraphNode[];
  startTime: number;
  endTime: number;
  color?: string;
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: AgentStatus;
  currentTask?: string;
  lastActivity: string;
  metrics: {
    totalExecutions: number;
    successRate: number;
    avgDuration: number;
    errorCount: number;
  };
}

export interface DebugSession {
  id: string;
  agentId: string;
  startTime: string;
  endTime?: string;
  status: AgentStatus;
  logs: LogEntry[];
  callStack: StackFrame[];
  variables: Variable[];
  metrics: PerformanceMetric[];
  flameGraph?: FlameGraphNode;
}

export interface DebugCommand {
  type: 'pause' | 'resume' | 'step' | 'continue' | 'restart' | 'stop' | 'evaluate';
  payload?: Record<string, unknown>;
}

export interface DebugWebSocketMessage {
  type: 'log' | 'state_change' | 'stack_update' | 'variable_update' | 'metric_update' | 'flame_update' | 'command_response';
  payload: unknown;
  timestamp: string;
}

export const LOG_LEVEL_CONFIG: Record<LogLevel, { label: string; color: string; bgColor: string }> = {
  debug: { label: 'DEBUG', color: 'text-slate-400', bgColor: 'bg-slate-500/20' },
  info: { label: 'INFO', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
  warning: { label: 'WARN', color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  error: { label: 'ERROR', color: 'text-red-400', bgColor: 'bg-red-500/20' },
  critical: { label: 'CRITICAL', color: 'text-red-500', bgColor: 'bg-red-600/30' },
};

export const AGENT_STATUS_CONFIG: Record<AgentStatus, { label: string; color: string }> = {
  running: { label: '运行中', color: 'text-green-400' },
  paused: { label: '已暂停', color: 'text-amber-400' },
  stopped: { label: '已停止', color: 'text-slate-400' },
  error: { label: '错误', color: 'text-red-400' },
};

export const EXECUTION_PHASE_CONFIG: Record<ExecutionPhase, { label: string; icon: string }> = {
  initialization: { label: '初始化', icon: '🔧' },
  planning: { label: '规划', icon: '📋' },
  execution: { label: '执行', icon: '⚡' },
  tool_call: { label: '工具调用', icon: '🔧' },
  reasoning: { label: '推理', icon: '🧠' },
  completed: { label: '完成', icon: '✅' },
  failed: { label: '失败', icon: '❌' },
};
