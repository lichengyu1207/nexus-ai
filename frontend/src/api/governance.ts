import apiClient from './client';

export interface AgentTemplate {
  id: string;
  name: string;
  department: string;
  level: number;
  skills: Array<{
    name: string;
    description: string;
    efficiency: number;
  }>;
  base_salary: number;
  recruit_cost: number;
  description: string;
  available: boolean;
}

export interface UserAgent {
  id: string;
  user_id: string;
  agent_id: string;
  name: string;
  department: string;
  level: number;
  salary: number;
  status: string;
  recruited_at: string;
  performance: {
    skills?: Array<{
      name: string;
      description: string;
      efficiency: number;
    }>;
    description?: string;
  };
}

export interface FinanceSummary {
  total_integral: number;
  total_spent: number;
  total_earned: number;
  active_agents: number;
  daily_salary_cost: number;
  monthly_salary_cost: number;
}

export interface RecruitResult {
  success: boolean;
  user_agent_id?: string;
  agent_name?: string;
  cost?: number;
  message?: string;
  error?: string;
}

export interface UpgradeResult {
  success: boolean;
  old_level?: number;
  new_level?: number;
  new_salary?: number;
  cost?: number;
  message?: string;
  error?: string;
}

export interface DismissResult {
  success: boolean;
  agent_name?: string;
  refund_amount?: number;
  message?: string;
  error?: string;
}

export const governanceApi = {
  getAvailableAgents: async (department?: string): Promise<{ success: boolean; agents: AgentTemplate[]; count: number }> => {
    const params = department ? { department } : {};
    const response = await apiClient.get('/api/market/agents', { params });
    return response.data;
  },

  getAgentDetail: async (agentId: string): Promise<{ success: boolean; agent: AgentTemplate }> => {
    const response = await apiClient.get(`/api/market/agents/${agentId}`);
    return response.data;
  },

  recruitAgent: async (agentId: string): Promise<RecruitResult> => {
    const response = await apiClient.post('/api/market/recruit', { agent_id: agentId });
    return response.data;
  },

  getUserAgents: async (): Promise<{ success: boolean; agents: UserAgent[]; count: number }> => {
    const response = await apiClient.get('/api/market/user/agents');
    return response.data;
  },

  upgradeAgent: async (userAgentId: string): Promise<UpgradeResult> => {
    const response = await apiClient.post('/api/market/user/agents/upgrade', { user_agent_id: userAgentId });
    return response.data;
  },

  dismissAgent: async (userAgentId: string, refundRate: number = 0.3): Promise<DismissResult> => {
    const response = await apiClient.post('/api/market/user/agents/dismiss', { 
      user_agent_id: userAgentId,
      refund_rate: refundRate 
    });
    return response.data;
  },

  getUserFinance: async (): Promise<{ success: boolean; finance: FinanceSummary; agent_stats: Array<{
    id: string;
    name: string;
    department: string;
    level: number;
    current_salary: number;
    task_count: number;
    total_salary_paid: number;
  }> }> => {
    const response = await apiClient.get('/api/market/user/finance');
    return response.data;
  },

  checkBalance: async (required?: number): Promise<{ success: boolean; sufficient: boolean; balance: number; required: number; shortage?: number }> => {
    const params = required ? { required } : {};
    const response = await apiClient.get('/api/market/user/balance', { params });
    return response.data;
  },

  getDepartments: async (): Promise<{ success: boolean; departments: {
    三省: Array<{ name: string; role: string; agent: string; description: string }>;
    六部: Array<{ name: string; role: string; agent: string; description: string }>;
  } }> => {
    const response = await apiClient.get('/api/governance/departments');
    return response.data;
  },

  getGovernanceAgents: async (): Promise<{ success: boolean; core_agents: Array<{
    agent_id: string;
    name: string;
    department: string;
    level: number;
    current_salary: number;
    status: string;
  }>; recruited_agents: UserAgent[]; total_count: number }> => {
    const response = await apiClient.get('/api/governance/agents');
    return response.data;
  },

  getGovernanceFinance: async (): Promise<{ success: boolean; summary: FinanceSummary }> => {
    const response = await apiClient.get('/api/governance/finance');
    return response.data;
  },

  submitTask: async (request: string, context?: Record<string, unknown>): Promise<{
    success: boolean;
    task_id?: string;
    result?: Record<string, unknown>;
    integral_cost?: number;
    steps?: Array<{
      step_id: string;
      step_name: string;
      department: string;
      agent_name: string;
      status: string;
      started_at: string;
      completed_at: string;
      input_data: Record<string, unknown>;
      output_data: Record<string, unknown>;
      error: string;
    }>;
    error?: string;
  }> => {
    const response = await apiClient.post('/api/governance/task', { request, context });
    return response.data;
  },

  getTaskStatus: async (taskId: string): Promise<{
    task_id: string;
    user_id: string;
    request: string;
    status: string;
    created_at: string;
    updated_at: string;
    plan: Record<string, unknown>;
    review_result: Record<string, unknown>;
    execution_result: Record<string, unknown>;
    final_result: Record<string, unknown>;
    steps: Array<Record<string, unknown>>;
    integral_cost: number;
  }> => {
    const response = await apiClient.get(`/api/governance/status/${taskId}`);
    return response.data;
  },
};

export default governanceApi;
