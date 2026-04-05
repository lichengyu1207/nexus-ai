import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChatBubbleLeftRightIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  EyeIcon,
  CheckCircleIcon,
  ClockIcon,
  FunnelIcon,
  ArrowTopRightOnSquareIcon,
  MapPinIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { HandThumbUpIcon as HandThumbUpSolidIcon, HandThumbDownIcon as HandThumbDownSolidIcon } from '@heroicons/react/24/solid';
import api from '@/services/api';
import showToast from '@/utils/toast';
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface Feedback {
  id: string;
  report_id: string;
  user_id: string;
  rating: number;
  issues: string[];
  comment: string;
  contact_allowed: boolean;
  status: string;
  admin_notes: string;
  created_at: string;
  processed_at: string;
  task_id: string;
  summary: string;
  email: string;
  full_name: string;
  city?: string;
  district?: string;
  community?: string;
}

interface FeedbackStats {
  total: number;
  avg_rating: number;
  by_rating: Record<string, number>;
  by_status: Record<string, number>;
  by_issue: Record<string, number>;
  recent_week: number;
}

interface TrendData {
  date: string;
  total: number;
  positive: number;
  negative: number;
}

interface RegionData {
  city: string;
  district: string;
  feedback_count: number;
  avg_rating: number;
  negative_count: number;
}

const ISSUE_LABELS: Record<string, string> = {
  price_accuracy: '价格准确性',
  area_estimate: '面积估算',
  location_info: '周边配套信息',
  market_analysis: '市场分析',
  investment_advice: '投资建议',
  data_completeness: '数据完整性',
  other: '其他问题',
};

const ISSUE_COLORS: Record<string, string> = {
  price_accuracy: '#ef4444',
  area_estimate: '#f97316',
  location_info: '#eab308',
  market_analysis: '#22c55e',
  investment_advice: '#3b82f6',
  data_completeness: '#8b5cf6',
  other: '#6b7280',
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: '待处理', color: 'bg-yellow-100 text-yellow-700' },
  processing: { label: '处理中', color: 'bg-blue-100 text-blue-700' },
  resolved: { label: '已解决', color: 'bg-green-100 text-green-700' },
  rejected: { label: '已拒绝', color: 'bg-gray-100 text-gray-700' },
};

