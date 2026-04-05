import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

interface OverviewData {
  dau_today: number;
  dau_yesterday: number;
  mau: number;
  total_events: number;
  tasks_created_today: number;
  new_users_today: number;
  logins_today: number;
}

interface EventData {
  id: string;
  user_id: string | null;
  session_id: string;
  event_type: string;
  page_url: string;
  element_id: string | null;
  properties: Record<string, any>;
  ip_address: string | null;
  created_at: string;
}

interface TrendData {
  date: string;
  dau: number;
  events: number;
}

interface EventTypeStats {
  event_type: string;
  count: number;
}

const StatCard: React.FC<{
  title: string;
  value: number | string;
  icon: string;
  color: string;
}> = ({ title, value, icon, color }) => (
  <div className="bg-white rounded-lg shadow p-4 h-full">
    <div className="flex items-center mb-2">
      <span className="text-xl mr-2" style={{ color }}>{icon}</span>
      <span className="text-sm text-gray-500">{title}</span>
    </div>
    <div className="text-2xl font-bold">
      {typeof value === 'number' ? value.toLocaleString() : value}
    </div>
  </div>
);

const AdminAnalyticsPage: React.FC = () => {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [events, setEvents] = useState<EventData[]>([]);
  const [trend, setTrend] = useState<TrendData[]>([]);
  const [eventTypes, setEventTypes] = useState<EventTypeStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalEvents, setTotalEvents] = useState(0);
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('');

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [page, rowsPerPage, eventTypeFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const [overviewRes, trendRes, typesRes] = await Promise.all([
        fetch('http://localhost:8000/api/admin/analytics/overview', { headers }).then(r => r.json()),
        fetch('http://localhost:8000/api/admin/analytics/trend?days=7', { headers }).then(r => r.json()),
        fetch('http://localhost:8000/api/admin/analytics/event-types', { headers }).then(r => r.json()),
      ]);
      
      setOverview(overviewRes);
      setTrend(trendRes.trend || []);
      setEventTypes(typesRes.event_types || []);
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvents = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page: (page + 1).toString(),
        page_size: rowsPerPage.toString(),
      });
      
      if (eventTypeFilter) {
        params.append('event_type', eventTypeFilter);
      }
      
      const res = await fetch(`http://localhost:8000/api/admin/analytics/events?${params}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      const data = await res.json();
      setEvents(data.events || []);
      setTotalEvents(data.total || 0);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    }
  };

  const getEventColor = (eventType: string): string => {
    const colors: Record<string, string> = {
      page_view: 'bg-blue-100 text-blue-700',
      button_click: 'bg-green-100 text-green-700',
      task_create: 'bg-yellow-100 text-yellow-700',
      report_view: 'bg-purple-100 text-purple-700',
      login: 'bg-pink-100 text-pink-700',
      register: 'bg-red-100 text-red-700',
    };
    return colors[eventType] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">数据分析</h1>

      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="今日活跃用户"
            value={overview.dau_today}
            icon="👥"
            color="#1976d2"
          />
          <StatCard
            title="月活跃用户"
            value={overview.mau}
            icon="📈"
            color="#2e7d32"
          />
          <StatCard
            title="今日新建任务"
            value={overview.tasks_created_today}
            icon="📋"
            color="#ed6c02"
          />
          <StatCard
            title="总事件数"
            value={overview.total_events}
            icon="📊"
            color="#9c27b0"
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-medium mb-4">用户活跃趋势</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="dau" stroke="#1976d2" name="DAU" />
              <Line type="monotone" dataKey="events" stroke="#2e7d32" name="事件数" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-medium mb-4">事件类型分布</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={eventTypes.slice(0, 8)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="event_type" type="category" width={80} />
              <Tooltip />
              <Bar dataKey="count" fill="#1976d2" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4 mt-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">事件记录</h3>
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1 text-sm"
          >
            <option value="">全部事件类型</option>
            {eventTypes.map((type) => (
              <option key={type.event_type} value={type.event_type}>
                {type.event_type}
              </option>
            ))}
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left py-2 px-3">时间</th>
                <th className="text-left py-2 px-3">事件类型</th>
                <th className="text-left py-2 px-3">用户ID</th>
                <th className="text-left py-2 px-3">页面</th>
                <th className="text-left py-2 px-3">元素</th>
                <th className="text-left py-2 px-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-3">
                    {new Date(event.created_at).toLocaleString('zh-CN')}
                  </td>
                  <td className="py-2 px-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${getEventColor(event.event_type)}`}>
                      {event.event_type}
                    </span>
                  </td>
                  <td className="py-2 px-3">{event.user_id || '匿名'}</td>
                  <td className="py-2 px-3">{event.page_url}</td>
                  <td className="py-2 px-3">{event.element_id || '-'}</td>
                  <td className="py-2 px-3">{event.ip_address || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">每页行数:</span>
            <select
              value={rowsPerPage}
              onChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, totalEvents)} 共 {totalEvents} 条
            </span>
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
            >
              上一页
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * rowsPerPage >= totalEvents}
              className="px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminAnalyticsPage;
