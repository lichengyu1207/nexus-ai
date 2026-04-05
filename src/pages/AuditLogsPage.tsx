import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardDocumentListIcon,
  FunnelIcon,
  ArrowLeftIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import { LoadingCard } from '@/components/Loading';

interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, any> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string | null;
}

interface ActionInfo {
  action: string;
  label: string;
  description: string;
}

const ACTION_LABELS: Record<string, string> = {
  TASK_CREATE: '创建任务',
  TASK_DELETE: '删除任务',
  TASK_SHARE: '分享任务',
  REPORT_VIEW: '查看报告',
  REPORT_EXPORT: '导出报告',
  REPORT_SHARE: '分享报告',
  TEAM_CREATE: '创建团队',
  TEAM_DELETE: '删除团队',
  TEAM_JOIN: '加入团队',
  TEAM_LEAVE: '离开团队',
  TEAM_INVITE: '邀请成员',
  TEAM_MEMBER_REMOVE: '移除成员',
  TEAM_ROLE_CHANGE: '修改角色',
  TEAM_SETTINGS_CHANGE: '修改设置',
  PROFILE_UPDATE: '更新资料',
  PASSWORD_CHANGE: '修改密码',
  LOGIN: '登录',
  LOGOUT: '登出',
  COMMENT_CREATE: '发表评论',
  COMMENT_DELETE: '删除评论',
};

const ACTION_COLORS: Record<string, string> = {
  TASK_CREATE: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  TASK_DELETE: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  TASK_SHARE: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  REPORT_VIEW: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
  REPORT_EXPORT: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
  REPORT_SHARE: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  TEAM_CREATE: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  TEAM_DELETE: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  TEAM_JOIN: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  TEAM_LEAVE: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
  TEAM_INVITE: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  TEAM_MEMBER_REMOVE: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  TEAM_ROLE_CHANGE: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
  TEAM_SETTINGS_CHANGE: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
  PROFILE_UPDATE: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
  PASSWORD_CHANGE: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
  LOGIN: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  LOGOUT: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
  COMMENT_CREATE: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  COMMENT_DELETE: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
};

const AuditLogsPage: React.FC = () => {
  const navigate = useNavigate();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [actions, setActions] = useState<ActionInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState<string>('');
  const pageSize = 20;

  const loadActions = useCallback(async () => {
    try {
      const response = await api.get('/audit-logs/actions');
      setActions(response.data);
    } catch {
      console.error('Failed to load actions');
    }
  }, []);

  const loadLogs = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: Record<string, any> = {
        limit: pageSize,
        offset: (page - 1) * pageSize,
      };
      if (actionFilter) {
        params.action = actionFilter;
      }
      
      const response = await api.get('/audit-logs', { params });
      setLogs(response.data.logs);
      setTotal(response.data.total);
    } catch {
      console.error('Failed to load audit logs');
    } finally {
      setIsLoading(false);
    }
  }, [page, actionFilter]);

  useEffect(() => {
    loadActions();
  }, [loadActions]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/settings')}
            className="text-primary-600 dark:text-primary-400 hover:text-primary-700 text-sm flex items-center gap-1 mb-2"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            返回设置
          </button>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <ClipboardDocumentListIcon className="w-7 h-7 text-primary-600 dark:text-primary-400" />
            操作日志
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            共 {total} 条操作记录
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <FunnelIcon className="w-4 h-4 text-gray-400" />
            <select
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(1);
              }}
              className="px-3 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-200"
            >
              <option value="">全部操作</option>
              {actions.map(action => (
                <option key={action.action} value={action.action}>
                  {action.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Logs List */}
      {isLoading ? (
        <LoadingCard message="加载日志..." />
      ) : logs.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-12 text-center">
          <ClipboardDocumentListIcon className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">暂无操作记录</h3>
          <p className="text-gray-500 dark:text-gray-400 mt-1">您的操作记录将显示在这里</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    操作
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    资源
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    IP地址
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    时间
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
                        ACTION_COLORS[log.action] || 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}>
                        {ACTION_LABELS[log.action] || log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {log.resource_type && (
                        <div className="text-sm">
                          <span className="text-gray-500 dark:text-gray-400">{log.resource_type}</span>
                          {log.resource_id && (
                            <span className="ml-1 text-gray-400 dark:text-gray-500 font-mono text-xs">
                              {log.resource_id.slice(0, 8)}...
                            </span>
                          )}
                        </div>
                      )}
                      {log.details && Object.keys(log.details).length > 0 && (
                        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {Object.entries(log.details).slice(0, 2).map(([key, value]) => (
                            <span key={key} className="mr-2">
                              {key}: {typeof value === 'string' ? value.slice(0, 20) : String(value).slice(0, 20)}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 font-mono">
                      {log.ip_address || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                第 {page} 页，共 {totalPages} 页
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50"
                >
                  <ChevronLeftIcon className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50"
                >
                  <ChevronRightIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AuditLogsPage;
