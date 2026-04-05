import api from '@/services/api';

export type ReportType = 'report' | 'comment' | 'user';

export interface Report {
  id: string;
  reporter_id: string;
  reported_type: ReportType;
  reported_id: string;
  reason: string;
  details: string | null;
  evidence: string[];
  status: string;
  admin_notes: string | null;
  action_taken: string | null;
  created_at: string;
  processed_at: string | null;
}

export interface ReportCreateParams {
  reported_type: ReportType;
  reported_id: string;
  reason: string;
  details?: string;
  evidence?: string[];
}

export interface ReportListResponse {
  items: Report[];
  total: number;
}

export const reportReasons = {
  inappropriate: '不当内容',
  spam: '垃圾广告',
  fraud: '涉嫌欺诈',
  copyright: '版权问题',
  privacy: '隐私侵犯',
  attack: '人身攻击',
  misinformation: '虚假信息',
  other: '其他原因',
};

export const reportTypeLabels = {
  report: '分析报告',
  comment: '评论',
  user: '用户',
};

export const reportStatus = {
  pending: { label: '待处理', color: 'bg-yellow-100 text-yellow-700' },
  investigating: { label: '调查中', color: 'bg-blue-100 text-blue-700' },
  resolved: { label: '已解决', color: 'bg-green-100 text-green-700' },
  dismissed: { label: '已驳回', color: 'bg-gray-100 text-gray-700' },
};

export const submitReport = async (data: ReportCreateParams): Promise<Report> => {
  const response = await api.post('reports', data);
  return response.data.data;
};

export const getMyReports = async (limit: number = 20): Promise<ReportListResponse> => {
  const response = await api.get(`/api/reports/my?limit=${limit}`);
  return response.data;
};

export const getReportDetail = async (reportId: string): Promise<Report> => {
  const response = await api.get(`/api/reports/${reportId}`);
  return response.data;
};

export const getReportReasons = async (): Promise<Record<string, string>> => {
  const response = await api.get('reports/reasons');
  return response.data.reasons;
};

export const checkHasReported = async (
  reportedType: ReportType,
  reportedId: string
): Promise<boolean> => {
  try {
    const reports = await getMyReports(100);
    return reports.items.some(
      (r) => r.reported_type === reportedType && r.reported_id === reportedId
    );
  } catch {
    return false;
  }
};
