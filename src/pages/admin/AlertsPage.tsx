import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BellAlertIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  FunnelIcon,
  EyeIcon,
  PlayIcon,
  ShieldExclamationIcon,
  XMarkIcon,
  UserIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface Alert {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string | null;
  user_id: string | null;
  username: string | null;
  ip_address: string | null;
  rule_name: string;
  matched_count: number;
  time_window_start: string;
  time_window_end: string;
  status: string;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_note: string | null;
  created_at: string;
}

interface AlertStats {
  total_alerts: number;
  open_alerts: number;
  acknowledged_alerts: number;
  resolved_alerts: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  recent_trend: Array<{ date: string; count: number }>;
}

interface Rule {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  category: string;
  severity: string;
  enabled: boolean;
  config: Record<string, unknown>;
  cooldown_minutes: number;
  notify_admins: boolean;
  last_triggered_at: string | null;
  trigger_count: number;
}

const AdminAlertsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'alerts' | 'rules' | 'stats'>('alerts');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [openCount, setOpenCount] = useState(0);
  const [criticalCount, setCriticalCount] = useState(0);
  
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    alert_type: '',
  });
  
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveNote, setResolveNote] = useState('');

  useEffect(() => {
    loadData();
  }, [activeTab, filters]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === 'alerts') {
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.severity) params.append('severity', filters.severity);
        if (filters.alert_type) params.append('alert_type', filters.alert_type);
        
        const response = await api.get(`/api/admin/alerts?${params}`);
        setAlerts(response.data.alerts);
        setTotal(response.data.total);
        setOpenCount(response.data.open_count);
        setCriticalCount(response.data.critical_count);
      } else if (activeTab === 'stats') {
        const response = await api.get('admin/alerts/stats');
        setStats(response.data);
      } else {
        const response = await api.get('admin/alerts/rules/list');
        setRules(response.data.rules);
      }
    } catch {
      showToast.error('加载失败');
    } finally {
      setLoading(false);
    }
  }, [activeTab, filters]);

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await api.post(`/api/admin/alerts/${alertId}/acknowledge`, { note: '' });
      showToast.success('告警已确认');
      loadData();
    } catch {
      showToast.error('操作失败');
    }
  };

  const resolveAlert = async () => {
    if (!selectedAlert || !resolveNote.trim()) {
      showToast.error('请填写处理说明');
      return;
    }
    
    try {
      await api.post(`/api/admin/alerts/${selectedAlert.id}/resolve`, { note: resolveNote });
      showToast.success('告警已解决');
      setShowResolveModal(false);
      setSelectedAlert(null);
      setResolveNote('');
      loadData();
    } catch {
      showToast.error('操作失败');
    }
  };

  const markFalsePositive = async (alertId: string) => {
    try {
      await api.post(`/api/admin/alerts/${alertId}/false-positive`, { note: '' });
      showToast.success('已标记为误报');
      loadData();
    } catch {
      showToast.error('操作失败');
    }
  };

  const runDetection = async () => {
    try {
      const response = await api.post('admin/alerts/run-detection');
      showToast.success(`检测完成，创建 ${response.data.alerts_created} 条告警`);
      loadData();
    } catch {
      showToast.error('检测失败');
    }
  };

  const toggleRule = async (ruleName: string, enabled: boolean) => {
    try {
      await api.put(`/api/admin/alerts/rules/${ruleName}`, { enabled });
      showToast.success(enabled ? '规则已启用' : '规则已禁用');
      loadData();
    } catch {
      showToast.error('操作失败');
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    };
    const labels: Record<string, string> = {
      critical: '严重',
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

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      open: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      acknowledged: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      resolved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      false_positive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    };
    const labels: Record<string, string> = {
      open: '待处理',
      acknowledged: '已确认',
      resolved: '已解决',
      false_positive: '误报',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles.open}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getAlertTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      brute_force_login: '暴力破解',
      bulk_delete: '批量删除',
      unusual_time_access: '非常规访问',
      permission_escalation: '权限提升',
      mass_export: '批量导出',
      multiple_ip_login: '多IP登录',
      failed_permission_access: '权限失败',
    };
    return labels[type] || type;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <BellAlertIcon className="w-7 h-7 text-primary-600" />
              安全告警
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              实时监控系统异常行为，及时发现安全威胁
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={runDetection}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
            >
              <PlayIcon className="w-4 h-4" />
              立即检测
            </button>
            {openCount > 0 && (
              <span className="flex items-center gap-1 px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full text-sm font-medium">
                <ExclamationTriangleIcon className="w-4 h-4" />
                {openCount} 条待处理
              </span>
            )}
          </div>
        </div>

        {criticalCount > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6"
          >
            <div className="flex items-center gap-3">
              <ShieldExclamationIcon className="w-6 h-6 text-red-500" />
              <div>
                <p className="font-medium text-red-800 dark:text-red-200">
                  发现 {criticalCount} 条严重告警需要立即处理
                </p>
                <p className="text-sm text-red-600 dark:text-red-300">
                  请尽快查看并处理这些安全威胁
                </p>
              </div>
            </div>
          </motion.div>
        )}

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex -mb-px">
              {[
                { id: 'alerts', label: '告警列表', icon: BellAlertIcon },
                { id: 'rules', label: '检测规则', icon: ShieldExclamationIcon },
                { id: 'stats', label: '统计分析', icon: ChartBarIcon },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
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

          {activeTab === 'alerts' && (
            <div className="p-6">
              <div className="flex flex-wrap items-center gap-4 mb-6">
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">所有状态</option>
                  <option value="open">待处理</option>
                  <option value="acknowledged">已确认</option>
                  <option value="resolved">已解决</option>
                </select>

                <select
                  value={filters.severity}
                  onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">所有级别</option>
                  <option value="critical">严重</option>
                  <option value="high">高</option>
                  <option value="medium">中</option>
                  <option value="low">低</option>
                </select>

                <select
                  value={filters.alert_type}
                  onChange={(e) => setFilters({ ...filters, alert_type: e.target.value })}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">所有类型</option>
                  <option value="brute_force_login">暴力破解</option>
                  <option value="bulk_delete">批量删除</option>
                  <option value="permission_escalation">权限提升</option>
                  <option value="mass_export">批量导出</option>
                  <option value="multiple_ip_login">多IP登录</option>
                </select>
              </div>

              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
                </div>
              ) : alerts.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircleIcon className="w-16 h-16 mx-auto text-green-500 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">暂无告警</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className={`p-4 rounded-lg border ${
                        alert.status === 'open'
                          ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800'
                          : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <ExclamationTriangleIcon className={`w-5 h-5 ${
                              alert.severity === 'critical' ? 'text-red-500' :
                              alert.severity === 'high' ? 'text-orange-500' : 'text-yellow-500'
                            }`} />
                            <span className="font-medium text-gray-900 dark:text-white">
                              {alert.title}
                            </span>
                            {getSeverityBadge(alert.severity)}
                            {getStatusBadge(alert.status)}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                            {alert.description}
                          </p>
                          <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
                            <span className="flex items-center gap-1">
                              <ClockIcon className="w-3 h-3" />
                              {formatDate(alert.created_at)}
                            </span>
                            {alert.username && (
                              <span className="flex items-center gap-1">
                                <UserIcon className="w-3 h-3" />
                                {alert.username}
                              </span>
                            )}
                            {alert.ip_address && (
                              <span className="flex items-center gap-1">
                                <GlobeAltIcon className="w-3 h-3" />
                                {alert.ip_address}
                              </span>
                            )}
                            <span>触发次数: {alert.matched_count}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => { setSelectedAlert(alert); setShowDetailModal(true); }}
                            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                            title="查看详情"
                          >
                            <EyeIcon className="w-5 h-5" />
                          </button>
                          {alert.status === 'open' && (
                            <>
                              <button
                                onClick={() => acknowledgeAlert(alert.id)}
                                className="px-3 py-1 text-sm bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
                              >
                                确认
                              </button>
                              <button
                                onClick={() => { setSelectedAlert(alert); setShowResolveModal(true); }}
                                className="px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
                              >
                                解决
                              </button>
                            </>
                          )}
                          {alert.status !== 'resolved' && alert.status !== 'false_positive' && (
                            <button
                              onClick={() => markFalsePositive(alert.id)}
                              className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500"
                            >
                              误报
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'rules' && (
            <div className="p-6">
              {loading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
                </div>
              ) : (
                <div className="space-y-4">
                  {rules.map((rule) => (
                    <div
                      key={rule.id}
                      className={`p-4 rounded-lg border ${
                        rule.enabled
                          ? 'bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600'
                          : 'bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-gray-900 dark:text-white">
                              {rule.display_name}
                            </span>
                            {getSeverityBadge(rule.severity)}
                            {!rule.enabled && (
                              <span className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-full">
                                已禁用
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {rule.description}
                          </p>
                          <div className="flex gap-4 mt-2 text-xs text-gray-400">
                            <span>类别: {rule.category}</span>
                            <span>冷却时间: {rule.cooldown_minutes}分钟</span>
                            <span>触发次数: {rule.trigger_count}</span>
                          </div>
                        </div>
                        <button
                          onClick={() => toggleRule(rule.name, !rule.enabled)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            rule.enabled ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              rule.enabled ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
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
                <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                  <p className="text-sm text-red-600 dark:text-red-400">总告警</p>
                  <p className="text-2xl font-bold text-red-700 dark:text-red-300">
                    {stats.total_alerts}
                  </p>
                </div>
                <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4">
                  <p className="text-sm text-orange-600 dark:text-orange-400">待处理</p>
                  <p className="text-2xl font-bold text-orange-700 dark:text-orange-300">
                    {stats.open_alerts}
                  </p>
                </div>
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                  <p className="text-sm text-yellow-600 dark:text-yellow-400">已确认</p>
                  <p className="text-2xl font-bold text-yellow-700 dark:text-yellow-300">
                    {stats.acknowledged_alerts}
                  </p>
                </div>
                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                  <p className="text-sm text-green-600 dark:text-green-400">已解决</p>
                  <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                    {stats.resolved_alerts}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    按严重级别分布
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(stats.by_severity).map(([severity, count]) => (
                      <div key={severity} className="flex items-center gap-4">
                        <span className="w-16 text-sm text-gray-600 dark:text-gray-400">
                          {severity}
                        </span>
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              severity === 'critical' ? 'bg-red-500' :
                              severity === 'high' ? 'bg-orange-500' :
                              severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                            }`}
                            style={{
                              width: `${Math.min(100, (count / Math.max(...Object.values(stats.by_severity))) * 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400 w-12 text-right">
                          {count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    按类型分布
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(stats.by_type).slice(0, 8).map(([type, count]) => (
                      <div key={type} className="flex items-center gap-4">
                        <span className="w-32 text-sm text-gray-600 dark:text-gray-400 truncate">
                          {getAlertTypeLabel(type)}
                        </span>
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-primary-500 h-2 rounded-full"
                            style={{
                              width: `${Math.min(100, (count / Math.max(...Object.values(stats.by_type))) * 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400 w-12 text-right">
                          {count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <AnimatePresence>
        {showDetailModal && selectedAlert && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setShowDetailModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 max-w-lg w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  告警详情
                </h3>
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">标题</p>
                  <p className="text-gray-900 dark:text-white">{selectedAlert.title}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">描述</p>
                  <p className="text-gray-900 dark:text-white">{selectedAlert.description}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">严重级别</p>
                    {getSeverityBadge(selectedAlert.severity)}
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">状态</p>
                    {getStatusBadge(selectedAlert.status)}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500 dark:text-gray-400">用户</p>
                    <p className="text-gray-900 dark:text-white">{selectedAlert.username || selectedAlert.user_id || '-'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 dark:text-gray-400">IP地址</p>
                    <p className="text-gray-900 dark:text-white font-mono">{selectedAlert.ip_address || '-'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 dark:text-gray-400">触发次数</p>
                    <p className="text-gray-900 dark:text-white">{selectedAlert.matched_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 dark:text-gray-400">创建时间</p>
                    <p className="text-gray-900 dark:text-white">{formatDate(selectedAlert.created_at)}</p>
                  </div>
                </div>
                {selectedAlert.resolution_note && (
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">处理说明</p>
                    <p className="text-gray-900 dark:text-white">{selectedAlert.resolution_note}</p>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showResolveModal && selectedAlert && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setShowResolveModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 max-w-md w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                解决告警
              </h3>
              <textarea
                value={resolveNote}
                onChange={(e) => setResolveNote(e.target.value)}
                placeholder="请输入处理说明..."
                className="w-full h-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              />
              <div className="flex justify-end gap-2 mt-4">
                <button
                  onClick={() => setShowResolveModal(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                >
                  取消
                </button>
                <button
                  onClick={resolveAlert}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  确认解决
                </button>
              </div>
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

export default AdminAlertsPage;
