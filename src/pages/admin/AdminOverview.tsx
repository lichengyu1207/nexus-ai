import React, { useState, useEffect } from 'react';
import {
  UsersIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  UserGroupIcon,
  ChatBubbleLeftIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  ArrowRightIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { LoadingCard } from '@/components/Loading';
import ErrorBoundary from '@/components/ErrorBoundary';

interface SystemStats {
  total_users: number;
  admin_users: number;
  active_users: number;
  total_tasks: number;
  completed_tasks: number;
  total_reports: number;
  total_teams: number;
  total_comments: number;
}

interface FeedbackStats {
  total_feedback: number;
  pending_feedback: number;
  avg_response_time: string;
  feedback_by_type: Record<string, number>;
  trend_last_7_days: Array<{ date: string; count: number }>;
}

interface ReportsStats {
  total_reports: number;
  pending_reports: number;
  avg_process_time: string;
  reports_by_type: Record<string, number>;
  trend_last_7_days: Array<{ date: string; count: number }>;
}

const StatCard: React.FC<{
  title: string;
  value: number | string;
  icon: React.FC<{ className?: string }>;
  color: string;
  subtitle?: string;
  onClick?: () => void;
}> = ({ title, value, icon: Icon, color, subtitle, onClick }) => (
  <div 
    className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6 ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
    onClick={onClick}
  >
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
        {subtitle && (
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{subtitle}</p>
        )}
      </div>
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
    </div>
    {onClick && (
      <div className="mt-3 flex items-center text-primary-600 text-sm">
        查看详情 <ArrowRightIcon className="w-4 h-4 ml-1" />
      </div>
    )}
  </div>
);

const TrendChart: React.FC<{
  data: Array<{ date: string; count: number }> | null;
  title: string;
  color: string;
}> = ({ data, title, color }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-40 flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
        暂无数据
      </div>
    );
  }

  const maxCount = Math.max(...data.map(d => d.count), 1);

  return (
    <div className="h-40 flex items-end gap-2">
      {data.map((item, index) => {
        const height = (item.count / maxCount) * 100;
        return (
          <div key={index} className="flex-1 flex flex-col items-center">
            <div
              className={`w-full ${color} rounded-t transition-all`}
              style={{ height: `${height}%`, minHeight: item.count > 0 ? '4px' : '0' }}
            />
            <span className="text-xs text-gray-400 mt-1">
              {new Date(item.date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })}
            </span>
          </div>
        );
      })}
    </div>
  );
};

const AdminOverview: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null);
  const [reportsStats, setReportsStats] = useState<ReportsStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statsRes, feedbackRes, reportsRes] = await Promise.all([
        api.get('/admin/stats/overview'),
        api.get('/admin/stats/feedback').catch(() => ({ data: null })),
        api.get('/admin/stats/reports').catch(() => ({ data: null })),
      ]);
      setStats(statsRes.data);
      setFeedbackStats(feedbackRes.data);
      setReportsStats(reportsRes.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
      setError('加载统计数据失败，请检查后端服务是否正常运行');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  if (isLoading) {
    return <LoadingCard message="加载统计数据..." />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
          <ExclamationTriangleIcon className="w-8 h-8 text-red-600 dark:text-red-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">加载失败</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-4">{error}</p>
        <button
          onClick={loadStats}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <ArrowPathIcon className="w-4 h-4" />
          重新加载
        </button>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">暂无数据</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">系统概览</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">查看系统整体运行状态</p>
        </div>
        <button
          onClick={loadStats}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          <ArrowPathIcon className="w-4 h-4" />
          刷新
        </button>
      </div>

      <ErrorBoundary>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="总用户数"
            value={stats.total_users}
            icon={UsersIcon}
            color="bg-blue-500"
            subtitle={`${stats.active_users} 活跃用户`}
          />
          <StatCard
            title="管理员"
            value={stats.admin_users}
            icon={ShieldCheckIcon}
            color="bg-purple-500"
          />
          <StatCard
            title="总任务数"
            value={stats.total_tasks}
            icon={ClipboardDocumentListIcon}
            color="bg-green-500"
            subtitle={`${stats.completed_tasks} 已完成`}
          />
          <StatCard
            title="总报告数"
            value={stats.total_reports}
            icon={DocumentTextIcon}
            color="bg-orange-500"
          />
        </div>
      </ErrorBoundary>

      <ErrorBoundary>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="团队数量"
            value={stats.total_teams}
            icon={UserGroupIcon}
            color="bg-indigo-500"
          />
          <StatCard
            title="评论数量"
            value={stats.total_comments}
            icon={ChatBubbleLeftIcon}
            color="bg-pink-500"
          />
          <StatCard
            title="待处理反馈"
            value={feedbackStats?.pending_feedback || 0}
            icon={ChatBubbleLeftRightIcon}
            color="bg-yellow-500"
            subtitle={`平均响应: ${feedbackStats?.avg_response_time || 'N/A'}`}
            onClick={() => navigate('/admin/user-communication')}
          />
          <StatCard
            title="待处理举报"
            value={reportsStats?.pending_reports || 0}
            icon={ExclamationTriangleIcon}
            color="bg-red-500"
            subtitle={`平均处理: ${reportsStats?.avg_process_time || 'N/A'}`}
            onClick={() => navigate('/admin/reports')}
          />
        </div>
      </ErrorBoundary>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ErrorBoundary>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">任务完成率</h2>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-500"
                    style={{
                      width: stats.total_tasks > 0
                        ? `${(stats.completed_tasks / stats.total_tasks) * 100}%`
                        : '0%'
                    }}
                  />
                </div>
              </div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {stats.total_tasks > 0
                  ? `${((stats.completed_tasks / stats.total_tasks) * 100).toFixed(1)}%`
                  : '0%'}
              </span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              {stats.completed_tasks} / {stats.total_tasks} 任务已完成
            </p>
          </div>
        </ErrorBoundary>

        <ErrorBoundary>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">反馈类型分布</h2>
            {feedbackStats?.feedback_by_type && Object.keys(feedbackStats.feedback_by_type).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(feedbackStats.feedback_by_type).map(([type, count]) => {
                  const total = Object.values(feedbackStats.feedback_by_type).reduce((a, b) => a + b, 0);
                  const percentage = total > 0 ? (count / total) * 100 : 0;
                  const typeLabels: Record<string, string> = {
                    feedback: '功能反馈',
                    suggestion: '建议',
                    bug: '问题报告',
                    complaint: '投诉',
                  };
                  return (
                    <div key={type}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600 dark:text-gray-400">{typeLabels[type] || type}</span>
                        <span className="text-gray-900 dark:text-white font-medium">{count}</span>
                      </div>
                      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-500 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-sm">暂无反馈数据</p>
            )}
          </div>
        </ErrorBoundary>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ErrorBoundary>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">近7天反馈趋势</h2>
              <button
                onClick={() => navigate('/admin/user-communication')}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                查看全部
              </button>
            </div>
            <TrendChart 
              data={feedbackStats?.trend_last_7_days || null} 
              title="反馈趋势" 
              color="bg-primary-500" 
            />
          </div>
        </ErrorBoundary>

        <ErrorBoundary>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">近7天举报趋势</h2>
              <button
                onClick={() => navigate('/admin/reports')}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                查看全部
              </button>
            </div>
            <TrendChart 
              data={reportsStats?.trend_last_7_days || null} 
              title="举报趋势" 
              color="bg-red-500" 
            />
          </div>
        </ErrorBoundary>
      </div>
    </div>
  );
};

export default AdminOverview;
