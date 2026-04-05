import React, { useState, useEffect, useCallback } from 'react';
import {
  ServerIcon,
  CpuChipIcon,
  CircleStackIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  PlayIcon,
  ChartBarIcon,
  BellIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';
import toast from '@/utils/toast';

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
}

interface DatabaseMetrics {
  size_mb: number;
  table_count: number;
  slow_queries: number;
}

interface TaskMetrics {
  pending: number;
  running: number;
  completed_today: number;
  failed_today: number;
}

interface AgentMetrics {
  total: number;
  active: number;
  idle: number;
  departments: number;
}

interface Alert {
  id: number;
  type: string;
  severity: string;
  message: string;
  status: string;
  created_at: string;
}

interface TaskInfo {
  task_id: string;
  name: string;
  status: string;
  worker?: string;
}

const OpsDashboardPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'tasks' | 'alerts' | 'agents'>('overview');
  
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [databaseMetrics, setDatabaseMetrics] = useState<DatabaseMetrics | null>(null);
  const [taskMetrics, setTaskMetrics] = useState<TaskMetrics | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [tasks, setTasks] = useState<{ scheduled: TaskInfo[]; running: TaskInfo[] }>({
    scheduled: [],
    running: [],
  });
  const [uptime, setUptime] = useState(0);

  const loadOverview = useCallback(async () => {
    try {
      const response = await api.get('/admin/ops/overview');
      setSystemMetrics(response.data.system);
      setDatabaseMetrics(response.data.database);
      setTaskMetrics(response.data.tasks);
      setAgentMetrics(response.data.agents);
      setUptime(response.data.uptime_seconds);
    } catch (error) {
      console.error('Failed to load overview:', error);
    }
  }, []);

  const loadAlerts = useCallback(async () => {
    try {
      const response = await api.get('/admin/ops/alerts?hours=24');
      setAlerts([...response.data.active, ...response.data.history].slice(0, 20));
    } catch (error) {
      console.error('Failed to load alerts:', error);
    }
  }, []);

  const loadTasks = useCallback(async () => {
    try {
      const response = await api.get('/admin/ops/tasks');
      setTasks({
        scheduled: response.data.scheduled || [],
        running: response.data.running || [],
      });
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([loadOverview(), loadAlerts(), loadTasks()]);
    } finally {
      setRefreshing(false);
    }
  }, [loadOverview, loadAlerts, loadTasks]);

  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      await refreshAll();
      setIsLoading(false);
    };
    init();

    const interval = setInterval(refreshAll, 30000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  const triggerTask = async (taskName: string) => {
    try {
      const response = await api.post('/admin/ops/tasks/trigger', {
        task_name: taskName,
      });
      toast.success(`任务已触发: ${response.data.task_id}`);
      loadTasks();
    } catch (error) {
      toast.error('触发任务失败');
    }
  };

  const resolveAlert = async (alertId: number) => {
    try {
      await api.post(`/admin/ops/alerts/${alertId}/resolve`);
      toast.success('告警已解决');
      loadAlerts();
    } catch (error) {
      toast.error('解决告警失败');
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${days}天 ${hours}时 ${mins}分`;
  };

  const getStatusColor = (value: number, thresholds: [number, number]) => {
    if (value < thresholds[0]) return 'text-green-500';
    if (value < thresholds[1]) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-blue-100 text-blue-800';
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="CPU 使用率"
          value={systemMetrics?.cpu_usage || 0}
          unit="%"
          icon={<CpuChipIcon className="w-6 h-6" />}
          colorClass={getStatusColor(systemMetrics?.cpu_usage || 0, [70, 90])}
        />
        <MetricCard
          title="内存使用率"
          value={systemMetrics?.memory_usage || 0}
          unit="%"
          icon={<ServerIcon className="w-6 h-6" />}
          colorClass={getStatusColor(systemMetrics?.memory_usage || 0, [80, 95])}
        />
        <MetricCard
          title="磁盘使用率"
          value={systemMetrics?.disk_usage || 0}
          unit="%"
          icon={<CircleStackIcon className="w-6 h-6" />}
          colorClass={getStatusColor(systemMetrics?.disk_usage || 0, [80, 95])}
        />
        <MetricCard
          title="运行时间"
          value={formatUptime(uptime)}
          unit=""
          icon={<ClockIcon className="w-6 h-6" />}
          colorClass="text-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">数据库状态</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">数据库大小</span>
              <span className="font-medium">{databaseMetrics?.size_mb || 0} MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">表数量</span>
              <span className="font-medium">{databaseMetrics?.table_count || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">慢查询 (1h)</span>
              <span className={`font-medium ${databaseMetrics?.slow_queries ? 'text-yellow-500' : 'text-green-500'}`}>
                {databaseMetrics?.slow_queries || 0}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">智能体状态</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">总智能体数</span>
              <span className="font-medium">{agentMetrics?.total || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">活跃智能体</span>
              <span className="font-medium text-green-500">{agentMetrics?.active || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">空闲智能体</span>
              <span className="font-medium text-gray-400">{agentMetrics?.idle || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">部门数量</span>
              <span className="font-medium">{agentMetrics?.departments || 0}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">快速操作</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <QuickActionButton
            label="训练任务"
            onClick={() => triggerTask('self_play_training')}
            icon={<PlayIcon className="w-4 h-4" />}
          />
          <QuickActionButton
            label="数据聚合"
            onClick={() => triggerTask('aggregate_stats')}
            icon={<ChartBarIcon className="w-4 h-4" />}
          />
          <QuickActionButton
            label="记忆整理"
            onClick={() => triggerTask('memory_consolidation')}
            icon={<CogIcon className="w-4 h-4" />}
          />
          <QuickActionButton
            label="健康检查"
            onClick={() => triggerTask('health_check')}
            icon={<CheckCircleIcon className="w-4 h-4" />}
          />
        </div>
      </div>
    </div>
  );

  const renderTasks = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">运行中的任务</h3>
          {tasks.running.length === 0 ? (
            <p className="text-gray-500 text-center py-4">暂无运行中的任务</p>
          ) : (
            <div className="space-y-3">
              {tasks.running.map((task) => (
                <div key={task.task_id} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{task.name}</p>
                    <p className="text-xs text-gray-500">{task.task_id}</p>
                  </div>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                    运行中
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">计划任务</h3>
          {tasks.scheduled.length === 0 ? (
            <p className="text-gray-500 text-center py-4">暂无计划任务</p>
          ) : (
            <div className="space-y-3">
              {tasks.scheduled.map((task) => (
                <div key={task.task_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{task.name}</p>
                    <p className="text-xs text-gray-500">{task.eta}</p>
                  </div>
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
                    待执行
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">手动触发任务</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          <TaskTriggerButton
            label="自博弈训练"
            taskName="self_play_training"
            onTrigger={triggerTask}
          />
          <TaskTriggerButton
            label="防御统计聚合"
            taskName="aggregate_stats"
            onTrigger={triggerTask}
          />
          <TaskTriggerButton
            label="记忆整理"
            taskName="memory_consolidation"
            onTrigger={triggerTask}
          />
          <TaskTriggerButton
            label="数据库备份"
            taskName="database_backup"
            onTrigger={triggerTask}
          />
          <TaskTriggerButton
            label="健康检查"
            taskName="health_check"
            onTrigger={triggerTask}
          />
        </div>
      </div>
    </div>
  );

  const renderAlerts = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">告警列表 (24h)</h3>
      {alerts.length === 0 ? (
        <div className="text-center py-8">
          <CheckCircleIcon className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <p className="text-gray-500">暂无告警</p>
        </div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence>
            {alerts.map((alert) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
                  <div>
                    <p className="font-medium text-sm">{alert.message}</p>
                    <p className="text-xs text-gray-500">
                      {alert.type} · {new Date(alert.created_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${getSeverityColor(alert.severity)}`}>
                    {alert.severity}
                  </span>
                  {alert.status === 'active' && (
                    <button
                      onClick={() => resolveAlert(alert.id)}
                      className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                      解决
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );

  const renderAgents = () => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">智能体状态</h3>
      <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
        {['吏部', '户部', '礼部', '兵部', '刑部', '工部', '攻击', '防御', '记忆'].map((dept, idx) => (
          <div key={dept} className="text-center p-4 bg-gray-50 rounded-lg">
            <div className={`w-12 h-12 mx-auto mb-2 rounded-full flex items-center justify-center ${
              idx < 6 ? 'bg-blue-100 text-blue-600' : 
              idx < 8 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
            }`}>
              {dept[0]}
            </div>
            <p className="text-sm font-medium">{dept}</p>
            <p className="text-xs text-gray-500">
              {Math.random() > 0.3 ? '活跃' : '空闲'}
            </p>
          </div>
        ))}
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <ArrowPathIcon className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <ServerIcon className="w-8 h-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">运维监控中心</h1>
          </div>
          <button
            onClick={refreshAll}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            刷新
          </button>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="flex border-b border-gray-200">
            {[
              { key: 'overview', label: '概览', icon: <ChartBarIcon className="w-4 h-4" /> },
              { key: 'tasks', label: '任务', icon: <CogIcon className="w-4 h-4" /> },
              { key: 'alerts', label: '告警', icon: <BellIcon className="w-4 h-4" /> },
              { key: 'agents', label: '智能体', icon: <ServerIcon className="w-4 h-4" /> },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium ${
                  activeTab === tab.key
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'tasks' && renderTasks()}
            {activeTab === 'alerts' && renderAlerts()}
            {activeTab === 'agents' && renderAgents()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: number | string;
  unit: string;
  icon: React.ReactNode;
  colorClass: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, unit, icon, colorClass }) => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div className="flex items-center justify-between mb-2">
      <span className="text-gray-500 text-sm">{title}</span>
      <div className={`${colorClass}`}>{icon}</div>
    </div>
    <div className={`text-2xl font-bold ${colorClass}`}>
      {value}{unit}
    </div>
  </div>
);

interface QuickActionButtonProps {
  label: string;
  onClick: () => void;
  icon: React.ReactNode;
}

const QuickActionButton: React.FC<QuickActionButtonProps> = ({ label, onClick, icon }) => (
  <button
    onClick={onClick}
    className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
  >
    {icon}
    {label}
  </button>
);

interface TaskTriggerButtonProps {
  label: string;
  taskName: string;
  onTrigger: (taskName: string) => void;
}

const TaskTriggerButton: React.FC<TaskTriggerButtonProps> = ({ label, taskName, onTrigger }) => {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      await onTrigger(taskName);
    } finally {
      setTimeout(() => setLoading(false), 1000);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-colors"
    >
      {loading ? (
        <ArrowPathIcon className="w-4 h-4 animate-spin" />
      ) : (
        <PlayIcon className="w-4 h-4" />
      )}
      {label}
    </button>
  );
};

export default OpsDashboardPage;
