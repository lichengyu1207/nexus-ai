import api from '../services/api';

export interface TaskRequest {
  request: string;
  context?: Record<string, unknown>;
}

export interface TaskResponse {
  success: boolean;
  task_id?: string;
  result?: Record<string, unknown>;
  integral_cost?: number;
  steps?: WorkflowStep[];
  error?: string;
}

export interface TaskStatus {
  task_id: string;
  status: 'queued' | 'planning' | 'reviewing' | 'executing' | 'completed' | 'failed';
  progress: number;
  current_province?: 'zhongshu' | 'menxia' | 'shangshu';
  current_department?: string;
  current_step?: string;
  result?: Record<string, unknown>;
  error?: string;
  workflow_steps?: WorkflowStep[];
}

export interface WorkflowStep {
  id: string;
  province: string;
  department?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  started_at?: string;
  completed_at?: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface UserAgent {
  id: string;
  agent_id: string;
  name: string;
  department: string;
  level: number;
  salary: number;
  status: string;
  recruited_at: string;
  skills: any[];
  description: string;
}

export interface FinanceSummary {
  total_income: number;
  total_expenses: number;
  balance: number;
  pending_payments: number;
  period_start: string;
  period_end: string;
}

export interface SalaryLog {
  id: string;
  agent_id: string;
  agent_name: string;
  amount: number;
  reason: string;
  created_at: string;
}

export interface AgentSalaryStats {
  agent_id: string;
  agent_name: string;
  total_paid: number;
  payment_count: number;
  avg_payment: number;
}

export interface Department {
  name: string;
  role: string;
  agent: string;
  description: string;
}

export interface GovernanceTaskCreateRequest {
  query: string;
  style?: 'balanced' | 'aggressive' | 'conservative';
}

export interface GovernanceTaskCreateResponse {
  id: string;
  user_id: string;
  query: string;
  status: string;
  progress: number;
  style: string;
  created_at: string | null;
  completed_at: string | null;
  agents: any[];
}

export const governanceApi = {
  async submitTask(request: TaskRequest): Promise<TaskResponse> {
    const response = await api.post('/governance/task', request);
    return response.data;
  },

  async createTask(data: GovernanceTaskCreateRequest): Promise<GovernanceTaskCreateResponse> {
    const response = await api.post('/tasks', data);
    return response.data;
  },

  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  async getTask(taskId: string): Promise<TaskStatus> {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  async getTasks(params?: { limit?: number; offset?: number; status?: string }): Promise<{
    tasks: TaskStatus[];
    total: number;
  }> {
    const response = await api.get('/tasks', { params });
    return response.data;
  },

  async getUserAgents(): Promise<{
    success: boolean;
    core_agents: any[];
    recruited_agents: UserAgent[];
    total_count: number;
  }> {
    const response = await api.get('/governance/agents');
    return response.data;
  },

  async getFinanceSummary(): Promise<{ success: boolean; summary: FinanceSummary }> {
    const response = await api.get('/governance/finance');
    return response.data;
  },

  async getSalaryLogs(limit: number = 50, offset: number = 0): Promise<{
    success: boolean;
    logs: SalaryLog[];
    count: number;
  }> {
    const response = await api.get('/governance/salary-logs', { params: { limit, offset } });
    return response.data;
  },

  async getAgentSalaryStats(): Promise<{ success: boolean; stats: AgentSalaryStats[] }> {
    const response = await api.get('/governance/agent-stats');
    return response.data;
  },

  async getDepartments(): Promise<{
    success: boolean;
    departments: {
      三省: Department[];
      六部: Department[];
    };
  }> {
    const response = await api.get('/governance/departments');
    return response.data;
  },

  async getStatus(): Promise<{
    pending_requests: number;
    completed_today: number;
    avg_processing_time: number;
    is_active: boolean;
  }> {
    const response = await api.get('/governance/status');
    return response.data;
  },

  async submitRequest(params: { department: string; task_type: string; description: string }): Promise<TaskResponse> {
    const response = await api.post('/governance/request', params);
    return response.data;
  },
};

export default governanceApi;
