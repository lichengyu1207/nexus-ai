import api from '../services/api';

export interface RecommendedTeam {
  id: string;
  name: string;
  matchScore: number;
  skills: string[];
  memberCount: number;
  recentTasks: number;
}

export interface RecommendedTalent {
  id: string;
  name: string;
  avatar?: string;
  matchScore: number;
  skills: Array<{
    name: string;
    proficiency: number;
    successRate: number;
  }>;
  rating: number;
  completedTasks: number;
  isAvailable: boolean;
}

export interface Recruitment {
  id: string;
  teamId: string;
  teamName: string;
  title: string;
  description: string;
  requiredSkills: string[];
  budget: number;
  deadline: string;
  status: 'open' | 'closed' | 'cancelled';
  bidsCount: number;
  createdAt: string;
}

export interface Bid {
  id: string;
  recruitmentId: string;
  talentId: string;
  talentName: string;
  talentAvatar?: string;
  proposal: string;
  price: number;
  estimatedDays: number;
  status: 'pending' | 'accepted' | 'rejected';
  createdAt: string;
}

export interface MemoryItem {
  id: string;
  title: string;
  content: string;
  tags: string[];
  importance: number;
  sourceTaskId?: string;
  sourceTeamId?: string;
  createdAt: string;
}

export interface DistributionResult {
  success: boolean;
  successCount: number;
  distributedTo: string[];
}

export const relationApi = {
  getRecommendedTeams: async (taskId: string): Promise<RecommendedTeam[]> => {
    const response = await api.get(`/tasks/${taskId}/recommended-teams`);
    return response.data.teams;
  },

  getRecommendedTalents: async (params: { skills?: string[]; teamId?: string }): Promise<RecommendedTalent[]> => {
    const response = await api.get('/talents/recommended', {
      params: {
        skills: params.skills?.join(','),
        teamId: params.teamId
      }
    });
    return response.data.talents;
  },

  createTaskFromConsult: async (data: { consultResultId: string; teamId?: string; title?: string }): Promise<{ task: { id: string; title: string; status: string } }> => {
    const response = await api.post('/tasks/from-consult', data);
    return response.data;
  },

  getTeamRecruitments: async (teamId: string): Promise<Recruitment[]> => {
    const response = await api.get(`/teams/${teamId}/recruitments`);
    return response.data.recruitments;
  },

  createRecruitment: async (data: {
    teamId: string;
    title: string;
    description: string;
    requiredSkills: string[];
    budget: number;
    deadline: string;
  }): Promise<Recruitment> => {
    const response = await api.post('/recruitments', data);
    return response.data;
  },

  getRecruitment: async (recruitmentId: string): Promise<Recruitment> => {
    const response = await api.get(`/recruitments/${recruitmentId}`);
    return response.data;
  },

  getRecruitmentBids: async (recruitmentId: string): Promise<Bid[]> => {
    const response = await api.get(`/recruitments/${recruitmentId}/bids`);
    return response.data.bids;
  },

  acceptBid: async (bidId: string): Promise<{
    success: boolean;
    task: { id: string; title: string };
    bid: Bid;
  }> => {
    const response = await api.put(`/bids/${bidId}/accept`);
    return response.data;
  },

  rejectBid: async (bidId: string, reason?: string): Promise<{ success: boolean }> => {
    const response = await api.put(`/bids/${bidId}/reject`, { reason });
    return response.data;
  },

  submitBid: async (recruitmentId: string, data: {
    proposal: string;
    price: number;
    estimatedDays: number;
  }): Promise<Bid> => {
    const response = await api.post(`/recruitments/${recruitmentId}/bids`, data);
    return response.data;
  },

  saveTaskToMemory: async (taskId: string, data: {
    title: string;
    content: string;
    tags: string[];
    importance: number;
  }): Promise<MemoryItem> => {
    const response = await api.post(`/tasks/${taskId}/to-memory`, data);
    return response.data;
  },

  distributeTask: async (taskId: string, endpoints: string[]): Promise<DistributionResult> => {
    const response = await api.post(`/tasks/${taskId}/distribute`, { endpoints });
    return response.data;
  },

  getSkillTalents: async (skillId: string): Promise<RecommendedTalent[]> => {
    const response = await api.get(`/skills/${skillId}/talents`);
    return response.data.talents;
  },

  inviteTalent: async (talentId: string, teamId: string, message?: string): Promise<{ success: boolean; invitationId: string }> => {
    const response = await api.post(`/talents/${talentId}/invite`, { teamId, message });
    return response.data;
  },

  getTeamRecommendedTasks: async (teamId: string): Promise<Array<{
    id: string;
    title: string;
    description: string;
    matchScore: number;
    requiredSkills: string[];
  }>> => {
    const response = await api.get(`/teams/${teamId}/recommended-tasks`);
    return response.data.tasks;
  },
};

export default relationApi;
