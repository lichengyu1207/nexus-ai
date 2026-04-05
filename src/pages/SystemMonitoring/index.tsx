import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChartBarIcon,
  BellIcon,
  ClockIcon,
  HeartIcon,
  MegaphoneIcon,
} from '@heroicons/react/24/outline';
import { TimeRangeSelector } from './components/TimeRangeSelector';
import { MetricCard } from './components/MetricCard';
import { MetricChart } from './components/MetricChart';
import { AlertRuleTable } from './components/AlertRuleTable';
import { AlertRuleModal, AlertRuleFormData } from './components/AlertRuleModal';
import { AlertHistoryList } from './components/AlertHistoryList';
import { HealthCheckCard } from './components/HealthCheckCard';
import { NotificationChannelTable } from './components/NotificationChannelTable';
import { useMetrics } from './hooks/useMetrics';
import { useAlertRules } from './hooks/useAlertRules';
import { useAlertHistory } from './hooks/useAlertHistory';
import { useHealthChecks } from './hooks/useHealthChecks';
import { useNotificationChannels } from './hooks/useNotificationChannels';
import { useAlertWebSocket } from './hooks/useAlertWebSocket';
import type { TimeRange, AlertRule, AlertEvent, MetricSeries } from './types';

const TABS = [
  { id: 'dashboard', label: '监控仪表盘', icon: ChartBarIcon },
  { id: 'rules', label: '告警规则', icon: BellIcon },
  { id: 'history', label: '告警历史', icon: ClockIcon },
  { id: 'health', label: '健康检查', icon: HeartIcon },
  { id: 'channels', label: '通知渠道', icon: MegaphoneIcon },
];

const MOCK_METRICS: MetricSeries[] = [
  {
    metric: 'agent.cpu.usage',
    unit: '%',
    data: Array.from({ length: 60 }, (_, i) => ({
      timestamp: Date.now() - (59 - i) * 60000,
      value: 30 + Math.random() * 40,
    })),
  },
  {
    metric: 'agent.memory.usage',
    unit: '%',
    data: Array.from({ length: 60 }, (_, i) => ({
      timestamp: Date.now() - (59 - i) * 60000,
      value: 50 + Math.random() * 30,
    })),
  },
  {
    metric: 'task.throughput',
    unit: '个/秒',
    data: Array.from({ length: 60 }, (_, i) => ({
      timestamp: Date.now() - (59 - i) * 60000,
      value: 100 + Math.random() * 50,
    })),
  },
  {
    metric: 'api.latency.p99',
    unit: 'ms',
    data: Array.from({ length: 60 }, (_, i) => ({
      timestamp: Date.now() - (59 - i) * 60000,
      value: 50 + Math.random() * 100,
    })),
  },
];