const FeedbackPage: React.FC = () => {
  const navigate = useNavigate();
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [trend, setTrend] = useState<TrendData[]>([]);
  const [regions, setRegions] = useState<RegionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFeedback, setSelectedFeedback] = useState<Feedback | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [ratingFilter, setRatingFilter] = useState<string>('');
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [activeTab, setActiveTab] = useState<'list' | 'trend' | 'region'>('list');
  const limit = 20;

  useEffect(() => {
    fetchFeedbacks();
    fetchStats();
    fetchTrend();
    fetchRegions();
  }, [statusFilter, ratingFilter, page]);

  const fetchFeedbacks = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (ratingFilter) params.append('rating', ratingFilter);
      params.append('limit', String(limit));
      params.append('offset', String(page * limit));

      const response = await api.get(`/admin/feedback?${params}`);
      setFeedbacks(response.data.items || response.data.feedbacks || []);
      setTotal(response.data.total);
    } catch (error) {
      showToast.error('获取反馈列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/admin/feedback/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchTrend = async () => {
    try {
      const response = await api.get('/admin/feedback/trend?days=30');
      setTrend(response.data.trend);
    } catch (error) {
      console.error('Failed to fetch trend:', error);
    }
  };

  const fetchRegions = async () => {
    try {
      const response = await api.get('/admin/feedback/by-region?limit=20');
      setRegions(response.data.regions);
    } catch (error) {
      console.error('Failed to fetch regions:', error);
    }
  };

  const handleStatusUpdate = async (feedbackId: string, newStatus: string, adminNotes?: string) => {
    try {
      await api.patch(`/admin/feedback/${feedbackId}/status`, {
        status: newStatus,
        admin_reply: adminNotes,
      });
      showToast.success('状态已更新');
      fetchFeedbacks();
      fetchStats();
      if (selectedFeedback?.id === feedbackId) {
        setSelectedFeedback({ ...selectedFeedback, status: newStatus, admin_notes: adminNotes || '' });
      }
    } catch (error) {
      showToast.error('更新失败');
    }
  };

  const handleViewReport = (taskId: string) => {
    navigate(`/tasks/${taskId}/report`);
    setSelectedFeedback(null);
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const formatShortDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  const totalPages = Math.ceil(total / limit);

  const maxTrendTotal = Math.max(...trend.map(t => t.total), 1);
  const maxIssueCount = stats && stats.by_issue ? Math.max(...Object.values(stats.by_issue), 1) : 1;
  const maxRegionCount = regions.length > 0 ? Math.max(...regions.map(r => r.feedback_count || r.count || 0), 1) : 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">反馈分析</h1>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">总反馈数</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
              </div>
              <ChatBubbleLeftRightIcon className="w-8 h-8 text-primary-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">满意度</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.total > 0 ? `${((stats.by_rating['2'] || 0) / stats.total * 100).toFixed(0)}%` : '-'}
                </p>
              </div>
              <HandThumbUpIcon className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">本周新增</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.recent_week}</p>
              </div>
              <ClockIcon className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">待处理</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.by_status.pending || 0}
                </p>
              </div>
              <ExclamationTriangleIcon className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <ChartBarIcon className="w-4 h-4" />
            问题类型分布
          </h3>
          {stats && stats.by_issue && Object.keys(stats.by_issue).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(stats.by_issue)
                .sort(([, a], [, b]) => b - a)
                .map(([issue, count]) => (
                  <div key={issue} className="flex items-center gap-3">
                    <span className="w-24 text-sm text-gray-600 dark:text-gray-400 truncate">
                      {ISSUE_LABELS[issue] || issue}
                    </span>
                    <div className="flex-1 h-6 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${(count / maxIssueCount) * 100}%`,
                          backgroundColor: ISSUE_COLORS[issue] || '#6b7280'
                        }}
                      />
                    </div>
                    <span className="w-8 text-sm font-medium text-gray-900 dark:text-white text-right">
                      {count}
                    </span>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">暂无数据</p>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <ClockIcon className="w-4 h-4" />
            反馈趋势（近30天）
          </h3>
          {trend.length > 0 ? (
            <div className="h-40 flex items-end gap-1">
              {trend.slice(-14).map((item, index) => (
                <div key={index} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full flex flex-col gap-0.5">
                    <div
                      className="w-full bg-green-500 rounded-t transition-all duration-300"
                      style={{ height: `${(item.positive / maxTrendTotal) * 80}px` }}
                      title={`满意: ${item.positive}`}
                    />
                    <div
                      className="w-full bg-red-500 rounded-b transition-all duration-300"
                      style={{ height: `${(item.negative / maxTrendTotal) * 80}px` }}
                      title={`不满意: ${item.negative}`}
                    />
                  </div>
                  <span className="text-xs text-gray-400 transform -rotate-45 origin-left">
                    {formatShortDate(item.date)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">暂无数据</p>
          )}
          <div className="flex items-center justify-center gap-4 mt-4 text-xs">
            <div className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-green-500" />
              <span className="text-gray-500">满意</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="w-3 h-3 rounded bg-red-500" />
              <span className="text-gray-500">不满意</span>
            </div>
          </div>
        </div>
      </div>

      {regions.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <MapPinIcon className="w-4 h-4" />
            区域反馈热度（问题最多区域）
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                  <th className="pb-2 font-medium">城市</th>
                  <th className="pb-2 font-medium">区域</th>
                  <th className="pb-2 font-medium text-center">反馈数</th>
                  <th className="pb-2 font-medium text-center">不满意数</th>
                  <th className="pb-2 font-medium text-center">满意度</th>
                  <th className="pb-2 font-medium">热度</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {regions.map((region, index) => (
                  <tr key={index} className="text-gray-700 dark:text-gray-300">
                    <td className="py-2">{region.city || '-'}</td>
                    <td className="py-2">{region.district || '-'}</td>
                    <td className="py-2 text-center">{region.feedback_count}</td>
                    <td className="py-2 text-center">
                      <span className={region.negative_count > 0 ? 'text-red-600 font-medium' : ''}>
                        {region.negative_count}
                      </span>
                    </td>
                    <td className="py-2 text-center">
                      {region.avg_rating ? `${((region.avg_rating / 2) * 100).toFixed(0)}%` : '-'}
                    </td>
                    <td className="py-2">
                      <div className="w-24 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            region.negative_count > 3 ? 'bg-red-500' :
                            region.negative_count > 0 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${(region.feedback_count / maxRegionCount) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <FunnelIcon className="w-5 h-5 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
                className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
              >
                <option value="">全部状态</option>
                {Object.entries(STATUS_LABELS).map(([key, { label }]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={ratingFilter}
                onChange={(e) => { setRatingFilter(e.target.value); setPage(0); }}
                className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
              >
                <option value="">全部评分</option>
                <option value="2">满意 👍</option>
                <option value="1">不满意 👎</option>
              </select>
            </div>

            <div className="ml-auto text-sm text-gray-500 dark:text-gray-400">
              共 {total} 条反馈
            </div>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : feedbacks.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无反馈数据</div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {feedbacks.map((feedback) => (
              <div
                key={feedback.id}
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
                onClick={() => setSelectedFeedback(feedback)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {feedback.rating === 2 ? (
                      <HandThumbUpSolidIcon className="w-6 h-6 text-green-500 flex-shrink-0 mt-1" />
                    ) : feedback.rating === 1 ? (
                      <HandThumbDownSolidIcon className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
                    ) : (
                      <div className="w-6 h-6 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                        <span className="text-gray-500 text-xs">-</span>
                      </div>
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {feedback.full_name || feedback.email || '匿名用户'}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs ${STATUS_LABELS[feedback.status]?.color || 'bg-gray-100 text-gray-700'}`}>
                          {STATUS_LABELS[feedback.status]?.label || feedback.status}
                        </span>
                      </div>
                      {feedback.issues && feedback.issues.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {feedback.issues.map((issue) => (
                            <span key={issue} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-600 rounded text-xs text-gray-600 dark:text-gray-300">
                              {ISSUE_LABELS[issue] || issue}
                            </span>
                          ))}
                        </div>
                      )}
                      {feedback.comment && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                          {feedback.comment}
                        </p>
                      )}
                      <div className="flex items-center gap-3 mt-1">
                        <p className="text-xs text-gray-400">
                          {formatDate(feedback.created_at)}
                        </p>
                        {(feedback.city || feedback.district) && (
                          <p className="text-xs text-gray-400 flex items-center gap-1">
                            <MapPinIcon className="w-3 h-3" />
                            {feedback.city}{feedback.district ? ` · ${feedback.district}` : ''}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <EyeIcon className="w-5 h-5 text-gray-400" />
                </div>
              </div>
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-center gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded disabled:opacity-50"
            >
              上一页
            </button>
            <span className="text-sm text-gray-500">
              第 {page + 1} / {totalPages} 页
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        )}
      </div>

      {selectedFeedback && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/30" onClick={() => setSelectedFeedback(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">反馈详情</h3>
              <button
                onClick={() => setSelectedFeedback(null)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="p-4 space-y-4">
              <div className="flex items-center gap-3">
                {selectedFeedback.rating === 2 ? (
                  <HandThumbUpSolidIcon className="w-8 h-8 text-green-500" />
                ) : selectedFeedback.rating === 1 ? (
                  <HandThumbDownSolidIcon className="w-8 h-8 text-red-500" />
                ) : (
                  <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
                    <span className="text-gray-500 text-sm">N/A</span>
                  </div>
                )}
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {selectedFeedback.rating === 2 ? '满意' : selectedFeedback.rating === 1 ? '不满意' : '未评价'}
                  </p>
                  <p className="text-sm text-gray-500">
                    {selectedFeedback.full_name || selectedFeedback.email}
                  </p>
                </div>
              </div>

              {selectedFeedback.issues && selectedFeedback.issues.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">问题类型</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedFeedback.issues.map((issue: string) => (
                      <span key={issue} className="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full text-sm">
                        {ISSUE_LABELS[issue] || issue}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedFeedback.comment && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">详细说明</p>
                  <p className="text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                    {selectedFeedback.comment}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">提交时间</p>
                  <p className="text-gray-900 dark:text-white">{formatDate(selectedFeedback.created_at)}</p>
                </div>
                <div>
                  <p className="text-gray-500">允许联系</p>
                  <p className="text-gray-900 dark:text-white">
                    {selectedFeedback.contact_allowed ? '是' : '否'}
                  </p>
                </div>
              </div>

              {(selectedFeedback.city || selectedFeedback.district) && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">位置信息</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                    <MapPinIcon className="w-4 h-4" />
                    {selectedFeedback.city}
                    {selectedFeedback.district && ` · ${selectedFeedback.district}`}
                    {selectedFeedback.community && ` · ${selectedFeedback.community}`}
                  </p>
                </div>
              )}

              {selectedFeedback.summary && (
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">报告摘要</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                    {selectedFeedback.summary}
                  </p>
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">更新状态</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(STATUS_LABELS).map(([key, { label, color }]) => (
                    <button
                      key={key}
                      onClick={() => selectedFeedback && handleStatusUpdate(selectedFeedback.id, key)}
                      disabled={selectedFeedback?.status === key}
                      className={`px-3 py-1.5 rounded text-sm ${
                        selectedFeedback?.status === key
                          ? `${color} ring-2 ring-offset-1`
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {selectedFeedback?.task_id && (
                <button
                  onClick={() => selectedFeedback?.task_id && handleViewReport(selectedFeedback.task_id)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                  查看对应报告
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeedbackPage;
