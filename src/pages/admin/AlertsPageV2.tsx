import React, { useState, useEffect } from 'react';
import {
  AlertTriangle, Bell, CheckCircle, XCircle, Clock,
  Filter, RefreshCw, AlertCircle, ChevronDown,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

interface Alert {
  id: number;
  alertname: string;
  status: string;
  severity: string;
  message: string;
  summary: string | null;
  starts_at: string | null;
  ends_at: string | null;
  fingerprint: string | null;
  labels: Record<string, string>;
  annotations: Record<string, string>;
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  note: string | null;
}

interface AlertStats {
  total: number;
  by_status: {
    firing: number;
    resolved: number;
    acknowledged: number;
  };
  by_severity: {
    critical: number;
    warning: number;
  };
  top_alerts: Array<{ name: string; count: number }>;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
};

const STATUS_COLORS: Record<string, string> = {
  firing: 'bg-red-500',
  resolved: 'bg-green-500',
  acknowledged: 'bg-blue-500',
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  firing: <AlertTriangle className="w-4 h-4 text-red-500" />,
  resolved: <CheckCircle className="w-4 h-4 text-green-500" />,
  acknowledged: <Bell className="w-4 h-4 text-blue-500" />,
};

const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('');
  const [severity, setSeverity] = useState('');
  const [days, setDays] = useState(7);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [acknowledgeNote, setAcknowledgeNote] = useState('');

  useEffect(() => {
    fetchAlerts();
    fetchStats();
  }, [days, status, severity]);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('days', days.toString());
      if (status) params.append('status', status);
      if (severity) params.append('severity', severity);

      const response = await fetch(`/api/alerts/history?${params}`);
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`/api/alerts/stats?days=${days}`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const acknowledgeAlert = async (alertId: number) => {
    try {
      const response = await fetch(`/api/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          acknowledged_by: 'admin',
          note: acknowledgeNote,
        }),
      });

      if (response.ok) {
        fetchAlerts();
        fetchStats();
        setSelectedAlert(null);
        setAcknowledgeNote('');
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const sendTestAlert = async () => {
    try {
      await fetch('/api/alerts/test', { method: 'POST' });
      alert('测试告警已发送');
    } catch (error) {
      console.error('Failed to send test alert:', error);
    }
  };

  const formatTime = (time: string | null) => {
    if (!time) return '-';
    return new Date(time).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">告警管理</h1>
        <div className="flex gap-2">
          <button
            onClick={sendTestAlert}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            发送测试告警
          </button>
          <button
            onClick={() => {
              fetchAlerts();
              fetchStats();
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">总告警数</p>
            <p className="text-2xl font-bold">{stats.total}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <p className="text-sm text-gray-500">触发中</p>
            </div>
            <p className="text-2xl font-bold text-red-600">{stats.by_status.firing}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <p className="text-sm text-gray-500">已解决</p>
            </div>
            <p className="text-2xl font-bold text-green-600">{stats.by_status.resolved}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <p className="text-sm text-gray-500">已确认</p>
            </div>
            <p className="text-2xl font-bold text-blue-600">{stats.by_status.acknowledged}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              <p className="text-sm text-gray-500">严重告警</p>
            </div>
            <p className="text-2xl font-bold text-yellow-600">{stats.by_severity.critical}</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b flex gap-4">
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
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="">所有状态</option>
            <option value="firing">触发中</option>
            <option value="resolved">已解决</option>
            <option value="acknowledged">已确认</option>
          </select>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="">所有严重程度</option>
            <option value="critical">严重</option>
            <option value="warning">警告</option>
            <option value="info">信息</option>
          </select>
        </div>

        <div className="divide-y max-h-[500px] overflow-y-auto">
          {loading ? (
            <div className="p-8 text-center text-gray-500">加载中...</div>
          ) : alerts.length === 0 ? (
            <div className="p-8 text-center text-gray-500">暂无告警</div>
          ) : (
            alerts.map((alert) => (
              <div
                key={alert.id}
                onClick={() => setSelectedAlert(alert)}
                className="p-4 hover:bg-gray-50 cursor-pointer"
              >
                <div className="flex items-start gap-3">
                  {STATUS_ICONS[alert.status]}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{alert.alertname}</span>
                      <span
                        className={`px-2 py-0.5 text-xs rounded ${
                          SEVERITY_COLORS[alert.severity] || SEVERITY_COLORS.info
                        }`}
                      >
                        {alert.severity}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-xs rounded text-white ${
                          STATUS_COLORS[alert.status] || 'bg-gray-500'
                        }`}
                      >
                        {alert.status}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-600">
                      {alert.summary || alert.message}
                    </p>
                    <div className="mt-1 text-xs text-gray-400">
                      {formatTime(alert.created_at)}
                      {alert.acknowledged_by && (
                        <span className="ml-2">
                          · 确认人: {alert.acknowledged_by}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {stats && stats.top_alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold mb-4">高频告警</h3>
          <div className="space-y-2">
            {stats.top_alerts.map((alert, index) => (
              <div key={alert.name} className="flex items-center gap-3">
                <span className="text-sm text-gray-400 w-6">{index + 1}</span>
                <span className="flex-1">{alert.name}</span>
                <span className="text-sm text-gray-600">{alert.count} 次</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedAlert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="font-semibold">{selectedAlert.alertname}</h3>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <p className="text-sm text-gray-500">消息</p>
                <p>{selectedAlert.message || selectedAlert.summary}</p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">状态</p>
                  <p>{selectedAlert.status}</p>
                </div>
                <div>
                  <p className="text-gray-500">严重程度</p>
                  <p>{selectedAlert.severity}</p>
                </div>
                <div>
                  <p className="text-gray-500">开始时间</p>
                  <p>{formatTime(selectedAlert.starts_at)}</p>
                </div>
                <div>
                  <p className="text-gray-500">结束时间</p>
                  <p>{formatTime(selectedAlert.ends_at)}</p>
                </div>
              </div>
              
              {selectedAlert.status === 'firing' && (
                <div>
                  <textarea
                    value={acknowledgeNote}
                    onChange={(e) => setAcknowledgeNote(e.target.value)}
                    placeholder="确认备注..."
                    className="w-full p-2 border rounded-lg"
                    rows={3}
                  />
                </div>
              )}
            </div>
            <div className="p-4 border-t flex justify-end gap-2">
              <button
                onClick={() => setSelectedAlert(null)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                关闭
              </button>
              {selectedAlert.status === 'firing' && (
                <button
                  onClick={() => acknowledgeAlert(selectedAlert.id)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  确认告警
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertsPage;
