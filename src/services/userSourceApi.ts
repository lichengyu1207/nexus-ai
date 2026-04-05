import api from './api';

export type UserSourceType = 
  | 'founder_ip'
  | 'casual'
  | 'seo'
  | 'urgent'
  | 'referral'
  | 'direct';

export interface SourceInfo {
  source: UserSourceType;
  name: string;
  welcome_message: string;
  free_integral: number;
  bonus_label: string | null;
  mascot_emotion: string;
  mascot_message: string;
}

export const userSourceApi = {
  getSourceInfo: async (): Promise<SourceInfo> => {
    const response = await api.get<SourceInfo>('/user/source');
    return response.data;
  },

  previewSource: async (source: UserSourceType): Promise<{ source: string; config: Record<string, unknown> }> => {
    const response = await api.get('/user/source/preview', { params: { source } });
    return response.data;
  },

  detectSource: async (params: { source?: string; ref?: string; utm_source?: string }): Promise<{ detected_source: string; config: Record<string, unknown> }> => {
    const response = await api.get('/user/source/detect', { params });
    return response.data;
  },
};

export default userSourceApi;
