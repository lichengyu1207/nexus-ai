import api from '../services/api';

export interface AISafetyStatus {
  is_active: boolean;
  total_checks: number;
  issues_found: number;
  issues_resolved: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface SafetyCheck {
  id: string;
  check_type: 'bias' | 'toxicity' | 'privacy' | 'security' | 'compliance';
  target: string;
  status: 'pending' | 'running' | 'passed' | 'failed';
  score: number;
  issues: SafetyIssue[];
  created_at: string;
  completed_at?: string;
}

export interface SafetyIssue {
  id: string;
  check_id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  description: string;
  recommendation: string;
  status: 'open' | 'acknowledged' | 'resolved' | 'ignored';
}

export const aiSafetyApi = {
  async getStatus(): Promise<AISafetyStatus> {
    const response = await api.get('/ai-safety/status');
    return response.data;
  },

  async getChecks(status?: string): Promise<{ checks: SafetyCheck[]; total: number }> {
    const response = await api.get('/ai-safety/checks', { params: { status } });
    return response.data;
  },

  async runCheck(request: {
    check_type: string;
    target: string;
    config?: Record<string, unknown>;
  }): Promise<{ success: boolean; check: SafetyCheck }> {
    const response = await api.post('/ai-safety/checks', { json: request });
    return response.data;
  },

  async getIssues(severity?: string): Promise<{ issues: SafetyIssue[]; total: number }> {
    const response = await api.get('/ai-safety/issues', { params: { severity } });
    return response.data;
  },

  async resolveIssue(issueId: string, resolution: string): Promise<{ success: boolean }> {
    const response = await api.post(`/ai-safety/issues/${issueId}/resolve`, {
      json: { resolution },
    });
    return response.data;
  },

  async getStatistics(): Promise<{
    total_checks: number;
    passed_checks: number;
    failed_checks: number;
    open_issues: number;
    by_category: Record<string, number>;
  }> {
    const response = await api.get('/ai-safety/statistics');
    return response.data;
  },
};

export default aiSafetyApi;
