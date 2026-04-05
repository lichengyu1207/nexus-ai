import React, { useState, useEffect } from 'react';
import { BarChart2, MessageCircle, TrendingUp, Target, Flame, Settings, Award, Calendar } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

interface FunctionStats {
  today_count: number;
  consecutive_days: number;
  total_count: number;
  total_days: number;
  daily_goal: number;
  daily_progress: number;
  weekly_count: number;
  weekly_goal: number;
  weekly_progress: number;
}

interface HabitStats {
  task_analysis: FunctionStats;
  intelligent_consult: FunctionStats;
}

interface HistoryRecord {
  date: string;
  count: number;
  consecutive_days: number;
}

interface UsageHistory {
  function_type: string;
  history: HistoryRecord[];
  total_days: number;
}

export default function HabitsPage() {
  const { token } = useAuth();
  const [stats, setStats] = useState<HabitStats | null>(null);
  const [taskHistory, setTaskHistory] = useState<UsageHistory | null>(null);
  const [consultHistory, setConsultHistory] = useState<UsageHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    task_analysis_daily_target: 5,
    intelligent_consult_daily_target: 3,
    reminder_enabled: true,
    reminder_time: '20:00'
  });

  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [statsRes, taskHistRes, consultHistRes, prefsRes] = await Promise.all([
        fetch('/api/habit/stats', { headers: { Authorization: `Bearer ${token}` } }),
        fetch('/api/habit/history/task_analysis?days=30', { headers: { Authorization: `Bearer ${token}` } }),
        fetch('/api/habit/history/intelligent_consult?days=30', { headers: { Authorization: `Bearer ${token}` } }),
        fetch('/api/habit/preferences', { headers: { Authorization: `Bearer ${token}` } })
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (taskHistRes.ok) setTaskHistory(await taskHistRes.json());
      if (consultHistRes.ok) setConsultHistory(await consultHistRes.json());
      if (prefsRes.ok) {
        const prefs = await prefsRes.json();
        setSettings(prev => ({ ...prev, reminder_enabled: prefs.reminder_enabled, reminder_time: prefs.reminder_time }));
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  const saveSettings = async () => {
    if (!token) return;
    try {
      await fetch('/api/habit/goals', {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          task_analysis_daily_target: settings.task_analysis_daily_target,
          intelligent_consult_daily_target: settings.intelligent_consult_daily_target
        })
      });

      await fetch('/api/habit/preferences', {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          reminder_enabled: settings.reminder_enabled,
          reminder_time: settings.reminder_time
        })
      });

      toast.success('设置已保存');
      setShowSettings(false);
      fetchData();
    } catch (error) {
      toast.error('保存失败');
    }
  };

  const renderHeatmap = (history: HistoryRecord[] | undefined, title: string) => {
    if (!history || history.length === 0) return null;

    const today = new Date();
    const days = [];
    for (let i = 29; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      const record = history.find(r => r.date === dateStr);
      days.push({ date: dateStr, count: record?.count || 0 });
    }

    return (
      <div className="bg-white rounded-xl p-4 shadow-sm">
        <h3 className="font-medium text-gray-900 mb-3">{title}</h3>
        <div className="grid grid-cols-10 gap-1">
          {days.map((day, idx) => (
            <div
              key={idx}
              className={`w-6 h-6 rounded-sm ${
                day.count === 0 ? 'bg-gray-100' :
                day.count === 1 ? 'bg-green-200' :
                day.count === 2 ? 'bg-green-300' :
                day.count >= 3 ? 'bg-green-500' : 'bg-gray-100'
              }`}
              title={`${day.date}: ${day.count}次`}
            />
          ))}
        </div>
        <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
          <span>少</span>
          <div className="w-4 h-4 bg-gray-100 rounded-sm" />
          <div className="w-4 h-4 bg-green-200 rounded-sm" />
          <div className="w-4 h-4 bg-green-300 rounded-sm" />
          <div className="w-4 h-4 bg-green-500 rounded-sm" />
          <span>多</span>
        </div>
      </div>
    );
  };

  const renderStatsCard = (title: string, icon: React.ReactNode, data: FunctionStats, color: string) => {
    const progress = (data.daily_progress / data.daily_goal) * 100;

    return (
      <div className="bg-white rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center`}>
            {icon}
          </div>
          <div>
            <h3 className="font-medium text-gray-900">{title}</h3>
            <p className="text-sm text-gray-500">今日已使用 {data.today_count} 次</p>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">每日目标</span>
              <span className="text-gray-900 font-medium">{data.daily_progress}/{data.daily_goal}</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${progress >= 100 ? 'bg-green-500' : color.replace('bg-', 'bg-').replace('-100', '-500')}`}
                style={{ width: `${Math.min(100, progress)}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-2">
            <div className="text-center p-2 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-gray-900">{data.consecutive_days}</div>
              <div className="text-xs text-gray-500">连续天数</div>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-gray-900">{data.total_count}</div>
              <div className="text-xs text-gray-500">累计次数</div>
            </div>
            <div className="text-center p-2 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-gray-900">{data.weekly_count}</div>
              <div className="text-xs text-gray-500">本周次数</div>
            </div>
          </div>

          {data.consecutive_days >= 7 && (
            <div className="flex items-center gap-2 p-2 bg-orange-50 rounded-lg text-orange-600">
              <Award className="w-4 h-4" />
              <span className="text-sm">连续使用 {data.consecutive_days} 天！</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">我的习惯</h1>
            <p className="text-gray-500 mt-1">培养使用习惯，提升房产决策能力</p>
          </div>
          <button
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm hover:shadow-md transition-all"
          >
            <Settings className="w-4 h-4" />
            <span>设置</span>
          </button>
        </div>

        {stats && (
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            {renderStatsCard(
              '任务分析',
              <BarChart2 className="w-6 h-6 text-blue-500" />,
              stats.task_analysis,
              'bg-blue-100'
            )}
            {renderStatsCard(
              '智能咨询',
              <MessageCircle className="w-6 h-6 text-purple-500" />,
              stats.intelligent_consult,
              'bg-purple-100'
            )}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-4 mb-6">
          {renderHeatmap(taskHistory?.history, '任务分析热力图')}
          {renderHeatmap(consultHistory?.history, '智能咨询热力图')}
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm">
          <h3 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            使用记录
          </h3>
          <div className="space-y-2">
            {[...(taskHistory?.history || [])].reverse().slice(0, 10).map((record, idx) => (
              <div key={idx} className="flex justify-between items-center py-2 border-b last:border-0">
                <span className="text-gray-600">{record.date}</span>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-500">分析 {record.count} 次</span>
                  {record.consecutive_days > 0 && (
                    <span className="flex items-center gap-1 text-orange-500 text-sm">
                      <Flame className="w-3 h-3" />
                      {record.consecutive_days}天
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {showSettings && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl p-6 max-w-md w-full">
              <h3 className="text-lg font-bold mb-4">习惯设置</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    任务分析每日目标
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={settings.task_analysis_daily_target}
                    onChange={e => setSettings({ ...settings, task_analysis_daily_target: parseInt(e.target.value) || 5 })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    智能咨询每日目标
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={settings.intelligent_consult_daily_target}
                    onChange={e => setSettings({ ...settings, intelligent_consult_daily_target: parseInt(e.target.value) || 3 })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">开启提醒</span>
                  <button
                    onClick={() => setSettings({ ...settings, reminder_enabled: !settings.reminder_enabled })}
                    className={`w-12 h-6 rounded-full transition-all ${settings.reminder_enabled ? 'bg-blue-500' : 'bg-gray-300'}`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full transition-all ${settings.reminder_enabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
                  </button>
                </div>

                {settings.reminder_enabled && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      提醒时间
                    </label>
                    <input
                      type="time"
                      value={settings.reminder_time}
                      onChange={e => setSettings({ ...settings, reminder_time: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowSettings(false)}
                  className="flex-1 py-2 border rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={saveSettings}
                  className="flex-1 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
