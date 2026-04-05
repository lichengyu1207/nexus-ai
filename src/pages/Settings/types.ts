export type Theme = 'dark' | 'light' | 'system';
export type Language = 'zh' | 'en';
export type ActorType = 'user' | 'agent';
export type ActionResult = 'success' | 'failure';
export type AuthType = 'none' | 'apiKey' | 'oauth';

export interface NotificationSettings {
  email: boolean;
  inApp: boolean;
  webhook?: string;
}

export interface UserSettings {
  theme: Theme;
  language: Language;
  notifications: NotificationSettings;
  voiceEnabled: boolean;
}

export interface AgentPermission {
  agentId: string;
  agentName: string;
  department: string;
  toolIds: string[];
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  actorType: ActorType;
  action: string;
  target: string;
  targetType: string;
  result: ActionResult;
  details?: string;
  ipAddress?: string;
}

export interface AuditLogFilters {
  startDate?: string;
  endDate?: string;
  actor?: string;
  actionType?: string;
  result?: ActionResult;
}

export interface AuditLogResponse {
  items: AuditLogEntry[];
  total: number;
  nextPage?: number;
}

export interface MCPTool {
  id: string;
  name: string;
  description: string;
  callCount: number;
  enabled: boolean;
  endpoint: string;
  authType: AuthType;
  parametersSchema?: Record<string, unknown>;
}

export interface MCPToolPayload {
  name: string;
  description: string;
  endpoint: string;
  authType: AuthType;
  parametersSchema?: Record<string, unknown>;
}

export interface GlobalConfig {
  maxConcurrentTasks: number;
  defaultModel: string;
  rateLimitPerSecond: number;
  dataRetentionDays: number;
}

export type SettingsTab = 
  | 'profile'
  | 'theme'
  | 'language'
  | 'notifications'
  | 'voice'
  | 'agent-permissions'
  | 'audit-logs'
  | 'mcp-tools'
  | 'global-config';

export interface MenuItem {
  key: SettingsTab;
  label: string;
  icon: string;
  isAdmin?: boolean;
}
