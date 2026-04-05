import api from '../services/api';

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
  entities?: Record<string, any>;
  created_at: string;
}

export interface Session {
  id: string;
  user_id: string;
  title: string;
  status: string;
  last_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Profile {
  id: string;
  user_id: string;
  age?: number;
  gender?: string;
  occupation?: string;
  monthly_income?: number;
  annual_income?: number;
  family_structure?: string;
  has_children?: boolean;
  children_ages?: number[];
  current_city?: string;
  current_district?: string;
  work_city?: string;
  work_district?: string;
  commute_preference?: string;
  house_type_preference?: string;
  budget_min?: number;
  budget_max?: number;
  down_payment?: number;
  loan_need?: boolean;
  credit_score?: number;
}

export interface ConsultResponse {
  reply: string;
  session_id: string;
  action: 'ask_more' | 'done' | 'show_report';
  intent?: string;
  entities?: Record<string, any>;
}

export const consultApi = {
  async sendMessage(message: string, sessionId?: string): Promise<ConsultResponse> {
    const response = await api.post('/consult', {
      message,
      session_id: sessionId,
    });
    return response.data;
  },

  async getSessions(limit: number = 20): Promise<{ sessions: Session[]; total: number }> {
    const response = await api.get(`/consult/sessions?limit=${limit}`);
    return response.data;
  },

  async createSession(title?: string): Promise<Session> {
    const response = await api.post('/consult/sessions', { title });
    return response.data;
  },

  async getSessionDetail(sessionId: string): Promise<{ session: Session; history: Message[] }> {
    const response = await api.get(`/consult/sessions/${sessionId}`);
    return response.data;
  },

  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/consult/sessions/${sessionId}`);
  },

  async getProfile(): Promise<{ profile: Profile | null }> {
    const response = await api.get('/consult/profile');
    return response.data;
  },

  async updateProfile(data: Partial<Profile>): Promise<{ profile: Profile; message: string }> {
    const response = await api.put('/consult/profile', data);
    return response.data;
  },

  async generateReport(sessionId: string): Promise<{ report_id: string; message: string }> {
    const response = await api.post(`/consult/sessions/${sessionId}/report`);
    return response.data;
  },

  async getReports(limit: number = 20): Promise<{ reports: any[]; total: number }> {
    const response = await api.get(`/consult/reports?limit=${limit}`);
    return response.data;
  },

  async getReport(reportId: string): Promise<any> {
    const response = await api.get(`/consult/reports/${reportId}`);
    return response.data;
  },

  async getQuickQuestions(): Promise<{ questions: string[] }> {
    const response = await api.get('/consult/quick-questions');
    return response.data;
  },

  async getIntegral(): Promise<{ integral: number; membership_level: string; membership_expires: string | null; is_member: boolean }> {
    const response = await api.get('/consult/integral');
    return response.data;
  },
};

export default consultApi;
