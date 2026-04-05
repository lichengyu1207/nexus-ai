import React, { useState, useEffect } from 'react';
import {
  ExclamationTriangleIcon,
  FunnelIcon,
  EyeIcon,
  XMarkIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface Report {
  id: string;
  reporter_id: string;
  reported_type: string;
  reported_id: string;
  reason: string;
  details: string;
  status: string;
  admin_notes: string;
  action_taken: string;
  created_at: string;
  reporter_email: string;
  reporter_name: string;
}

const REPORT_STATUS: Record<string, { label: string; color: string }> = {
  pending: { label: '待处理', color: 'bg-yellow-100 text-yellow-700' },
  investigating: { label: '调查中', color: 'bg-blue-100 text-blue-700' },
  resolved: { label: '已解决', color: 'bg-green-100 text-green-700' },
  dismissed: { label: '已驳回', color: 'bg-gray-100 text-gray-700' },
};

const REPORT_REASONS: Record<string, string> = {
  inappropriate: '不当内容',
  spam: '垃圾广告',
  fraud: '涉嫌欺诈',
  copyright: '版权问题',
  privacy: '隐私侵犯',
  attack: '人身攻击',
  misinformation: '虚假信息',
  other: '其他原因',
};

const TYPE_LABELS: Record<string, string> = {
  report: '分析报告',
  comment: '评论',
  user: '用户',
};

const ReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [newStatus, setNewStatus] = useState('');
  const [adminNotes, setAdminNotes] = useState('');
  const [actionTaken, setActionTaken] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchReports();
    fetchStats();
  }, [statusFilter, typeFilter]);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (typeFilter) params.append('reported_type', typeFilter);
      const response = await api.get(`/admin/reports?${params}`);
      setReports(response.data.items || []);
    } catch (error) {
      showToast.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/reports/stats');
      setStats(response.data || {});
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleProcess = async () => {
    if (!selectedReport) return;

    setProcessing(true);
    try {
      await api.put(`/admin/reports/${selectedReport.id}`, {
        status: newStatus || selectedReport.status,
        admin_notes: adminNotes || undefined,
        action_taken: actionTaken || undefined,
      });
      showToast.success('处理成功');
      setSelectedReport(null);
      setAdminNotes('');
      setActionTaken('');
      fetchReports();
      fetchStats();
    } catch (error) {
      showToast.error('处理失败');
    } finally {
      setProcessing(false);
    }
  };

  const viewContent = (report: Report) => {
    if (report.reported_type === 'report') {
      navigate(`/reports/${report.reported_id}`);
    } else if (report.reported_type === 'comment') {
      showToast.info('评论查看功能开发中');
    } else if (report.reported_type === 'user') {
      showToast.info('用户查看功能开发中');
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">举报管理</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">总数</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">待处理</p>
          <p className="text-2xl font-bold text-yellow-600">{stats.pending || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">调查中</p>
          <p className="text-2xl font-bold text-blue-600">{stats.by_status?.investigating || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">已解决</p>
          <p className="text-2xl font-bold text-green-600">{stats.by_status?.resolved || 0}</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <FunnelIcon className="w-5 h-5 text-gray-400" />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
        >
          <option value="">全部状态</option>
          {Object.entries(REPORT_STATUS).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
        >
          <option value="">全部类型</option>
          {Object.entries(TYPE_LABELS).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : reports.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无举报记录</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left font-medium">举报人</th>
                <th className="px-4 py-3 text-left font-medium">类型</th>
                <th className="px-4 py-3 text-left font-medium">原因</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-left font-medium">时间</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3">{report.reporter_name || report.reporter_email}</td>
                  <td className="px-4 py-3">{TYPE_LABELS[report.reported_type] || report.reported_type}</td>
                  <td className="px-4 py-3">{REPORT_REASONS[report.reason] || report.reason}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${REPORT_STATUS[report.status]?.color}`}>
                      {REPORT_STATUS[report.status]?.label || report.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">{formatDate(report.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => { setSelectedReport(report); setNewStatus(report.status); }}
                      className="text-primary-600 hover:text-primary-700 mr-2"
                    >
                      处理
                    </button>
                    <button
                      onClick={() => viewContent(report)}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      <EyeIcon className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/30" onClick={() => setSelectedReport(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">举报详情</h3>
              <button onClick={() => setSelectedReport(null)} className="p-1 hover:bg-gray-100 rounded">
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">举报人</p>
                  <p className="font-medium">{selectedReport.reporter_name || selectedReport.reporter_email}</p>
                </div>
                <div>
                  <p className="text-gray-500">举报时间</p>
                  <p className="font-medium">{formatDate(selectedReport.created_at)}</p>
                </div>
              </div>

              <div>
                <p className="text-gray-500 text-sm">被举报内容</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-medium">{TYPE_LABELS[selectedReport.reported_type]}</span>
                  <button
                    onClick={() => viewContent(selectedReport)}
                    className="text-primary-600 text-sm flex items-center gap-1"
                  >
                    查看内容 <ArrowTopRightOnSquareIcon className="w-3 h-3" />
                  </button>
                </div>
              </div>

              <div>
                <p className="text-gray-500 text-sm">举报原因</p>
                <p className="font-medium">{REPORT_REASONS[selectedReport.reason] || selectedReport.reason}</p>
              </div>

              {selectedReport.details && (
                <div>
                  <p className="text-gray-500 text-sm">补充说明</p>
                  <p className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">{selectedReport.details}</p>
                </div>
              )}

              <div>
                <p className="text-gray-500 text-sm mb-1">更新状态</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(REPORT_STATUS).map(([key, { label, color }]) => (
                    <button
                      key={key}
                      onClick={() => setNewStatus(key)}
                      className={`px-3 py-1.5 rounded text-sm ${
                        newStatus === key ? `${color} ring-2 ring-offset-1` : 'bg-gray-100 dark:bg-gray-700'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-gray-500 text-sm mb-1">处理备注</p>
                <textarea
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 resize-none"
                  rows={3}
                />
              </div>

              <div>
                <p className="text-gray-500 text-sm mb-1">采取措施</p>
                <select
                  value={actionTaken}
                  onChange={(e) => setActionTaken(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                >
                  <option value="">选择措施</option>
                  <option value="warning">警告用户</option>
                  <option value="content_removed">删除内容</option>
                  <option value="no_action">无需处理</option>
                  <option value="other">其他</option>
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setSelectedReport(null)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={handleProcess}
                disabled={processing}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                {processing ? '处理中...' : '提交'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsPage;
