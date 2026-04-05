import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell,
} from 'recharts';
import { Activity, Clock, AlertTriangle, TrendingUp, Globe, Zap } from 'lucide-react';
import api from '@/services/api';

interface PerformanceStats {
  metric_name: string;
  avg_value: number;
  p50_value: number;
  p75_value: number;
  p95_value: number;
  p99_value: number;
  good_count: number;
  needs_improvement_count: number;
  poor_count: number;
  total_count: number;
  good_rate: number;
}

interface TrendData {
  date: string;
  avg_value: number;
  count: number;
  good_rate: number;
}

interface PagePerformance {
  url: string;
  total_requests: number;
  avg_lcp: number | null;
  avg_fid: number | null;
  avg_cls: number | null;
  poor_count: number;
}

interface Summary {
  unique_sessions_24h: number;
  total_metrics_24h: number;
  last_report: string;
  core_metrics: Record<string, Record<string, number>>;
}

const COLORS = {
  good: '#22c55e',
  'needs-improvement': '#f59e0b',
  poor: '#ef4444',
};

const METRIC_THRESHOLDS: Record<string, { good: number; poor: number; unit: string }> = {
  LCP: { good: 2500, poor: 4000, unit: 'ms' },
  FID: { good: 100, poor: 300, unit: 'ms' },
  CLS: { good: 0.1, poor: 0.25, unit: '' },
  FCP: { good: 1800, poor: 3000, unit: 'ms' },
  TTFB: { good: 800, poor: 1800, unit: 'ms' },
};

