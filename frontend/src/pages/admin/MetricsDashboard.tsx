import React, { useEffect, useState } from 'react';

interface MetricsData {
  dau: { today: number; yesterday: number; growth: number };
  mau: number;
  new_users_today: number;
  tasks_today: number;
  reports_today: number;
  users: { total: number; paid: number; conversion_rate: number };
  retention: { '7d': number };
  nps: { avg_rating: number };
}

interface TrendItem {
  date: string;
  dau: number;
  new_users: number;
  tasks: number;
}

const MetricCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  color?: string;
  trend?: number;
}> = ({ title, value, subtitle, icon, color = '#1976d2', trend }) => (
  <div className="bg-white rounded-lg shadow p-4 h-full">
    <div className="flex justify-between items-start">
      <div>
        <p className="text-sm text-gray-500 mb-1">{title}</p>
        <p className="text-2xl font-bold" style={{ color }}>{value}</p>
        {subtitle && (
          <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
        )}
        {trend !== undefined && (
          <span className={`inline-block mt-2 px-2 py-0.5 rounded text-xs ${
            trend >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <span className="text-3xl opacity-80" style={{ color }}>{icon}</span>
    </div>
  </div>
);

const MetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [trend, setTrend] = useState<TrendItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const token = localStorage.getItem('token');
        const [metricsRes, trendRes] = await Promise.all([
          fetch('http://localhost:8000/api/metrics/dashboard', {
            headers: { 'Authorization': `Bearer ${token}` }
          }).then(r => r.json()),
          fetch('http://localhost:8000/api/metrics/trend?days=7', {
            headers: { 'Authorization': `Bearer ${token}` }
          }).then(r => r.json()),
        ]);
        setMetrics(metricsRes);
        setTrend(trendRes.trend || []);
      } catch (error) {
        console.error('获取指标失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="w-full h-1 bg-gray-200 overflow-hidden">
        <div className="h-full bg-primary animate-pulse w-full"></div>
      </div>
    );
  }

  if (!metrics) {
    return <p className="p-4 text-gray-500">无法加载指标数据</p>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">核心指标看板</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="今日活跃用户 (DAU)"
          value={metrics.dau.today}
          subtitle={`昨日: ${metrics.dau.yesterday}`}
          icon="👥"
          color="#1976d2"
          trend={metrics.dau.growth}
        />

        <MetricCard
          title="月活跃用户 (MAU)"
          value={metrics.mau}
          icon="📈"
          color="#2e7d32"
        />

        <MetricCard
          title="今日新用户"
          value={metrics.new_users_today}
          subtitle={`总用户: ${metrics.users.total}`}
          icon="👤"
          color="#ed6c02"
        />

        <MetricCard
          title="今日任务"
          value={metrics.tasks_today}
          subtitle={`报告: ${metrics.reports_today}`}
          icon="📋"
          color="#9c27b0"
        />

        <MetricCard
          title="付费用户"
          value={metrics.users.paid}
          subtitle={`转化率: ${metrics.users.conversion_rate}%`}
          icon="💰"
          color="#1976d2"
        />

        <MetricCard
          title="7日留存率"
          value={`${metrics.retention['7d']}%`}
          icon="📊"
          color="#2e7d32"
        />

        <MetricCard
          title="平均评分"
          value={metrics.nps.avg_rating}
          subtitle="用户满意度"
          icon="⭐"
          color="#ed6c02"
        />
      </div>

      <div className="bg-white rounded-lg shadow p-4 mt-6">
        <h3 className="text-lg font-medium mb-4">7日趋势</h3>
        <div className="flex gap-1 items-end h-40">
          {trend.map((item) => (
            <div
              key={item.date}
              className="flex-1 flex flex-col items-center"
            >
              <div
                className="w-full bg-primary rounded-t"
                style={{ height: Math.max(item.dau * 2, 4) }}
              />
              <span className="text-xs mt-1">{item.date.slice(5)}</span>
              <span className="text-xs text-gray-400">{item.dau}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;
