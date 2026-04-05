import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface DefenseStats {
  total_attacks: number;
  blocked_attacks: number;
  missed_attacks: number;
  false_positives: number;
  normal_requests: number;
  service_down_events: number;
  block_rate: number;
  miss_rate: number;
  false_positive_rate: number;
  service_availability: number;
}

interface TrainingProgress {
  total_episodes: number;
  best_win_rate: number;
  avg_reward: number;
  model_version: number;
}

interface SystemMetrics {
  cpu_usage_percent: number;
  memory_usage_bytes: number;
  disk_usage_percent: number;
  active_workers: number;
  pending_tasks: number;
}

interface Alert {
  id: number;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  is_resolved: boolean;
  created_at: string;
}

export const MonitoringDashboard: React.FC = () => {
  const [defenseStats, setDefenseStats] = useState<DefenseStats | null>(null);
  const [trainingProgress, setTrainingProgress] = useState<TrainingProgress | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const fetchDashboardData = async () => {
    try {
      const [defenseRes, trainingRes, metricsRes, alertsRes] = await Promise.all([
        fetch('/api/reports/defense/summary').then(r => r.json()),
        fetch('/api/reports/training/progress').then(r => r.json()),
        fetch('/api/reports/resource/usage').then(r => r.json()),
        fetch('/api/reports/alerts').then(r => r.json())
      ]);

      setDefenseStats(defenseRes);
      if (trainingRes.progress && trainingRes.progress.length > 0) {
        setTrainingProgress(trainingRes.progress[0]);
      }
      if (metricsRes.usage && metricsRes.usage.length > 0) {
        setSystemMetrics(metricsRes.usage[0]);
      }
      setAlerts(alertsRes.alerts || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const resolveAlert = async (alertId: number) => {
    try {
      await fetch(`/api/reports/alerts/${alertId}/resolve`, { method: 'POST' });
      setAlerts(alerts.filter(a => a.id !== alertId));
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">系统监控仪表盘</h1>
        <div className="flex items-center space-x-4">
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="border rounded px-3 py-1"
          >
            <option value={10}>10秒刷新</option>
            <option value={30}>30秒刷新</option>
            <option value={60}>1分钟刷新</option>
            <option value={300}>5分钟刷新</option>
          </select>
          <Button onClick={fetchDashboardData}>刷新数据</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">攻击拦截率</h3>
          <p className="text-3xl font-bold text-green-600">
            {defenseStats ? `${(defenseStats.block_rate * 100).toFixed(1)}%` : 'N/A'}
          </p>
          <p className="text-sm text-gray-400">
            已拦截 {defenseStats?.blocked_attacks || 0} / {defenseStats?.total_attacks || 0} 次
          </p>
        </Card>

        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">误判率</h3>
          <p className="text-3xl font-bold text-blue-600">
            {defenseStats ? `${(defenseStats.false_positive_rate * 100).toFixed(2)}%` : 'N/A'}
          </p>
          <p className="text-sm text-gray-400">
            目标 &lt; 1%
          </p>
        </Card>

        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">服务可用性</h3>
          <p className="text-3xl font-bold text-purple-600">
            {defenseStats ? `${(defenseStats.service_availability * 100).toFixed(2)}%` : 'N/A'}
          </p>
          <p className="text-sm text-gray-400">
            目标 99.9%
          </p>
        </Card>

        <Card className="p-4">
          <h3 className="text-sm font-medium text-gray-500">模型版本</h3>
          <p className="text-3xl font-bold text-orange-600">
            v{trainingProgress?.model_version || 0}
          </p>
          <p className="text-sm text-gray-400">
            胜率 {trainingProgress ? `${(trainingProgress.best_win_rate * 100).toFixed(1)}%` : 'N/A'}
          </p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">防御性能指标</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">总攻击数</span>
              <span className="font-semibold">{defenseStats?.total_attacks || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">已拦截攻击</span>
              <span className="font-semibold text-green-600">{defenseStats?.blocked_attacks || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">漏拦截攻击</span>
              <span className="font-semibold text-red-600">{defenseStats?.missed_attacks || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">误判数</span>
              <span className="font-semibold text-yellow-600">{defenseStats?.false_positives || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">正常请求</span>
              <span className="font-semibold">{defenseStats?.normal_requests || 0}</span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">系统资源</h2>
          {systemMetrics && (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-600">CPU 使用率</span>
                  <span className="font-semibold">{systemMetrics.cpu_usage_percent?.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${Math.min(systemMetrics.cpu_usage_percent || 0, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-600">内存使用</span>
                  <span className="font-semibold">
                    {((systemMetrics.memory_usage_bytes || 0) / 1024 / 1024 / 1024).toFixed(2)} GB
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${Math.min(systemMetrics.disk_usage_percent || 0, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-600">磁盘使用率</span>
                  <span className="font-semibold">{systemMetrics.disk_usage_percent?.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full"
                    style={{ width: `${Math.min(systemMetrics.disk_usage_percent || 0, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="text-center p-2 bg-gray-50 rounded">
                  <p className="text-2xl font-bold text-blue-600">{systemMetrics.active_workers || 0}</p>
                  <p className="text-sm text-gray-500">活跃Worker</p>
                </div>
                <div className="text-center p-2 bg-gray-50 rounded">
                  <p className="text-2xl font-bold text-orange-600">{systemMetrics.pending_tasks || 0}</p>
                  <p className="text-sm text-gray-500">待处理任务</p>
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>

      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">系统告警</h2>
          <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-sm">
            {alerts.filter(a => !a.is_resolved).length} 个活跃告警
          </span>
        </div>
        
        {alerts.length === 0 ? (
          <p className="text-gray-500 text-center py-4">暂无告警</p>
        ) : (
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${
                  alert.severity === 'critical' ? 'border-red-300 bg-red-50' :
                  alert.severity === 'warning' ? 'border-yellow-300 bg-yellow-50' :
                  'border-blue-300 bg-blue-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        alert.severity === 'critical' ? 'bg-red-200 text-red-800' :
                        alert.severity === 'warning' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-blue-200 text-blue-800'
                      }`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span className="font-medium">{alert.title}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!alert.is_resolved && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => resolveAlert(alert.id)}
                    >
                      解决
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">训练进度</h2>
          {trainingProgress && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">总训练轮次</span>
                <span className="font-semibold">{trainingProgress.total_episodes}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">最佳胜率</span>
                <span className="font-semibold text-green-600">
                  {(trainingProgress.best_win_rate * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">平均奖励</span>
                <span className="font-semibold">{trainingProgress.avg_reward?.toFixed(2)}</span>
              </div>
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">快速操作</h2>
          <div className="space-y-2">
            <Button className="w-full" onClick={() => fetch('/api/selfplay/train', { method: 'POST' })}>
              启动训练任务
            </Button>
            <Button className="w-full" variant="outline" onClick={() => fetch('/api/reports/export')}>
              导出报表
            </Button>
            <Button className="w-full" variant="outline" onClick={() => fetch('/api/backup/create', { method: 'POST' })}>
              创建备份
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">系统状态</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">API服务</span>
              <span className="flex items-center text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                正常
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">数据库</span>
              <span className="flex items-center text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                正常
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Redis</span>
              <span className="flex items-center text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                正常
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Celery</span>
              <span className="flex items-center text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                正常
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default MonitoringDashboard;
