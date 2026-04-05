import api from '@/services/api';

export interface OverviewStats {
  total_users: number;
  active_users: number;
  new_users_today: number;
  new_users_week: number;
  total_tasks: number;
  completed_tasks: number;
  running_tasks: number;
  failed_tasks: number;
  total_reports: number;
  total_teams: number;
  total_comments: number;
  completion_rate: number;
}

export interface UserGrowthItem {
  period: string;
  new_users: number;
}

export interface TaskStatsByPeriod {
  period: string;
  total: number;
  completed: number;
  failed: number;
}

export interface TaskStats {
  by_status: Record<string, number>;
  by_period: TaskStatsByPeriod[];
  by_style: Record<string, number>;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  uptime_seconds: number | null;
  cpu: {
    percent?: number;
    count?: number;
    load_avg?: number[] | null;
    error?: string;
  };
  memory: {
    total_mb?: number;
    available_mb?: number;
    used_mb?: number;
    percent?: number;
    error?: string;
  };
  disk: {
    total_gb?: number;
    used_gb?: number;
    free_gb?: number;
    percent?: number;
    error?: string;
  };
  database: {
    status?: string;
    response_time_ms?: number;
    size_mb?: number;
    error?: string;
  };
  process: {
    pid?: number;
    memory_mb?: number;
    cpu_percent?: number;
    threads?: number;
    error?: string;
  };
}

export interface ActivityStats {
  period_days: number;
  daily_activity: Array<{
    date: string;
    new_users: number;
    new_tasks: number;
    new_reports: number;
    new_comments: number;
  }>;
}

export const adminStatsApi = {
  getOverview: async (): Promise<OverviewStats> => {
    const response = await api.get('/admin/stats/overview');
    return response.data;
  },

  getUserGrowth: async (params?: {
    start_date?: string;
    end_date?: string;
    granularity?: 'day' | 'month';
  }): Promise<UserGrowthItem[]> => {
    const response = await api.get('/admin/stats/users', { params });
    return response.data;
  },

  getTaskStats: async (params?: {
    start_date?: string;
    end_date?: string;
    granularity?: 'day' | 'month';
  }): Promise<TaskStats> => {
    const response = await api.get('/admin/stats/tasks', { params });
    return response.data;
  },

  getSystemHealth: async (): Promise<SystemHealth> => {
    const response = await api.get('/admin/stats/system');
    return response.data;
  },

  getActivity: async (days: number = 7): Promise<ActivityStats> => {
    const response = await api.get(`/admin/stats/activity?days=${days}`);
    return response.data;
  },

  getDashboard: async (): Promise<{
    overview: OverviewStats;
    activity: ActivityStats;
    health: {
      status: string;
      cpu_percent?: number;
      memory_percent?: number;
      disk_percent?: number;
      database_status?: string;
    };
  }> => {
    const response = await api.get('/admin/stats/dashboard');
    return response.data;
  },

  clearCache: async (): Promise<{ message: string }> => {
    const response = await api.post('/admin/stats/cache/clear');
    return response.data;
  },

  exportCsv: async (type: 'overview' | 'users' | 'tasks'): Promise<Blob> => {
    const response = await api.get(`/admin/stats/export?type=${type}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
