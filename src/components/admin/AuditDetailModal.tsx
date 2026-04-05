import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ClockIcon,
  UserIcon,
  GlobeAltIcon,
  ComputerDesktopIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { AuditLog } from '@/api/admin/audit';

interface AuditDetailModalProps {
  log: AuditLog | null;
  isOpen: boolean;
  onClose: () => void;
}

const AuditDetailModal: React.FC<AuditDetailModalProps> = ({ log, isOpen, onClose }) => {
  if (!log) return null;

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

  const getActionTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      LOGIN: '登录',
      LOGOUT: '登出',
      LOGIN_FAILED: '登录失败',
      REGISTER: '注册',
      PASSWORD_CHANGE: '修改密码',
      PROFILE_UPDATE: '更新资料',
      TASK_CREATE: '创建任务',
      TASK_VIEW: '查看任务',
      TASK_UPDATE: '更新任务',
      TASK_DELETE: '删除任务',
      TASK_ASSIGN: '分配任务',
      REPORT_CREATE: '创建报告',
      REPORT_VIEW: '查看报告',
      REPORT_EXPORT: '导出报告',
      REPORT_DELETE: '删除报告',
      REPORT_SHARE: '分享报告',
      TEAM_CREATE: '创建团队',
      TEAM_JOIN: '加入团队',
      TEAM_LEAVE: '离开团队',
      TEAM_MEMBER_ADD: '添加成员',
      TEAM_MEMBER_REMOVE: '移除成员',
      TEAM_DELETE: '删除团队',
      FEEDBACK_CREATE: '创建反馈',
      FEEDBACK_REPLY: '回复反馈',
      ADMIN_USER_VIEW: '查看用户',
      ADMIN_USER_CREATE: '创建用户',
      ADMIN_USER_UPDATE: '更新用户',
      ADMIN_USER_DELETE: '删除用户',
      ADMIN_SETTING_CHANGE: '修改设置',
      ADMIN_ANNOUNCEMENT_CREATE: '创建公告',
      ADMIN_ANNOUNCEMENT_PUBLISH: '发布公告',
      DATA_EXPORT: '数据导出',
      DATA_IMPORT: '数据导入',
      API_ACCESS: 'API访问',
      FILE_UPLOAD: '文件上传',
      FILE_DOWNLOAD: '文件下载',
      PRIVACY_CONSENT: '隐私同意',
    };
    return labels[type] || type;
  };

  const getResourceTypeLabel = (type: string | null) => {
    const labels: Record<string, string> = {
      user: '用户',
      task: '任务',
      report: '报告',
      team: '团队',
      feedback: '反馈',
      announcement: '公告',
      setting: '设置',
      file: '文件',
      system: '系统',
    };
    return type ? labels[type] || type : '-';
  };

  const formatJsonValue = (value: unknown): string => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm"
              onClick={onClose}
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <DocumentTextIcon className="w-5 h-5 text-primary-500" />
                  审计日志详情
                </h2>
                <button
                  onClick={onClose}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {log.status === 'success' ? (
                      <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                        <CheckCircleIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                        <ExclamationTriangleIcon className="w-5 h-5 text-red-600 dark:text-red-400" />
                      </div>
                    )}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {getActionTypeLabel(log.action_type)}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {log.status === 'success' ? '操作成功' : '操作失败'}
                      </p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    log.status === 'success'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  }`}>
                    {log.status === 'success' ? '成功' : '失败'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <ClockIcon className="w-5 h-5 text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">时间戳</p>
                        <p className="text-sm text-gray-900 dark:text-white">{formatDate(log.timestamp)}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <UserIcon className="w-5 h-5 text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">用户</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {log.username || log.user_id || '匿名用户'}
                        </p>
                        {log.user_role && (
                          <p className="text-xs text-gray-400">角色: {log.user_role}</p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <GlobeAltIcon className="w-5 h-5 text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">IP地址</p>
                        <p className="text-sm text-gray-900 dark:text-white font-mono">
                          {log.ip_address || '-'}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <ArrowPathIcon className="w-5 h-5 text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">操作类型</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {log.action_type}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <DocumentTextIcon className="w-5 h-5 text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">资源</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {getResourceTypeLabel(log.resource_type)}
                        </p>
                        {log.resource_id && (
                          <p className="text-xs text-gray-400 font-mono truncate max-w-[200px]">
                            ID: {log.resource_id}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <ComputerDesktopIcon className="w-5 h-5 text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">User-Agent</p>
                        <p className="text-sm text-gray-900 dark:text-white truncate max-w-[200px]">
                          {log.user_agent || '-'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {log.error_message && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <p className="text-sm font-medium text-red-800 dark:text-red-200 mb-1">错误信息</p>
                    <p className="text-sm text-red-700 dark:text-red-300">{log.error_message}</p>
                  </div>
                )}

                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">旧值 (Old Value)</p>
                      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 max-h-40 overflow-auto">
                        <pre className="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-mono">
                          {formatJsonValue(log.old_value)}
                        </pre>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">新值 (New Value)</p>
                      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 max-h-40 overflow-auto">
                        <pre className="text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-mono">
                          {formatJsonValue(log.new_value)}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">日志ID</p>
                  <p className="text-xs font-mono text-gray-600 dark:text-gray-300 break-all">
                    {log.id}
                  </p>
                </div>
              </div>

              <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
                <div className="flex justify-end">
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                  >
                    关闭
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default AuditDetailModal;
