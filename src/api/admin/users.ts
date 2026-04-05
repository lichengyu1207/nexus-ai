import api from '@/services/api';

export interface AdminUser {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: string;
  is_admin: boolean;
  is_active: boolean;
  permissions: Record<string, boolean> | null;
  created_at: string | null;
  updated_at: string | null;
  last_login: string | null;
}

export interface AdminUserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminUserCreate {
  email: string;
  password?: string;
  full_name?: string;
  role?: string;
  send_invite?: boolean;
}

export interface AdminUserUpdate {
  email?: string;
  full_name?: string;
  role?: string;
  is_active?: boolean;
  permissions?: Record<string, boolean>;
}

export interface UserListParams {
  search?: string;
  role?: string;
  is_active?: boolean;
  is_admin?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}

export const adminUsersApi = {
  list: async (params: UserListParams): Promise<AdminUserListResponse> => {
    const response = await api.get('/admin/users', { params });
    return response.data;
  },

  get: async (userId: string): Promise<AdminUser> => {
    const response = await api.get(`/admin/users/${userId}`);
    return response.data;
  },

  create: async (data: AdminUserCreate): Promise<AdminUser> => {
    const response = await api.post('/admin/users', data);
    return response.data;
  },

  update: async (userId: string, data: AdminUserUpdate): Promise<AdminUser> => {
    const response = await api.put(`/admin/users/${userId}`, data);
    return response.data;
  },

  delete: async (userId: string, hardDelete: boolean = false): Promise<void> => {
    await api.delete(`/admin/users/${userId}?hard_delete=${hardDelete}`);
  },

  resetPassword: async (userId: string, sendEmail: boolean = false): Promise<{ message: string; new_password?: string }> => {
    const response = await api.post(`/admin/users/${userId}/reset-password?send_email=${sendEmail}`);
    return response.data;
  },

  updateRole: async (userId: string, role: string): Promise<{ message: string }> => {
    const response = await api.put(`/admin/users/${userId}/role`, { role });
    return response.data;
  },

  updateStatus: async (userId: string, isActive: boolean): Promise<{ message: string }> => {
    const response = await api.put(`/admin/users/${userId}/status`, { is_active: isActive });
    return response.data;
  },

  getActivity: async (userId: string): Promise<{ user_id: string; email: string; activity: any[] }> => {
    const response = await api.get(`/admin/users/${userId}/activity`);
    return response.data;
  },
};
