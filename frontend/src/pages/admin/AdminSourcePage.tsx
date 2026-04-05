import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';

interface SourceOverview {
  source: string;
  count: number;
  percentage: number;
}

interface SourceTrend {
  date: string;
  laohai: number;
  seo: number;
  social: number;
  direct: number;
  referral: number;
}

interface CrossAnalysis {
  objective_source: string;
  subjective_source: string;
  count: number;
}

interface SourceLog {
  id: string;
  user_id: string;
  email: string;
  source: string;
  landing_page: string;
  referrer: string;
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  created_at: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

const sourceLabels: Record<string, string> = {
  laohai: '老骇粉丝',
  seo: '搜索引擎',
  social: '社交媒体',
  direct: '直接访问',
  referral: '好友推荐',
};

const AdminSourcePage: React.FC = () => {
  const [overview, setOverview] = useState<SourceOverview[]>([]);
  const [trend, setTrend] = useState<SourceTrend[]>([]);
  const [crossAnalysis, setCrossAnalysis] = useState<CrossAnalysis[]>([]);
  const [logs, setLogs] = useState<SourceLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [dateRange, setDateRange] = useState('7d');

  useEffect(() => {
    fetchData();
  }, [dateRange]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const [overviewRes, trendRes, crossRes, logsRes] = await Promise.all([
        fetch('http://localhost:8000/api/admin/source/overview', { headers }),
        fetch(`http://localhost:8000/api/admin/source/trend?days=${dateRange === '7d' ? 7 : 30}`, { headers }),
        fetch('http://localhost:8000/api/admin/source/cross', { headers }),
        fetch('http://localhost:8000/api/admin/source/logs?limit=50', { headers }),
      ]);

      if (overviewRes.ok) {
        const data = await overviewRes.json();
        setOverview(data.sources || []);
      }
      if (trendRes.ok) {
        const data = await trendRes.json();
        setTrend(data.trend || []);
      }
      if (crossRes.ok) {
        const data = await crossRes.json();
        setCrossAnalysis(data.cross || []);
      }
      if (logsRes.ok) {
        const data = await logsRes.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Failed to fetch source data:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportCSV = () => {
    const csvContent = [
      ['用户ID', '邮箱', '来源', '着陆页', 'Referrer', 'UTM来源', 'UTM媒介', 'UTM活动', '时间'],
      ...logs.map(log => [
        log.user_id,
        log.email,
        log.source,
        log.landing_page,
        log.referrer,
        log.utm_source,
        log.utm_medium,
        log.utm_campaign,
        log.created_at,
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `source_logs_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center py-10">加载中...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">来源统计</h1>
        <div className="flex gap-2">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="7d">最近7天</option>
            <option value="30d">最近30天</option>
          </select>
          <button
            onClick={exportCSV}
            className="bg-primary text-white px-4 py-2 rounded hover:bg-primaryDark"
          >
            导出CSV
          </button>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        {['overview', 'trend', 'cross', 'logs'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded ${
              activeTab === tab ? 'bg-primary text-white' : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            {tab === 'overview' ? '概览' : tab === 'trend' ? '趋势' : tab === 'cross' ? '交叉分析' : '详细日志'}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium mb-4">来源分布</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={overview}
                  dataKey="count"
                  nameKey="source"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ source, percentage }) => `${sourceLabels[source] || source}: ${percentage}%`}
                >
                  {overview.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-medium mb-4">来源统计</h2>
            <div className="space-y-4">
              {overview.map((item, index) => (
                <div key={item.source} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span>{sourceLabels[item.source] || item.source}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-medium">{item.count}</span>
                    <span className="text-gray-500">{item.percentage}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'trend' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">来源趋势</h2>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="laohai" stroke={COLORS[0]} name="老骇粉丝" />
              <Line type="monotone" dataKey="seo" stroke={COLORS[1]} name="搜索引擎" />
              <Line type="monotone" dataKey="social" stroke={COLORS[2]} name="社交媒体" />
              <Line type="monotone" dataKey="direct" stroke={COLORS[3]} name="直接访问" />
              <Line type="monotone" dataKey="referral" stroke={COLORS[4]} name="好友推荐" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {activeTab === 'cross' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium mb-4">交叉分析（客观来源 vs 主观来源）</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客观来源</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">主观来源</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户数</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {crossAnalysis.map((item, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {sourceLabels[item.objective_source] || item.objective_source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {sourceLabels[item.subjective_source] || item.subjective_source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {item.count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">来源</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">着陆页</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">UTM</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(log.created_at).toLocaleString('zh-CN')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {log.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">
                      {sourceLabels[log.source] || log.source}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {log.landing_page}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.utm_source && (
                      <span className="text-xs">
                        {log.utm_source}/{log.utm_medium}/{log.utm_campaign}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminSourcePage;
