import React, { useState, useEffect, useCallback } from 'react';
import {
  UsersIcon,
  ClipboardDocumentListIcon,
  DocumentTextIcon,
  TeamIcon,
  ArrowDownTrayIcon,
  ArrowPathIcon,
  ComputerDesktopIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { adminStatsApi, OverviewStats, UserGrowthItem, TaskStats, SystemHealth } from '@/api/admin/stats';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.FC<{ className?: string }>;
  color: string;
  subtitle?: string;
  trend?: number;
}> = ({ title, value, icon: Icon, color, subtitle, trend }) => (
  <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
        {subtitle && (
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{subtitle}</p>
        )}
      </div>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
    </div>
    {trend !== undefined && (
      <div className={`mt-2 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
        {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% 较上周
      </div>
    )}
  </div>
);

const HealthBar: React.FC<{
  label: string;
  percent: number;
  color: string;
}> = ({ label, percent, color }) => (
  <div className="flex items-center gap-3">
    <span className="text-sm text-gray-600 dark:text-gray-400 w-16">{label}</span>
    <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
      <div
        className={`h-full ${color} rounded-full transition-all duration-500`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
    <span className="text-sm font-medium text-gray-900 dark:text-white w-12 text-right">
      {percent.toFixed(1)}%
    </span>
  </div>
);

const StatsPage: React.FC = () => {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [userGrowth, setUserGrowth] = useState<UserGrowthItem[]>([]);
  const [taskStats, setTaskStats] = useState<TaskStats | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7' | '30' | '90'>('7');
  const [autoRefresh, setAutoRefresh] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - parseInt(timeRange) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

      const [overviewRes, userGrowthRes, taskStatsRes, healthRes] = await Promise.all([
        adminStatsApi.getOverview(),
        adminStatsApi.getUserGrowth({ start_date: startDate, end_date: endDate }),
        adminStatsApi.getTaskStats({ start_date: startDate, end_date: endDate }),
        adminStatsApi.getSystemHealth(),
      ]);

      setOverview(overviewRes);
      setUserGrowth(userGrowthRes);
      setTaskStats(taskStatsRes);
      setHealth(healthRes);
    } catch {
      showToast.error('加载统计数据失败');
    } finally {
      setIsLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadData]);

  const handleExport = async (type: 'overview' | 'users' | 'tasks') => {
    try {
      const blob = await adminStatsApi.exportCsv(type);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_stats_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      showToast.success('导出成功');
    } catch {
      showToast.error('导出失败');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 dark:text-green-400';
      case 'warning': return 'text-yellow-600 dark:text-yellow-400';
      case 'degraded': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getHealthBarColor = (percent: number) => {
    if (percent > 80) return 'bg-red-500';
    if (percent > 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const pieData = taskStats?.by_status
    ? Object.entries(taskStats.by_status).map(([name, value]) => ({ name, value }))
    : [];

  if (isLoading) {
    return <LoadingCard message="加载统计数据..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">统计分析</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">系统运行状态和数据统计</p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Time Range */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300"
          >
            <option value="7">最近7天</option>
            <option value="30">最近30天</option>
            <option value="90">最近90天</option>
          </select>

          {/* Auto Refresh */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors ${
              autoRefresh
                ? 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800 text-green-600 dark:text-green-400'
                : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'
            }`}
          >
            <ArrowPathIcon className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            自动刷新
          </button>

          <button
            onClick={loadData}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <ArrowPathIcon className="w-4 h-4" />
            刷新
          </button>
        </div>
      </div>

      {/* Overview Stats */}
      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="总用户数"
            value={overview.total_users}
            icon={UsersIcon}
            color="bg-blue-500"
            subtitle={`${overview.active_users} 活跃`}
          />
          <StatCard
            title="今日新增用户"
            value={overview.new_users_today}
            icon={UsersIcon}
            color="bg-green-500"
            subtitle={`本周 ${overview.new_users_week}`}
          />
          <StatCard
            title="总任务数"
            value={overview.total_tasks}
            icon={ClipboardDocumentListIcon}
            color="bg-purple-500"
            subtitle={`${overview.completed_tasks} 已完成`}
          />
          <StatCard
            title="总报告数"
            value={overview.total_reports}
            icon={DocumentTextIcon}
            color="bg-orange-500"
            subtitle={`${overview.total_teams} 团队`}
          />
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">用户增长趋势</h3>
          {userGrowth.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={userGrowth}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
                <XAxis 
                  dataKey="period" 
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                  tickFormatter={(value) => value.slice(5)}
                />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1f2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="new_users"
                  name="新增用户"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-400">
              暂无数据
            </div>
          )}
        </div>

        {/* Task Stats Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">任务统计</h3>
          {taskStats && taskStats.by_period.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={taskStats.by_period}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
                <XAxis 
                  dataKey="period" 
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                  tickFormatter={(value) => value.slice(5)}
                />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1f2937', 
                    border: 'none', 
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Legend />
                <Bar dataKey="total" name="总数" fill="#3b82f6" />
                <Bar dataKey="completed" name="完成" fill="#10b981" />
                <Bar dataKey="failed" name="失败" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-400">
              暂无数据
            </div>
          )}
        </div>
      </div>

      {/* Task Status Pie & System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Task Status Pie */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">任务状态分布</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-400">
              暂无数据
            </div>
          )}
        </div>

        {/* System Health */}
        {health && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">系统健康状态</h3>
              <span className={`text-sm font-medium ${getStatusColor(health.status)}`}>
                {health.status === 'healthy' ? '正常' : health.status === 'warning' ? '警告' : '异常'}
              </span>
            </div>
            
            <div className="space-y-4">
              {health.cpu.percent !== undefined && (
                <HealthBar
                  label="CPU"
                  percent={health.cpu.percent}
                  color={getHealthBarColor(health.cpu.percent)}
                />
              )}
              
              {health.memory.percent !== undefined && (
                <HealthBar
                  label="内存"
                  percent={health.memory.percent}
                  color={getHealthBarColor(health.memory.percent)}
                />
              )}
              
              {health.disk.percent !== undefined && (
                <HealthBar
                  label="磁盘"
                  percent={health.disk.percent}
                  color={getHealthBarColor(health.disk.percent)}
                />
              )}
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6 pt-4 border-t border-gray-100 dark:border-gray-700">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">CPU核心</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{health.cpu.count || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">内存使用</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {health.memory.used_mb?.toFixed(0) || '-'} / {health.memory.total_mb?.toFixed(0) || '-'} MB
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">磁盘使用</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {health.disk.used_gb?.toFixed(1) || '-'} / {health.disk.total_gb?.toFixed(1) || '-'} GB
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">数据库响应</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {health.database.response_time_ms?.toFixed(0) || '-'} ms
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Export */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">导出数据</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleExport('overview')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            导出概览
          </button>
          <button
            onClick={() => handleExport('users')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            导出用户统计
          </button>
          <button
            onClick={() => handleExport('tasks')}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            导出任务统计
          </button>
        </div>
      </div>
    </div>
  );
};

export default StatsPage;