export default function SystemMonitoringPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [timeRange, setTimeRange] = useState<TimeRange>({
    from: Date.now() - 3600000,
    to: Date.now(),
  });
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);

  const { data: metricsData, summaries, refresh: refreshMetrics } = useMetrics({
    metrics: ['agent.cpu.usage', 'agent.memory.usage', 'task.throughput', 'api.latency.p99'],
    timeRange,
    refreshInterval,
  });

  const {
    rules,
    createRule,
    deleteRule,
    toggleRule,
  } = useAlertRules();

  const {
    events,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useAlertHistory();

  const {
    checks,
    triggerCheck,
    isTriggering,
    getOverallStatus,
  } = useHealthChecks();

  const {
    channels,
    testChannel,
    isTesting,
  } = useNotificationChannels();

  useAlertWebSocket({
    onNewAlert: () => {
      refetchHistory();
    },
    onAlertResolved: () => {
      refetchHistory();
    },
    enabled: true,
  });

  const handleCreateRule = useCallback((data: AlertRuleFormData) => {
    createRule(data);
    setShowRuleModal(false);
    setEditingRule(null);
  }, [createRule]);

  const handleEditRule = useCallback((rule: AlertRule) => {
    setEditingRule(rule);
    setShowRuleModal(true);
  }, []);

  const handleDeleteRule = useCallback((id: string) => {
    if (confirm('确定要删除此告警规则吗？')) {
      deleteRule(id);
    }
  }, [deleteRule]);

  const handleToggleRule = useCallback((id: string, enabled: boolean) => {
    toggleRule({ id, enabled });
  }, [toggleRule]);

  const handleViewAlertDetail = useCallback((alert: AlertEvent) => {
    console.log('View alert detail:', alert);
  }, []);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <TimeRangeSelector
                value={timeRange}
                onChange={setTimeRange}
                refreshInterval={refreshInterval}
                onRefresh={refreshMetrics}
              />
            </div>

            <div className="grid grid-cols-4 gap-4">
              <MetricCard
                title="CPU 使用率"
                value={summaries[0]?.value || 45}
                unit="%"
                trend={summaries[0]?.trend || 'stable'}
                trendValue={summaries[0]?.trendValue || 0}
                status={summaries[0]?.status || 'normal'}
                threshold={80}
              />
              <MetricCard
                title="内存使用率"
                value={summaries[1]?.value || 65}
                unit="%"
                trend={summaries[1]?.trend || 'stable'}
                trendValue={summaries[1]?.trendValue || 0}
                status={summaries[1]?.status || 'normal'}
                threshold={85}
              />
              <MetricCard
                title="任务吞吐量"
                value={summaries[2]?.value || 120}
                unit="个/秒"
                trend={summaries[2]?.trend || 'up'}
                trendValue={summaries[2]?.trendValue || 5}
              />
              <MetricCard
                title="API P99 延迟"
                value={summaries[3]?.value || 85}
                unit="ms"
                trend={summaries[3]?.trend || 'stable'}
                trendValue={summaries[3]?.trendValue || 0}
                status={summaries[3]?.value > 100 ? 'warning' : 'normal'}
                threshold={200}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              {(metricsData || MOCK_METRICS).slice(0, 2).map((series, index) => (
                <MetricChart
                  key={series.metric}
                  title={series.metric === 'agent.cpu.usage' ? '智能体 CPU 使用率' : '智能体内存使用率'}
                  data={series}
                  color={index === 0 ? '#f59e0b' : '#3b82f6'}
                />
              ))}
            </div>

            <div className="grid grid-cols-2 gap-4">
              {(metricsData || MOCK_METRICS).slice(2, 4).map((series, index) => (
                <MetricChart
                  key={series.metric}
                  title={series.metric === 'task.throughput' ? '任务吞吐量' : 'API P99 延迟'}
                  data={series}
                  color={index === 0 ? '#22c55e' : '#8b5cf6'}
                />
              ))}
            </div>
          </div>
        );

      case 'rules':
        return (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button
                onClick={() => {
                  setEditingRule(null);
                  setShowRuleModal(true);
                }}
                className="px-4 py-2 bg-amber-500 text-slate-900 rounded-lg text-sm font-medium hover:bg-amber-400 transition-colors"
              >
                创建规则
              </button>
            </div>
            <AlertRuleTable
              rules={rules}
              onEdit={handleEditRule}
              onDelete={handleDeleteRule}
              onToggle={handleToggleRule}
            />
          </div>
        );

      case 'history':
        return (
          <AlertHistoryList
            alerts={events}
            isLoading={historyLoading}
            onViewDetail={handleViewAlertDetail}
          />
        );

      case 'health':
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-slate-400">整体状态:</span>
                <span className={`text-sm font-medium ${
                  getOverallStatus() === 'healthy' ? 'text-green-400' :
                  getOverallStatus() === 'degraded' ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {getOverallStatus() === 'healthy' ? '正常' :
                   getOverallStatus() === 'degraded' ? '降级' : '故障'}
                </span>
              </div>
              <button
                onClick={() => triggerCheck()}
                disabled={isTriggering}
                className="px-4 py-2 bg-slate-700/50 text-white rounded-lg text-sm hover:bg-slate-700 transition-colors disabled:opacity-50"
              >
                {isTriggering ? '检查中...' : '手动检查'}
              </button>
            </div>
            <div className="grid grid-cols-3 gap-4">
              {checks.map((check) => (
                <HealthCheckCard
                  key={check.component}
                  check={check}
                  isChecking={isTriggering}
                />
              ))}
            </div>
          </div>
        );

      case 'channels':
        return (
          <NotificationChannelTable
            channels={channels}
            onAdd={() => {}}
            onEdit={() => {}}
            onDelete={() => {}}
            onTest={testChannel}
            isTesting={isTesting}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="border-b border-slate-700/50 bg-slate-800/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center gap-1">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors
                    ${activeTab === tab.id
                      ? 'text-amber-400 border-amber-400'
                      : 'text-slate-400 border-transparent hover:text-white hover:border-slate-600'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {renderTabContent()}
          </motion.div>
        </AnimatePresence>
      </div>

      <AlertRuleModal
        isOpen={showRuleModal}
        onClose={() => {
          setShowRuleModal(false);
          setEditingRule(null);
        }}
        onSubmit={handleCreateRule}
        rule={editingRule}
        channels={channels.map((c) => ({ id: c.id, name: c.name }))}
      />
    </div>
  );
}
