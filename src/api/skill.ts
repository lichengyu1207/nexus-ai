import api from '../services/api';

export interface Skill {
  id: string;
  name: string;
  description: string;
  type: 'builtin' | 'external' | 'custom';
  category: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  dependencies: string[];
  applicable_agents: string[];
  cost_points: number;
  version: string;
  tags: string[];
  status: 'draft' | 'published' | 'deprecated';
  icon_url?: string;
  avg_rating: number;
  download_count: number;
  created_at: string;
  updated_at: string;
}

export interface SkillListParams {
  category?: string;
  type?: string;
  status?: string;
  keyword?: string;
  sort_by?: string;
  sort_order?: 'ASC' | 'DESC';
  page?: number;
  size?: number;
}

export interface SkillListResponse {
  skills: Skill[];
  total: number;
  page: number;
  size: number;
}

export interface SkillCreateRequest {
  name: string;
  description: string;
  type?: 'builtin' | 'external' | 'custom';
  category?: string;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  dependencies?: string[];
  applicable_agents?: string[];
  cost_points?: number;
  version?: string;
  tags?: string[];
  code_config?: Record<string, unknown>;
  icon_url?: string;
}

export interface SkillInvokeRequest {
  input_data: Record<string, unknown>;
  agent_id?: string;
}

export interface SkillInvokeResult {
  skill_id: string;
  status: 'success' | 'error';
  output_data: Record<string, unknown>;
  duration_ms: number;
  error_message?: string;
}

export interface WalletBalance {
  total_points: number;
  available_points: number;
  frozen_points: number;
  withdrawable_points: number;
}

export interface Transaction {
  id: string;
  user_id: string;
  transaction_type: string;
  amount: number;
  balance_after: number;
  description: string;
  related_id?: string;
  created_at: string;
}

export interface SkillReview {
  id: string;
  skill_id: string;
  user_id: string;
  rating: number;
  comment?: string;
  created_at: string;
}

export const skillApi = {
  async listSkills(params?: SkillListParams): Promise<SkillListResponse> {
    const response = await api.get('/skills', { params });
    return response.data;
  },

  async getSkill(skillId: string): Promise<Skill> {
    const response = await api.get(`/skills/${skillId}`);
    return response.data;
  },

  async createSkill(request: SkillCreateRequest): Promise<Skill> {
    const response = await api.post('/skills', request);
    return response.data;
  },

  async updateSkill(skillId: string, updates: Partial<SkillCreateRequest>): Promise<Skill> {
    const response = await api.put(`/skills/${skillId}`, updates);
    return response.data;
  },

  async deleteSkill(skillId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/skills/${skillId}`);
    return response.data;
  },

  async invokeSkill(skillId: string, request: SkillInvokeRequest): Promise<SkillInvokeResult> {
    const response = await api.post(`/skills/${skillId}/invoke`, request);
    return response.data;
  },

  async purchaseSkill(skillId: string, userId: string): Promise<{
    success: boolean;
    skill_id: string;
    points_spent: number;
    message: string;
  }> {
    const response = await api.post(`/skills/${skillId}/purchase`, { user_id: userId });
    return response.data;
  },

  async getSkillReviews(skillId: string, page: number = 1, size: number = 10): Promise<{
    reviews: SkillReview[];
    total: number;
  }> {
    const response = await api.get(`/skills/${skillId}/reviews`, { params: { page, size } });
    return response.data;
  },

  async createSkillReview(skillId: string, rating: number, comment?: string): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.post(`/skills/${skillId}/reviews`, { rating, comment });
    return response.data;
  },

  async getSkillVersions(skillId: string): Promise<{
    skill_id: string;
    versions: Array<{
      id: string;
      version: string;
      changelog: string;
      status: string;
      created_at: string;
    }>;
  }> {
    const response = await api.get(`/skills/${skillId}/versions`);
    return response.data;
  },

  async getWalletBalance(userId?: string): Promise<WalletBalance> {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/skills/wallet/balance', { params });
    return response.data;
  },

  async dailyCheckin(userId?: string): Promise<{
    success: boolean;
    points_earned: number;
    streak_days: number;
    message: string;
  }> {
    const params = userId ? { user_id: userId } : {};
    const response = await api.post('/skills/wallet/checkin', null, { params });
    return response.data;
  },

  async getTransactions(params?: {
    user_id?: string;
    transaction_type?: string;
    page?: number;
    size?: number;
  }): Promise<{
    transactions: Transaction[];
    total: number;
    page: number;
    size: number;
  }> {
    const response = await api.get('/skills/wallet/transactions', { params });
    return response.data;
  },
};

export default skillApi;
