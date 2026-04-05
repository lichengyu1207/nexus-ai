import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowDownTrayIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  DocumentMagnifyingGlassIcon,
  ClockIcon,
  UserIcon,
  XMarkIcon,
  CalendarIcon,
  ComputerDesktopIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import auditApi, { AuditLog, AuditStats, Anomaly, VerificationResult, ActionType, ResourceType } from '@/api/admin/audit';
import showToast from '@/utils/toast';
import AuditDetailModal from '@/components/admin/AuditDetailModal';

const AuditPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'logs' | 'anomalies' | 'stats'>('logs');
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [totalLogs, setTotalLogs] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    user_id: '',
    action_type: '',
    resource_type: '',
    resource_id: '',
    status: '',
    ip_address: '',
    search: '',
    sort_by: 'timestamp' as const,
    sort_order: 'desc' as const,
  });
  
  const [page, setPage] = useState(1);
  const perPage = 50;
  
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  
  const [actionTypes, setActionTypes] = useState<ActionType[]>([]);
  const [resourceTypes, setResourceTypes] = useState<ResourceType[]>([]);

  useEffect(() => {
    loadActionTypes();
    loadResourceTypes();
  }, []);

  useEffect(() => {
    loadData();
  }, [activeTab, page, filters.sort_by, filters.sort_order]);

  const loadActionTypes = async () => {
    try {
      const response = await auditApi.getActionTypes();
      setActionTypes(response.types);
    } catch {
      // Ignore
    }
  };

  const loadResourceTypes = async () => {
    try {
      const response = await auditApi.getResourceTypes();
      setResourceTypes(response.types);
    } catch {
      // Ignore
    }
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === 'logs') {
        const response = await auditApi.getLogs({
          ...filters,
          page,
          per_page: perPage,
        });
        setLogs(response.logs);
        setTotalLogs(response.total);
        setTotalPages(response.total_pages);
      } else if (activeTab === 'anomalies') {
        const response = await auditApi.getAnomalies();
        setAnomalies(response);
      } else {
        const response = await auditApi.getStats(30);
        setStats(response);
      }
    } catch {
      showToast.error('加载失败');
    } finally {
      setLoading(false);
    }
  }, [activeTab, page, filters]);

  const handleSearch = () => {
    setPage(1);
    loadData();
  };

  const handleResetFilters = () => {
    setFilters({
      start_date: '',
      end_date: '',
      user_id: '',
      action_type: '',
      resource_type: '',
      resource_id: '',
      status: '',
      ip_address: '',
      search: '',
      sort_by: 'timestamp',
      sort_order: 'desc',
    });
    setPage(1);
  };

  const verifyChain = async () => {
    setVerifying(true);
    try {
      const result = await auditApi.verifyChain(10000, true);
      setVerificationResult(result);
      if (result.status === 'valid') {
        showToast.success(`验证通过，完整性评分: ${result.integrity_score}%`);
      } else if (result.status === 'warning') {
        showToast.warning(`验证完成，存在签名问题，评分: ${result.integrity_score}%`);
      } else {
        showToast.error(`验证失败，发现 ${result.summary.hash_errors + result.summary.chain_errors} 个错误`);
      }
    } catch {
      showToast.error('验证失败');
    } finally {
      setVerifying(false);
    }
  };

  const signLogs = async () => {
    try {
      const result = await auditApi.signLogs(100);
      showToast.success(result.message);
    } catch {
      showToast.error('签名失败');
    }
  };

  const exportLogs = async (format: 'csv' | 'json') => {
    try {
      const blob = await auditApi.exportLogs(filters, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      link.setAttribute('download', `audit_logs_${timestamp}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setShowExportModal(false);
      showToast.success('导出成功');
    } catch {
      showToast.error('导出失败');
    }
  };

  const generateReport = async () => {
    try {
      showToast.info('正在生成报告...');
      const response = await api.post('/admin/audit/report', {
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
        user_id: filters.user_id || undefined,
        action_types: filters.action_type ? [filters.action_type] : undefined,
        include_logs: true,
      }, { responseType: 'blob' });
      
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      link.setAttribute('download', `audit_report_${timestamp}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      showToast.success('报告生成成功');
    } catch {
      showToast.error('报告生成失败');
    }
  };

  const resolveAnomaly = async (id: string) => {
    try {
      await auditApi.resolveAnomaly(id);
      showToast.success('已标记为已处理');
      loadData();
    } catch {
      showToast.error('操作失败');
    }
  };

  const handleRowClick = (log: AuditLog) => {
    setSelectedLog(log);
    setShowDetailModal(true);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const getStatusBadge = (status: string) => {
    if (status === 'success') {
      return (
        <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full">
          成功
        </span>
      );
    }
    return (
      <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 rounded-full">
        失败
      </span>
    );
  };

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    };
    const labels: Record<string, string> = {
      high: '高',
      medium: '中',
      low: '低',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[severity] || styles.low}`}>
        {labels[severity] || severity}
      </span>
    );
  };

  const getActionTypeLabel = (type: string) => {
    const found = actionTypes.find(t => t.value === type);
    return found?.label || type;
  };

  const hasActiveFilters = Object.values(filters).some(v => v && v !== 'timestamp' && v !== 'desc');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <ShieldCheckIcon className="w-7 h-7 text-primary-600" />
              合规审计
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              查看和管理系统审计日志，确保合规性
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={signLogs}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
            >
              <ShieldCheckIcon className="w-4 h-4" />
              签名日志
            </button>
            <button
              onClick={verifyChain}
              disabled={verifying}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              <DocumentMagnifyingGlassIcon className="w-4 h-4" />
              {verifying ? '验证中...' : '验证完整性'}
            </button>
            {verificationResult && (
              <span className={`flex items-center gap-1 text-sm font-medium ${
                verificationResult.status === 'valid' ? 'text-green-600' : 
                verificationResult.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {verificationResult.status === 'valid' ? (
                  <CheckCircleIcon className="w-4 h-4" />
                ) : (
                  <ExclamationTriangleIcon className="w-4 h-4" />
                )}
                完整性: {verificationResult.integrity_score}%
              </span>
            )}
          </div>
        </div>

        {verificationResult && verificationResult.status !== 'valid' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6"
          >
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-medium text-red-800 dark:text-red-200">验证发现问题</h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  <p>哈希错误: {verificationResult.summary.hash_errors} 个</p>
                  <p>链断裂: {verificationResult.summary.chain_errors} 个</p>
                  <p>签名错误: {verificationResult.summary.signature_errors} 个</p>
                </div>
                <div className="mt-3">
                  <p className="text-sm font-medium text-red-800 dark:text-red-200">建议:</p>
                  <ul className="mt-1 text-sm text-red-700 dark:text-red-300 list-disc list-inside">
                    {verificationResult.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <button
                onClick={() => setVerificationResult(null)}
                className="text-red-500 hover:text-red-700"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        )}

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex -mb-px">
              {[
                { id: 'logs', label: '审计日志', icon: ClockIcon },
                { id: 'anomalies', label: '异常行为', icon: ExclamationTriangleIcon },
                { id: 'stats', label: '统计分析', icon: ChartBarIcon },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id as typeof activeTab); setPage(1); }}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                      : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {activeTab === 'logs' && (
            <div className="p-6">
              <div className="flex flex-wrap items-center gap-4 mb-6">
                <div className="flex-1 min-w-[200px] max-w-md">
                  <div className="relative">
                    <MagnifyingGlassIcon className="absolute left-3 top-1/2 w-4 h-4 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="搜索用户名、资源ID、IP..."
                      value={filters.search}
                      onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                  </div>
                </div>
                
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium transition-colors ${
                    hasActiveFilters
                      ? 'border-primary-500 text-primary-600 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600'
                  }`}
                >
                  <FunnelIcon className="w-4 h-4" />
                  筛选
                  {hasActiveFilters && (
                    <span className="w-2 h-2 bg-primary-500 rounded-full" />
                  )}
                </button>

                <select
                  value={filters.action_type}
                  onChange={(e) => setFilters({ ...filters, action_type: e.target.value })}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">所有操作</option>
                  {actionTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>

                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">所有状态</option>
                  <option value="success">成功</option>
                  <option value="failure">失败</option>
                </select>

                <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              导出
            </button>
            <button
              onClick={generateReport}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <DocumentTextIcon className="w-4 h-4" />
              生成报告
            </button>
              </div>

              <AnimatePresence>
                {showFilters && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden mb-6"
                  >
                    <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-4 space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            <CalendarIcon className="w-4 h-4 inline mr-1" />
                            开始日期
                          </label>
                          <input
                            type="date"
                            value={filters.start_date}
                            onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            <CalendarIcon className="w-4 h-4 inline mr-1" />
                            结束日期
                          </label>
                          <input
                            type="date"
                            value={filters.end_date}
                            onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            <UserIcon className="w-4 h-4 inline mr-1" />
                            用户ID
                          </label>
                          <input
                            type="text"
                            placeholder="输入用户ID"
                            value={filters.user_id}
                            onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            资源类型
                          </label>
                          <select
                            value={filters.resource_type}
                            onChange={(e) => setFilters({ ...filters, resource_type: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            <option value="">所有资源</option>
                            {resourceTypes.map((type) => (
                              <option key={type.value} value={type.value}>{type.label}</option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            资源ID
                          </label>
                          <input
                            type="text"
                            placeholder="输入资源ID"
                            value={filters.resource_id}
                            onChange={(e) => setFilters({ ...filters, resource_id: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            <ComputerDesktopIcon className="w-4 h-4 inline mr-1" />
                            IP地址
                          </label>
                          <input
                            type="text"
                            placeholder="支持模糊匹配"
                            value={filters.ip_address}
                            onChange={(e) => setFilters({ ...filters, ip_address: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                      </div>
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={handleResetFilters}
                          className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                        >
                          重置
                        </button>
                        <button
                          onClick={handleSearch}
                          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700"
                        >
                          应用筛选
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="flex items-center justify-between mb-4 text-sm text-gray-500 dark:text-gray-400">
                <span>共 {totalLogs.toLocaleString()} 条记录</span>
                <div className="flex items-center gap-2">
                  <span>排序:</span>
                  <select
                    value={filters.sort_by}
                    onChange={(e) => setFilters({ ...filters, sort_by: e.target.value as typeof filters.sort_by })}
                    className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  >
                    <option value="timestamp">时间</option>
                    <option value="user_id">用户</option>
                    <option value="action_type">操作类型</option>
                    <option value="status">状态</option>
                  </select>
                  <select
                    value={filters.sort_order}
                    onChange={(e) => setFilters({ ...filters, sort_order: e.target.value as typeof filters.sort_order })}
                    className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  >
                    <option value="desc">降序</option>
                    <option value="asc">升序</option>
                  </select>
                </div>
              </div>

              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">加载中...</p>
                </div>
              ) : logs.length === 0 ? (
                <div className="text-center py-12">
                  <ClockIcon className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">暂无审计日志</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead>
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          时间
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          用户
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          操作
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          资源
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          IP
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          状态
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {logs.map((log) => (
                        <tr
                          key={log.id}
                          onClick={() => handleRowClick(log)}
                          className="hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
                        >
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-white whitespace-nowrap">
                            {formatDate(log.timestamp)}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                            <div className="flex items-center gap-2">
                              <UserIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                              <span className="truncate max-w-[120px]">
                                {log.username || log.user_id || '匿名'}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                            {getActionTypeLabel(log.action_type)}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                            {log.resource_type && (
                              <span className="text-gray-400 dark:text-gray-500 mr-1">
                                {log.resource_type}:
                              </span>
                            )}
                            <span className="font-mono text-xs">
                              {log.resource_id?.substring(0, 8) || '-'}
                              {log.resource_id && log.resource_id.length > 8 && '...'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 font-mono">
                            {log.ip_address || '-'}
                          </td>
                          <td className="px-4 py-3">
                            {getStatusBadge(log.status)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <ChevronLeftIcon className="w-4 h-4" />
                    上一页
                  </button>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      第 {page} / {totalPages} 页
                    </span>
                  </div>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page >= totalPages}
                    className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    下一页
                    <ChevronRightIcon className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'anomalies' && (
            <div className="p-6">
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
                </div>
              ) : anomalies.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircleIcon className="w-16 h-16 mx-auto text-green-500 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">暂无异常行为</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {anomalies.map((anomaly) => (
                    <div
                      key={anomaly.id}
                      className={`p-4 rounded-lg border ${
                        anomaly.is_resolved
                          ? 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-700'
                          : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                            <span className="font-medium text-gray-900 dark:text-white">
                              {anomaly.anomaly_type}
                            </span>
                            {getSeverityBadge(anomaly.severity)}
                            {anomaly.is_resolved && (
                              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full">
                                已处理
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {anomaly.description}
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                            {formatDate(anomaly.created_at)}
                            {anomaly.username && ` · 用户: ${anomaly.username}`}
                          </p>
                        </div>
                        {!anomaly.is_resolved && (
                          <button
                            onClick={() => resolveAnomaly(anomaly.id)}
                            className="px-3 py-1 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                          >
                            标记已处理
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'stats' && stats && (
            <div className="p-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <p className="text-sm text-blue-600 dark:text-blue-400">总日志数</p>
                  <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                    {stats.total_logs?.toLocaleString() || 0}
                  </p>
                </div>
                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                  <p className="text-sm text-green-600 dark:text-green-400">今日日志</p>
                  <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                    {stats.logs_today?.toLocaleString() || 0}
                  </p>
                </div>
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                  <p className="text-sm text-purple-600 dark:text-purple-400">本周日志</p>
                  <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                    {stats.logs_this_week?.toLocaleString() || 0}
                  </p>
                </div>
                <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                  <p className="text-sm text-red-600 dark:text-red-400">失败操作</p>
                  <p className="text-2xl font-bold text-red-700 dark:text-red-300">
                    {stats.failure_count?.toLocaleString() || 0}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    热门操作 TOP 10
                  </h3>
                  <div className="space-y-2">
                    {stats.top_actions?.slice(0, 10).map((item, index) => (
                      <div key={item.action_type} className="flex items-center gap-4">
                        <span className="w-6 text-sm text-gray-400">{index + 1}</span>
                        <span className="w-32 text-sm text-gray-600 dark:text-gray-400 truncate">
                          {item.label}
                        </span>
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-primary-500 h-2 rounded-full transition-all"
                            style={{
                              width: `${Math.min(100, (item.count / (stats.top_actions?.[0]?.count || 1)) * 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400 w-16 text-right">
                          {item.count.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    活跃用户 TOP 10
                  </h3>
                  <div className="space-y-2">
                    {stats.top_users?.slice(0, 10).map((item, index) => (
                      <div key={item.user_id || index} className="flex items-center gap-4">
                        <span className="w-6 text-sm text-gray-400">{index + 1}</span>
                        <span className="w-32 text-sm text-gray-600 dark:text-gray-400 truncate">
                          {item.username || item.user_id || '匿名'}
                        </span>
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-green-500 h-2 rounded-full transition-all"
                            style={{
                              width: `${Math.min(100, (item.count / (stats.top_users?.[0]?.count || 1)) * 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400 w-16 text-right">
                          {item.count.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-8">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  每日趋势（最近30天）
                </h3>
                <div className="h-48 flex items-end gap-1">
                  {stats.daily_trend?.slice(0, 30).map((day, index) => {
                    const maxCount = Math.max(...(stats.daily_trend?.map(d => d.count) || [1]));
                    const height = (day.count / maxCount) * 100;
                    return (
                      <div
                        key={day.date || index}
                        className="flex-1 flex flex-col items-center gap-1"
                        title={`${day.date}: ${day.count} 条`}
                      >
                        <div
                          className="w-full bg-primary-500 rounded-t transition-all hover:bg-primary-400"
                          style={{ height: `${height}%`, minHeight: '2px' }}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <AuditDetailModal
        log={selectedLog}
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
      />

      <AnimatePresence>
        {showExportModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setShowExportModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 max-w-md w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                导出审计日志
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                选择导出格式，将根据当前筛选条件导出日志数据
              </p>
              <div className="flex gap-4">
                <button
                  onClick={() => exportLogs('csv')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <ArrowDownTrayIcon className="w-5 h-5" />
                  CSV 格式
                </button>
                <button
                  onClick={() => exportLogs('json')}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  <ArrowDownTrayIcon className="w-5 h-5" />
                  JSON 格式
                </button>
              </div>
              <button
                onClick={() => setShowExportModal(false)}
                className="w-full mt-4 px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                取消
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

function ChartBarIcon(props: React.ComponentProps<'svg'>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  );
}

export default AuditPage;
