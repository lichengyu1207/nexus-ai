import api from '@/services/api';

export interface SettingField {
  key: string;
  value: any;
  type: string;
  description: string;
  group?: string;
  options?: string[];
  min?: number;
  max?: number;
}

export interface GroupedSettings {
  groups: Record<string, Record<string, SettingField>>;
}

export interface SettingUpdateResponse {
  message: string;
  updated: Record<string, boolean>;
  errors?: Record<string, string>;
}

export const adminSettingsApi = {
  getAll: async (): Promise<GroupedSettings> => {
    const response = await api.get('/admin/settings');
    return response.data;
  },

  getGroups: async (): Promise<{ groups: string[] }> => {
    const response = await api.get('/admin/settings/groups');
    return response.data;
  },

  getKeys: async (): Promise<{ keys: string[] }> => {
    const response = await api.get('/admin/settings/keys');
    return response.data;
  },

  getByGroup: async (group: string): Promise<{ group: string; settings: Record<string, SettingField> }> => {
    const response = await api.get(`/admin/settings/group/${group}`);
    return response.data;
  },

  get: async (key: string): Promise<SettingField> => {
    const response = await api.get(`/admin/settings/${key}`);
    return response.data;
  },

  updateAll: async (settings: Record<string, any>): Promise<SettingUpdateResponse> => {
    const response = await api.put('/admin/settings', { settings });
    return response.data;
  },

  update: async (key: string, value: any): Promise<SettingField> => {
    const response = await api.put(`/admin/settings/${key}`, { key, value });
    return response.data;
  },

  reloadCache: async (): Promise<{ message: string }> => {
    const response = await api.post('/admin/settings/reload-cache');
    return response.data;
  },

  checkRegistration: async (): Promise<{ allow_registration: boolean }> => {
    const response = await api.get('/admin/settings/check/registration');
    return response.data;
  },

  checkMaintenance: async (): Promise<{ maintenance_mode: boolean }> => {
    const response = await api.get('/admin/settings/check/maintenance');
    return response.data;
  },

  getPublicInfo: async (): Promise<{ site_name: string; site_description: string; contact_email: string }> => {
    const response = await api.get('/admin/settings/public/info');
    return response.data;
  },
};