const PerformancePage: React.FC = () => {
  const [stats, setStats] = useState<PerformanceStats[]>([]);
  const [trend, setTrend] = useState<TrendData[]>([]);
  const [pages, setPages] = useState<PagePerformance[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('LCP');
  const [days, setDays] = useState(7);

  useEffect(() => {
    fetchAllData();
  }, [days, selectedMetric]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [statsRes, trendRes, pagesRes, summaryRes] = await Promise.all([
        api.get('/performance/stats?days=' + days),
        api.get(`/performance/trend?days=${days}&metric_name=${selectedMetric}`),
        api.get('/performance/pages?days=' + days),
        api.get('/performance/summary'),
      ]);

      setStats(statsRes.data);
      setTrend(trendRes.data);
      setPages(pagesRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMetricRating = (name: string, value: number): 'good' | 'needs-improvement' | 'poor' => {
    const threshold = METRIC_THRESHOLDS[name];
    if (!threshold) return 'good';
    if (value <= threshold.good) return 'good';
    if (value <= threshold.poor) return 'needs-improvement';
    return 'poor';
  };

  const pieData = stats.map((s) => ({
    name: s.metric_name,
    good: s.good_count,
    needsImprovement: s.needs_improvement_count,
    poor: s.poor_count,
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">性能监控</h1>
        <div className="flex gap-4">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg"
          >
            <option value={1}>最近1天</option>
            <option value={7}>最近7天</option>
            <option value={14}>最近14天</option>
            <option value={30}>最近30天</option>
          </select>
          <button
            onClick={fetchAllData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            刷新
          </button>
        </div>
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-gray-500">24小时会话</span>
            </div>
            <p className="text-2xl font-bold mt-1">{summary.unique_sessions_24h}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-green-600" />
              <span className="text-sm text-gray-500">指标总数</span>
            </div>
            <p className="text-2xl font-bold mt-1">{summary.total_metrics_24h}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-yellow-600" />
              <span className="text-sm text-gray-500">最后上报</span>
            </div>
            <p className="text-sm font-medium mt-1">
              {summary.last_report ? new Date(summary.last_report).toLocaleString() : '-'}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-600" />
              <span className="text-sm text-gray-500">核心指标</span>
            </div>
            <p className="text-sm font-medium mt-1">{Object.keys(summary.core_metrics).length} 个</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">核心指标趋势</h2>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="LCP">LCP (最大内容绘制)</option>
            <option value="FID">FID (首次输入延迟)</option>
            <option value="CLS">CLS (累积布局偏移)</option>
            <option value="FCP">FCP (首次内容绘制)</option>
            <option value="TTFB">TTFB (首字节时间)</option>
          </select>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="avg_value" stroke="#3b82f6" name="平均值" />
            <Line type="monotone" dataKey="good_rate" stroke="#22c55e" name="良好率" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">指标统计</h2>
          <div className="space-y-4">
            {stats.map((stat) => (
              <div key={stat.metric_name} className="border-b pb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">{stat.metric_name}</span>
                  <span
                    className="px-2 py-1 rounded text-sm"
                    style={{
                      backgroundColor:
                        stat.good_rate > 0.75
                          ? COLORS.good + '20'
                          : stat.good_rate > 0.5
                          ? COLORS['needs-improvement'] + '20'
                          : COLORS.poor + '20',
                      color:
                        stat.good_rate > 0.75
                          ? COLORS.good
                          : stat.good_rate > 0.5
                          ? COLORS['needs-improvement']
                          : COLORS.poor,
                    }}
                  >
                    良好率: {(stat.good_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-2 text-sm text-gray-600">
                  <div>
                    <span className="block text-gray-400">平均</span>
                    {stat.avg_value.toFixed(2)}
                    {METRIC_THRESHOLDS[stat.metric_name]?.unit}
                  </div>
                  <div>
                    <span className="block text-gray-400">P50</span>
                    {stat.p50_value.toFixed(2)}
                  </div>
                  <div>
                    <span className="block text-gray-400">P95</span>
                    {stat.p95_value.toFixed(2)}
                  </div>
                  <div>
                    <span className="block text-gray-400">P99</span>
                    {stat.p99_value.toFixed(2)}
                  </div>
                </div>
                <div className="flex gap-1 mt-2 h-2 rounded overflow-hidden bg-gray-100">
                  <div
                    className="bg-green-500"
                    style={{ width: `${(stat.good_count / stat.total_count) * 100}%` }}
                  />
                  <div
                    className="bg-yellow-500"
                    style={{
                      width: `${(stat.needs_improvement_count / stat.total_count) * 100}%`,
                    }}
                  />
                  <div
                    className="bg-red-500"
                    style={{ width: `${(stat.poor_count / stat.total_count) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">页面性能排名</h2>
          <div className="space-y-3">
            {pages.slice(0, 10).map((page, index) => (
              <div key={page.url} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-400 w-6">{index + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{page.url}</p>
                  <div className="flex gap-4 text-xs text-gray-500 mt-1">
                    {page.avg_lcp && (
                      <span
                        style={{
                          color: COLORS[getMetricRating('LCP', page.avg_lcp)],
                        }}
                      >
                        LCP: {page.avg_lcp.toFixed(0)}ms
                      </span>
                    )}
                    {page.avg_fid && (
                      <span
                        style={{
                          color: COLORS[getMetricRating('FID', page.avg_fid)],
                        }}
                      >
                        FID: {page.avg_fid.toFixed(0)}ms
                      </span>
                    )}
                    {page.avg_cls && (
                      <span
                        style={{
                          color: COLORS[getMetricRating('CLS', page.avg_cls)],
                        }}
                      >
                        CLS: {page.avg_cls.toFixed(3)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm text-gray-600">{page.total_requests} 次</span>
                  {page.poor_count > 0 && (
                    <p className="text-xs text-red-600">{page.poor_count} 差评</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">指标分布</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={pieData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="good" stackId="a" fill={COLORS.good} name="良好" />
            <Bar
              dataKey="needsImprovement"
              stackId="a"
              fill={COLORS['needs-improvement']}
              name="需改进"
            />
            <Bar dataKey="poor" stackId="a" fill={COLORS.poor} name="差" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-semibold text-blue-800 mb-2">Web Vitals 说明</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-700">
          <div>
            <strong>LCP (最大内容绘制)</strong>
            <p>衡量页面主要内容加载速度。良好 &lt; 2.5s</p>
          </div>
          <div>
            <strong>FID (首次输入延迟)</strong>
            <p>衡量交互响应速度。良好 &lt; 100ms</p>
          </div>
          <div>
            <strong>CLS (累积布局偏移)</strong>
            <p>衡量视觉稳定性。良好 &lt; 0.1</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformancePage;
