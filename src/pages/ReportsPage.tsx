import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  DocumentTextIcon,
  EyeIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import ReportSearchBar, { SearchFilters } from '@/components/ReportSearchBar';
import { LoadingCard } from '@/components/Loading';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface Report {
  id: string;
  task_id: string;
  status: string;
  summary: string | null;
  version: number;
  progress: number;
  created_at: string | null;
  completed_at: string | null;
}

const ReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<Report[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState<SearchFilters>({
    q: '',
    status: '',
    start_date: '',
    end_date: '',
  });
  const [page, setPage] = useState(1);
  const pageSize = 12;

  const loadReports = useCallback(async (searchFilters: SearchFilters, pageNum: number) => {
    setIsLoading(true);
    try {
      const params: Record<string, string | number> = {
        limit: pageSize,
        offset: (pageNum - 1) * pageSize,
      };

      if (searchFilters.q) params.q = searchFilters.q;
      if (searchFilters.status) params.status = searchFilters.status;
      if (searchFilters.start_date) params.start_date = searchFilters.start_date;
      if (searchFilters.end_date) params.end_date = searchFilters.end_date;

      const response = await api.get('/reports', { params });
      setReports(response.data.reports || []);
      setTotal(response.data.total || 0);
    } catch {
      showToast.error('加载报告失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports(filters, page);
  }, [loadReports, filters, page]);

  const handleSearch = (newFilters: SearchFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { icon: React.ReactNode; bg: string; text: string; label: string }> = {
      completed: {
        icon: <CheckCircleIcon className="w-5 h-5" />,
        bg: 'bg-green-100',
        text: 'text-green-700',
        label: '已完成',
      },
      failed: {
        icon: <ExclamationCircleIcon className="w-5 h-5" />,
        bg: 'bg-red-100',
        text: 'text-red-700',
        label: '失败',
      },
      generating: {
        icon: <ArrowPathIcon className="w-5 h-5 animate-spin" />,
        bg: 'bg-blue-100',
        text: 'text-blue-700',
        label: '生成中',
      },
      pending: {
        icon: <ClockIcon className="w-5 h-5" />,
        bg: 'bg-gray-100',
        text: 'text-gray-700',
        label: '等待中',
      },
      archived: {
        icon: <DocumentTextIcon className="w-5 h-5" />,
        bg: 'bg-gray-100',
        text: 'text-gray-600',
        label: '已归档',
      },
    };
    return configs[status] || configs.pending;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <DocumentTextIcon className="w-7 h-7 text-primary-600" />
            我的报告
          </h1>
          <p className="text-gray-600 mt-1">搜索和管理您的分析报告</p>
        </div>
        <Link
          to="/tasks"
          className="text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          查看任务列表 →
        </Link>
      </div>

      {/* Search Bar */}
      <ReportSearchBar onSearch={handleSearch} isLoading={isLoading} />

      {/* Results */}
      {isLoading ? (
        <LoadingCard message="加载报告..." />
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <DocumentTextIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">暂无报告</h3>
          <p className="text-gray-500 mt-1">
            {filters.q || filters.status || filters.start_date || filters.end_date
              ? '没有找到匹配的报告，请尝试其他搜索条件'
              : '创建分析任务后，报告将显示在这里'}
          </p>
          {!filters.q && !filters.status && !filters.start_date && !filters.end_date && (
            <Link
              to="/dashboard"
              className="inline-block mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              创建分析任务
            </Link>
          )}
        </div>
      ) : (
        <>
          {/* Results Count */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              共找到 <span className="font-medium text-gray-900">{total}</span> 份报告
            </p>
          </div>

          {/* Reports Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => {
              const statusConfig = getStatusConfig(report.status);
              return (
                <div
                  key={report.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow"
                >
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bg} ${statusConfig.text}`}>
                        {statusConfig.icon}
                        {statusConfig.label}
                      </span>
                      {report.version > 1 && (
                        <span className="text-xs text-gray-400">V{report.version}</span>
                      )}
                    </div>

                    <p className="text-sm text-gray-700 line-clamp-3 min-h-[60px]">
                      {report.summary || '报告生成中...'}
                    </p>

                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{formatDate(report.created_at)}</span>
                        {report.status === 'generating' && (
                          <span>{report.progress}%</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {report.status === 'completed' && (
                    <button
                      onClick={() => navigate(`/tasks/${report.task_id}/report`)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-50 text-gray-700 hover:bg-gray-100 text-sm font-medium"
                    >
                      <EyeIcon className="w-4 h-4" />
                      查看报告
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <span className="text-sm text-gray-600">
                第 {page} / {totalPages} 页
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ReportsPage;
