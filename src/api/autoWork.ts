import api from '../services/api';

export interface AutoWorkAgent {
  id: string;
  agent_id: string;
  name: string;
  department: string;
  level: number;
  rarity: string;
  daily_auto_work_limit: number;
  daily_work_seconds: number;
  status: 'idle' | 'working' | 'completed';
  auto_work_enabled: boolean;
  total_reward: number;
}

export interface AutoWorkStats {
  agents: AutoWorkAgent[];
  today_stats: {
    active_agents: number;
    total_seconds: number;
    total_reward: number;
  };
}

export interface AutoWorkLog {
  id: string;
  agent_id: string;
  agent_name: string;
  task_type: string;
  duration_seconds: number;
  reward_earned: number;
  status: string;
  created_at: string;
}

export interface SetAutoWorkRequest {
  agent_id: string;
  enabled: boolean;
}

export interface SetDailyLimitRequest {
  agent_id: string;
  limit_seconds: number;
}

export interface TaskType {
  type: string;
  suitable_departments: string[];
  duration_range: string;
}

export interface PendingTask {
  id: string;
  task_type: string;
  priority: number;
  status: string;
  assigned_agent_id: string | null;
  created_at: string;
}

export const autoWorkApi = {
  async setAutoWork(request: SetAutoWorkRequest): Promise<{ success: boolean; agent_id: string; enabled: boolean; message: string }> {
    const response = await api.post('/api/auto-work/toggle', {
      agent_id: request.agent_id,
      enabled: request.enabled,
    });
    return response.data;
  },

  async setDailyLimit(request: SetDailyLimitRequest): Promise<{ success: boolean; agent_id: string; daily_limit: number; message: string }> {
    const response = await api.post('/api/auto-work/set-limit', {
      agent_id: request.agent_id,
      limit_seconds: request.limit_seconds,
    });
    return response.data;
  },

  async getStats(): Promise<{ success: boolean; agents: AutoWorkAgent[]; today_stats: AutoWorkStats['today_stats'] }> {
    const response = await api.get('/api/auto-work/stats');
    return response.data;
  },

  async getLogs(agentId?: string, limit: number = 20, offset: number = 0): Promise<{ success: boolean; logs: AutoWorkLog[]; count: number }> {
    const params: any = { limit, offset };
    if (agentId) {
      params.agent_id = agentId;
    }
    const response = await api.get('/api/auto-work/logs', { params });
    return response.data;
  },

  async getPendingTasks(): Promise<{ success: boolean; tasks: PendingTask[]; count: number }> {
    const response = await api.get('/api/auto-work/tasks');
    return response.data;
  },

  async getTaskTypes(): Promise<{ success: boolean; task_types: TaskType[] }> {
    const response = await api.get('/api/auto-work/task-types');
    return response.data;
  },

  async triggerAssignment(): Promise<{ success: boolean; assigned_count: number; message: string }> {
    const response = await api.post('/api/auto-work/trigger-assign');
    return response.data;
  },

  async triggerExecution(): Promise<{ success: boolean; completed_count: number; message: string }> {
    const response = await api.post('/api/auto-work/trigger-execute');
    return response.data;
  },
};

export default autoWorkApi;
