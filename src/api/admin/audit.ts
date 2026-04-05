import api from '@/services/api';

export interface AuditLog {
  id: string;
  timestamp: string | null;
  user_id: string | null;
  username: string | null;
  user_role: string | null;
  ip_address: string | null;
  user_agent: string | null;
  action_type: string;
  resource_type: string | null;
  resource_id: string | null;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  status: string;
  error_message: string | null;
  created_at: string | null;
}

export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  filters_applied: Record<string, unknown>;
}

export interface AuditStats {
  total_logs: number;
  logs_today: number;
  logs_this_week: number;
  logs_this_month: number;
  success_count: number;
  failure_count: number;
  unique_users: number;
  unique_ips: number;
  top_actions: Array<{
    action_type: string;
    label: string;
    count: number;
  }>;
  top_users: Array<{
    user_id: string;
    username: string;
    count: number;
  }>;
  daily_trend: Array<{
    date: string;
    count: number;
    success_count: number;
    failure_count: number;
  }>;
}

export interface Anomaly {
  id: string;
  user_id: string | null;
  username: string | null;
  anomaly_type: string;
  severity: string;
  description: string | null;
  is_resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface VerificationResult {
  status: 'valid' | 'invalid' | 'warning' | 'error';
  summary: {
    total_logs: number;
    verified_logs: number;
    hash_errors: number;
    chain_errors: number;
    signature_errors: number;
  };
  verification_time: string;
  duration_ms: number;
  errors: {
    hash_errors: Array<{ log_id: string; log_index: number; error_type: string; timestamp: string }>;
    chain_errors: Array<{ log_id: string; log_index: number; error_type: string; timestamp: string }>;
    signature_errors: Array<{ batch_id: string; error_type: string }>;
  };
  integrity_score: number;
  recommendations: string[];
}

export interface SignatureBatch {
  id: string;
  start_log_id: string;
  end_log_id: string;
  start_timestamp: string;
  end_timestamp: string;
  log_count: number;
  batch_hash: string;
  signature: string;
  signed_at: string;
  public_key_fingerprint: string;
}

export interface AuditLogFilters {
  start_date?: string;
  end_date?: string;
  user_id?: string;
  action_type?: string;
  resource_type?: string;
  resource_id?: string;
  status?: string;
  ip_address?: string;
  search?: string;
  sort_by?: 'timestamp' | 'user_id' | 'action_type' | 'resource_type' | 'status' | 'ip_address';
  sort_order?: 'asc' | 'desc';
  page?: number;
  per_page?: number;
}

export interface ActionType {
  value: string;
  label: string;
}

export interface ResourceType {
  value: string;
  label: string;
}

export const auditApi = {
  async getLogs(filters: AuditLogFilters = {}): Promise<AuditLogListResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, String(value));
      }
    });
    
    const response = await api.get(`/admin/audit/logs?${params}`);
    return response.data;
  },

  async getLogDetail(logId: string): Promise<AuditLog> {
    const response = await api.get(`/admin/audit/logs/${logId}`);
    return response.data;
  },

  async getStats(days: number = 30): Promise<AuditStats> {
    const response = await api.get(`/admin/audit/stats?days=${days}`);
    return response.data;
  },

  async getAnomalies(): Promise<Anomaly[]> {
    const response = await api.get('/admin/audit/anomalies');
    return response.data;
  },

  async resolveAnomaly(id: string): Promise<void> {
    await api.post(`/admin/audit/anomalies/${id}/resolve`);
  },

  async verifyChain(limit: number = 10000, verifySignatures: boolean = true): Promise<VerificationResult> {
    const response = await api.post('/admin/audit/verify', null, {
      params: { limit, verify_signatures: verifySignatures, save_record: true }
    });
    return response.data;
  },

  async quickVerify(): Promise<{ status: string; total_logs: number; verified_logs: number; has_errors: boolean; integrity_score: number }> {
    const response = await api.get('/admin/audit/verify/quick');
    return response.data;
  },

  async signLogs(batchSize: number = 100): Promise<{ message: string; signed_count: number }> {
    const response = await api.post('/admin/audit/sign', null, {
      params: { batch_size: batchSize }
    });
    return response.data;
  },

  async getSignatureBatches(limit: number = 50, offset: number = 0): Promise<{ batches: SignatureBatch[]; total: number }> {
    const response = await api.get(`/admin/audit/signatures?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  async getVerificationHistory(limit: number = 20, offset: number = 0): Promise<{ records: Array<{
    id: string;
    verification_time: string;
    total_logs: number;
    verified_logs: number;
    hash_errors: number;
    chain_errors: number;
    signature_errors: number;
    status: string;
    integrity_score: number;
    duration_ms: number;
  }>; total: number }> {
    const response = await api.get(`/admin/audit/verifications?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  async getActionTypes(): Promise<{ types: ActionType[] }> {
    const response = await api.get('/admin/audit/action-types');
    return response.data;
  },

  async getResourceTypes(): Promise<{ types: ResourceType[] }> {
    const response = await api.get('/admin/audit/resource-types');
    return response.data;
  },

  async exportLogs(filters: AuditLogFilters = {}, format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, String(value));
      }
    });
    params.append('format', format);
    
    const response = await api.get(`/admin/audit/export?${params}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  async getUserLogs(userId: string, filters: Omit<AuditLogFilters, 'user_id'> = {}): Promise<AuditLogListResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, String(value));
      }
    });
    
    const response = await api.get(`/admin/audit/user/${userId}?${params}`);
    return response.data;
  },

  async getIpLogs(ipAddress: string, filters: Omit<AuditLogFilters, 'ip_address'> = {}): Promise<AuditLogListResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, String(value));
      }
    });
    
    const response = await api.get(`/admin/audit/ip/${encodeURIComponent(ipAddress)}?${params}`);
    return response.data;
  },

  async getResourceLogs(resourceType: string, resourceId: string, filters: Omit<AuditLogFilters, 'resource_type' | 'resource_id'> = {}): Promise<AuditLogListResponse> {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, String(value));
      }
    });
    
    const response = await api.get(`/api/admin/audit/resource/${resourceType}/${resourceId}?${params}`);
    return response.data;
  },

  async cleanupLogs(days: number = 90): Promise<{ message: string; deleted_count: number; cutoff_date: string }> {
    const response = await api.delete(`/api/admin/audit/cleanup?days=${days}`);
    return response.data;
  },
};

export default auditApi;
