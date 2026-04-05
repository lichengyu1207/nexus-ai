export interface MetricPoint {
  timestamp: number;
  value: number;
}

export interface MetricSeries {
  metric: string;
  unit: string;
  data: MetricPoint[];
}

export type AlertCondition = '>' | '<' | '>=' | '<=';

export type AlertSeverity = 'critical' | 'warning' | 'info';

export type AlertStatus = 'firing' | 'resolved';

export type HealthStatus = 'healthy' | 'degraded' | 'down';

export type NotificationType = 'email' | 'dingtalk' | 'wecom' | 'webhook';

export interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: AlertCondition;
  threshold: number;
  duration: number;
  channels: string[];
  enabled: boolean;
  silenceMinutes: number;
  createdAt: string;
  updatedAt: string;
}

export interface AlertEvent {
  id: string;
  ruleId: string;
  ruleName: string;
  severity: AlertSeverity;
  status: AlertStatus;
  triggeredAt: string;
  resolvedAt?: string;
  value: number;
  threshold: number;
  message?: string;
  handledBy?: string;
}

export interface HealthCheck {
  component: string;
  status: HealthStatus;
  latency: number;
  lastCheck: string;
  details?: string;
}

export interface NotificationChannel {
  id: string;
  type: NotificationType;
  name: string;
  config: {
    recipients?: string[];
    webhookUrl?: string;
    secret?: string;
  };
  enabled: boolean;
}

export interface TimeRange {
  from: number;
  to: number;
}

export interface MetricSummary {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendValue: number;
  threshold?: number;
  status: 'normal' | 'warning' | 'critical';
}

export const AVAILABLE_METRICS = [
  { id: 'agent.cpu.usage', name: '智能体 CPU 使用率', unit: '%' },
  { id: 'agent.memory.usage', name: '智能体内存使用率', unit: '%' },
  { id: 'task.queue.length', name: '任务队列长度', unit: '个' },
  { id: 'task.throughput', name: '任务吞吐量', unit: '个/秒' },
  { id: 'api.latency.p99', name: 'API P99 延迟', unit: 'ms' },
  { id: 'api.error.rate', name: 'API 错误率', unit: '%' },
  { id: 'db.connections', name: '数据库连接数', unit: '个' },
  { id: 'redis.memory', name: 'Redis 内存使用', unit: 'MB' },
  { id: 'model.latency', name: '模型响应延迟', unit: 'ms' },
];

export const COMPONENT_NAMES: Record<string, string> = {
  'agent-cluster': '智能体集群',
  'database': '数据库',
  'redis': 'Redis 缓存',
  'message-queue': '消息队列',
  'model-service': '模型服务',
  'api-gateway': 'API 网关',
};

export const SEVERITY_COLORS: Record<AlertSeverity, string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  warning: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  info: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
};

export const SEVERITY_LABELS: Record<AlertSeverity, string> = {
  critical: '严重',
  warning: '警告',
  info: '提醒',
};

export const HEALTH_STATUS_COLORS: Record<HealthStatus, string> = {
  healthy: 'text-green-400',
  degraded: 'text-yellow-400',
  down: 'text-red-400',
};

export const HEALTH_STATUS_LABELS: Record<HealthStatus, string> = {
  healthy: '正常',
  degraded: '降级',
  down: '故障',
};

export const NOTIFICATION_TYPE_LABELS: Record<NotificationType, string> = {
  email: '邮件',
  dingtalk: '钉钉',
  wecom: '企业微信',
  webhook: 'Webhook',
};
