import api, { handleApiError } from './api';

export interface Report {
  id: string;
  task_id: string;
  user_id: string;
  status: 'pending' | 'generating' | 'completed' | 'failed' | 'archived';
  content: ReportContent | null;
  summary: string | null;
  version: number;
  progress: number;
  current_section: string | null;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
  completed_at: string | null;
}

export interface ReportContent {
  task_id: string;
  style: string;
  generated_at: string;
  sections: {
    summary?: SummarySection;
    key_findings?: KeyFinding[];
    detailed_analysis?: DetailedAnalysis;
    investment_advice?: InvestmentAdvice;
    risk_warning?: string[];
    data_sources?: DataSource[];
  };
  charts?: ChartData[];
}

export interface ChartData {
  id: string;
  type: 'line' | 'bar' | 'pie';
  title: string;
  section: string;
  config: Record<string, unknown>;
  data: Record<string, unknown>[];
}

export interface SummarySection {
  text: string;
  confidence: number;
  generated_by: string;
}

export interface KeyFinding {
  title: string;
  description: string;
  confidence: number;
  source: string;
}

export interface DetailedAnalysis {
  market_analysis?: {
    supply_demand: string;
    liquidity: string;
    market_sentiment: string;
  };
  price_analysis?: {
    current_level: string;
    historical_trend: string;
    future_outlook: string;
  };
  location_analysis?: {
    transportation: string;
    education: string;
    medical: string;
    commercial: string;
  };
}

export interface InvestmentAdvice {
  overall_rating: string;
  investment_horizon?: {
    short_term: string;
    medium_term: string;
    long_term: string;
  };
  action_recommendation: string;
  key_factors?: string[];
  style_specific_advice?: {
    risk_level: string;
    suggestion: string;
  };
}

export interface DataSource {
  name: string;
  type: string;
  description: string;
  reliability: string;
}

export interface ReportChunk {
  task_id: string;
  report_id: string;
  section: string;
  content: unknown;
  progress: number;
  timestamp: string;
}

export interface ReportInteraction {
  id: string;
  report_id: string;
  user_id: string;
  interaction_type: 'like' | 'bookmark' | 'share' | 'comment';
  content: string | null;
  email: string;
  full_name: string | null;
  created_at: string;
}

export const reportApi = {
  getByTask: async (taskId: string): Promise<Report> => {
    const response = await api.get<Report>(`/reports/task/${taskId}`);
    return response.data;
  },

  getById: async (reportId: string): Promise<Report> => {
    const response = await api.get<Report>(`/reports/${reportId}`);
    return response.data;
  },

  list: async (params?: {
    q?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ reports: Report[]; total: number }> => {
    const response = await api.get<{ reports: Report[]; total: number }>('/reports', {
      params,
    });
    return response.data;
  },

  streamReport: (
    taskId: string,
    onChunk: (chunk: ReportChunk) => void,
    onComplete: (report: ReportContent) => void,
    onError: (error: string) => void,
    onConnected?: () => void
  ): EventSource => {
    const token = localStorage.getItem('token');
    const url = new URL(`/api/reports/${taskId}/stream`, window.location.origin);
    
    const eventSource = new EventSource(url.toString(), {
      withCredentials: true,
    });

    eventSource.onopen = () => {
      onConnected?.();
    };

    eventSource.addEventListener('connected', (event) => {
      console.log('SSE connected:', event.data);
    });

    eventSource.addEventListener('report_chunk', (event) => {
      try {
        const data = JSON.parse(event.data) as ReportChunk;
        onChunk(data);
      } catch (e) {
        console.error('Failed to parse report_chunk:', e);
      }
    });

    eventSource.addEventListener('report_complete', (event) => {
      try {
        const data = JSON.parse(event.data);
        onComplete(data.content as ReportContent);
        eventSource.close();
      } catch (e) {
        console.error('Failed to parse report_complete:', e);
      }
    });

    eventSource.addEventListener('report_error', (event) => {
      try {
        const data = JSON.parse(event.data);
        onError(data.error);
        eventSource.close();
      } catch (e) {
        onError('报告生成失败');
        eventSource.close();
      }
    });

    eventSource.addEventListener('heartbeat', () => {
      // Heartbeat received, connection is alive
    });

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      if (eventSource.readyState === EventSource.CLOSED) {
        onError('连接已关闭');
      }
    };

    return eventSource;
  },

  retry: async (reportId: string): Promise<void> => {
    await api.post(`/reports/${reportId}/retry`);
  },

  archive: async (reportId: string): Promise<void> => {
    await api.post(`/reports/${reportId}/archive`);
  },

  addInteraction: async (reportId: string, type: string, content?: string): Promise<void> => {
    await api.post(`/reports/${reportId}/interactions`, {
      interaction_type: type,
      content,
    });
  },

  removeInteraction: async (reportId: string, type: string): Promise<void> => {
    await api.delete(`/reports/${reportId}/interactions/${type}`);
  },

  getInteractions: async (
    reportId: string,
    type?: string
  ): Promise<{
    interactions: ReportInteraction[];
    counts: Record<string, number>;
    user_interactions: Record<string, boolean>;
  }> => {
    const response = await api.get(`/reports/${reportId}/interactions`, {
      params: { interaction_type: type },
    });
    return response.data;
  },

  getVersions: async (reportId: string): Promise<{ versions: Array<{ version: number; change_summary: string; created_at: string }> }> => {
    const response = await api.get(`/reports/${reportId}/versions`);
    return response.data;
  },

  getVersion: async (reportId: string, version: number): Promise<{ version: number; content: ReportContent }> => {
    const response = await api.get(`/reports/${reportId}/versions/${version}`);
    return response.data;
  },

  getTaskVersions: async (taskId: string): Promise<{ versions: Array<{ id: string; version: number; status: string; summary: string | null; created_at: string | null; completed_at: string | null; parent_version_id: string | null }>; task_id: string }> => {
    const response = await api.get(`/reports/task/${taskId}/versions`);
    return response.data;
  },

  compareVersions: async (reportId: string, compareVersion: number): Promise<{
    current_version: number;
    compare_version: number;
    current_content: ReportContent;
    compare_content: ReportContent;
    diff: {
      sections: Record<string, { status: string; current: unknown; compare: unknown }>;
      summary: { status: string; current: unknown; compare: unknown } | null;
      added: string[];
      removed: string[];
      modified: string[];
    };
  }> => {
    const response = await api.get(`/reports/${reportId}/compare/${compareVersion}`);
    return response.data;
  },
};

export { handleApiError };
