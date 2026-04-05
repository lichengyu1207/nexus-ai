import api from '../services/api';

export interface RecruitResult {
  success: boolean;
  agent_id: string;
  agent_name: string;
  rarity: 'N' | 'R' | 'SR' | 'SSR' | 'UR';
  rarity_color: string;
  department: string;
  level: number;
  skills: Array<{ name: string; level: number }>;
  cost: number;
  new_pity_count: number;
  error?: string;
}

export interface RecruitStats {
  total_recruits: number;
  pity_counter_sr: number;
  pity_counter_ssr: number;
  by_rarity: Record<string, number>;
  total_cost: number;
}

export interface ProbabilityInfo {
  recruit_type: string;
  probabilities: Record<string, number>;
  pity: {
    sr_threshold: number;
    ssr_threshold: number;
  };
}

export interface UserAgent {
  id: string;
  agent_id: string;
  name: string;
  rarity: string;
  rarity_color: string;
  department: string;
  level: number;
  experience: number;
  next_level_exp: number;
  skills: Array<{ name: string; level: number }>;
  status: 'idle' | 'working' | 'training';
  auto_work_enabled: boolean;
  daily_work_seconds: number;
  total_reward: number;
  created_at: string;
}

export interface AgentTemplate {
  id: string;
  name: string;
  rarity: string;
  department: string;
  skills: Array<{ name: string; description: string }>;
  description: string;
  base_stats: Record<string, number>;
}

export interface Bond {
  id: string;
  name: string;
  description: string;
  required_agents: string[];
  bonus: Record<string, number>;
  is_activated: boolean;
}

export const recruitApi = {
  async getProbabilityInfo(recruitType: string = 'basic'): Promise<ProbabilityInfo> {
    const response = await api.get('/api/recruit/probability', {
      params: { recruit_type: recruitType },
    });
    return response.data;
  },

  async basicRecruit(): Promise<RecruitResult> {
    const response = await api.post('/api/recruit/basic');
    return response.data;
  },

  async premiumRecruit(): Promise<RecruitResult> {
    const response = await api.post('/api/recruit/premium');
    return response.data;
  },

  async getStats(): Promise<{ success: boolean; stats: RecruitStats }> {
    const response = await api.get('/api/recruit/stats');
    return response.data;
  },

  async getMyAgents(): Promise<{ success: boolean; agents: UserAgent[]; count: number }> {
    const response = await api.get('/api/recruit/agents');
    return response.data;
  },

  async getAgentDetail(userAgentId: string): Promise<{ success: boolean; agent: UserAgent }> {
    const response = await api.get(`/api/recruit/agents/${userAgentId}`);
    return response.data;
  },

  async upgradeAgent(userAgentId: string): Promise<{ success: boolean; agent: UserAgent; cost: number }> {
    const response = await api.post('/api/recruit/agents/upgrade', {
      user_agent_id: userAgentId,
    });
    return response.data;
  },

  async assignDepartment(userAgentId: string, department: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/api/recruit/agents/assign', {
      user_agent_id: userAgentId,
      department,
    });
    return response.data;
  },

  async learnSkill(userAgentId: string, skillSlot: number): Promise<{ success: boolean; skill: { name: string; level: number }; cost: number }> {
    const response = await api.post('/api/recruit/agents/learn-skill', {
      user_agent_id: userAgentId,
      skill_slot: skillSlot,
    });
    return response.data;
  },

  async breakthrough(userAgentId: string): Promise<{ success: boolean; agent: UserAgent; cost: number; message: string }> {
    const response = await api.post('/api/recruit/agents/breakthrough', {
      user_agent_id: userAgentId,
    });
    return response.data;
  },

  async getAllTemplates(): Promise<{ success: boolean; templates: AgentTemplate[]; count: number }> {
    const response = await api.get('/api/recruit/templates');
    return response.data;
  },

  async getRarityInfo(): Promise<{ success: boolean; rarities: Record<string, any>; guarantee: Record<string, number> }> {
    const response = await api.get('/api/recruit/rarity-info');
    return response.data;
  },

  async getMyBonds(): Promise<{ success: boolean; bonds: Bond[]; count: number }> {
    const response = await api.get('/api/recruit/bonds');
    return response.data;
  },

  async getAllBonds(): Promise<{ success: boolean; bonds: Bond[]; total: number; activated: number }> {
    const response = await api.get('/api/recruit/all-bonds');
    return response.data;
  },
};

export default recruitApi;
