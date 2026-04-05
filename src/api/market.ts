import api from '../services/api';

export interface AgentTemplate {
  id: string;
  name: string;
  type: string;
  department: string;
  level: number;
  description: string;
  skills: Array<{ name: string; description: string }>;
  base_cost: number;
  rarity: string;
}

export interface UserAgent {
  id: string;
  agent_id: string;
  name: string;
  type: string;
  department: string;
  level: number;
  experience: number;
  next_level_exp: number;
  skills: Array<{ name: string; level: number }>;
  status: 'idle' | 'working' | 'training';
  owner: string;
  created_at: string;
  description?: string;
}

export interface FinanceSummary {
  total_integral: number;
  total_income: number;
  total_expenses: number;
  balance: number;
}

export interface RecruitResult {
  success: boolean;
  user_agent_id: string;
  agent_name: string;
  cost: number;
  new_level: number;
}

export const marketApi = {
  async getAvailableAgents(department?: string): Promise<{ success: boolean; agents: AgentTemplate[]; count: number }> {
    const params = department ? { department } : {};
    const response = await api.get('/api/market/agents', { params });
    return response.data;
  },

  async getAgentDetail(agentId: string): Promise<{ success: boolean; agent: AgentTemplate }> {
    const response = await api.get(`/api/market/agents/${agentId}`);
    return response.data;
  },

  async recruitAgent(agentId: string): Promise<RecruitResult> {
    const response = await api.post('/api/market/recruit', { agent_id: agentId });
    return response.data;
  },

  async getUserAgents(): Promise<{ success: boolean; agents: UserAgent[]; count: number }> {
    const response = await api.get('/api/market/user/agents');
    return response.data;
  },

  async upgradeAgent(userAgentId: string): Promise<{ success: boolean; agent: UserAgent; cost: number }> {
    const response = await api.post('/api/market/user/agents/upgrade', { user_agent_id: userAgentId });
    return response.data;
  },

  async dismissAgent(userAgentId: string, refundRate: number = 0.3): Promise<{ success: boolean; refund: number; message: string }> {
    const response = await api.post('/api/market/user/agents/dismiss', { 
      user_agent_id: userAgentId,
      refund_rate: refundRate,
    });
    return response.data;
  },

  async getUserFinance(): Promise<{ success: boolean; finance: FinanceSummary; agent_stats: any[] }> {
    const response = await api.get('/api/market/user/finance');
    return response.data;
  },

  async checkBalance(required?: number): Promise<{ success: boolean; sufficient: boolean; balance: number; required: number }> {
    const params = required ? { required } : {};
    const response = await api.get('/api/market/user/balance', { params });
    return response.data;
  },
};

export default marketApi;
