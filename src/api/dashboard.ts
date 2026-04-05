import api from '../services/api';

export interface AgentStatus {
  id: string;
  name: string;
  department: string;
  level: number;
  rarity: string;
  rarity_color: string;
  level_cap: number;
  status: 'idle' | 'busy' | 'working' | 'offline';
  current_task_id?: string;
  current_task_type?: string;
  current_task_description: string;
  work_start_time?: string;
  work_duration_seconds: number;
  efficiency: number;
  performance_today: number;
  base_salary: number;
  skills: Array<{ name: string; level: number }>;
  stats?: Record<string, number>;
  description?: string;
  auto_work_enabled: boolean;
  daily_work_seconds: number;
  daily_limit: number;
  total_reward: number;
}

export interface CurrentTask {
  id: string;
  type: 'user_task' | 'auto_task';
  task_type: string;
  description: string;
  status: string;
  progress: number;
  start_time?: string;
  assigned_agents: Array<{ id: string; name: string }>;
  base_reward?: number;
}

export interface DashboardStats {
  total_agents: number;
  online_agents: number;
  busy_agents: number;
  auto_work_agents: number;
  idle_agents: number;
  total_reward: number;
  today_work_seconds: number;
  pending_tasks: number;
}

export interface WorkLog {
  id: string;
  agent_id: string;
  agent_name: string;
  task_type: string;
  duration_seconds: number;
  reward_earned: number;
  status: string;
  created_at: string;
}

export interface TaskAssignmentOption {
  id: string;
  name: string;
  department: string;
  level: number;
  rarity: string;
  efficiency: number;
  skills: Array<{ name: string; level: number }>;
  recommendation_score: number;
  is_available: boolean;
}

export interface TaskTypeInfo {
  type: string;
  name: string;
  departments: string[];
}

export interface StartTaskRequest {
  task_type: 'analysis' | 'consult' | 'auto_work';
  input?: string;
  agent_ids?: string[];
  auto_assign?: boolean;
}

export interface StartTaskResponse {
  success: boolean;
  task_id: string;
  assigned_agents: string[];
  message: string;
}

export const dashboardApi = {
  async getAgentsStatus(): Promise<{ success: boolean; agents: AgentStatus[]; count: number }> {
    const response = await api.get('/dashboard/agents-status');
    return response.data;
  },

  async getCurrentTasks(): Promise<{ success: boolean; tasks: CurrentTask[]; count: number }> {
    const response = await api.get('/dashboard/current-tasks');
    return response.data;
  },

  async getStats(): Promise<{ success: boolean; stats: DashboardStats }> {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  async getLogs(limit: number = 20): Promise<{ success: boolean; logs: WorkLog[] }> {
    const response = await api.get('/dashboard/logs', { params: { limit } });
    return response.data;
  },

  async startTask(request: StartTaskRequest): Promise<StartTaskResponse> {
    const response = await api.post('/dashboard/start-task', request);
    return response.data;
  },

  async getTaskAssignmentOptions(taskType: string): Promise<{
    success: boolean;
    task_type: string;
    options: TaskAssignmentOption[];
  }> {
    const response = await api.get('/dashboard/task-assignment-options', {
      params: { task_type: taskType },
    });
    return response.data;
  },

  async getTaskTypes(): Promise<{
    success: boolean;
    task_types: TaskTypeInfo[];
  }> {
    const response = await api.get('/dashboard/task-types');
    return response.data;
  },
};

export default dashboardApi;
