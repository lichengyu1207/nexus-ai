import React, { useState, useEffect } from 'react';
import { BarChart2, MessageCircle, TrendingUp, Target, ChevronRight, Flame } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

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

export default function HabitCard() {
  const { token } = useAuth();
  const [stats, setStats] = useState<HabitStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    if (!token) return;
    try {
      const res = await fetch('/api/habit/stats', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch habit stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, [token]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-4 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (!stats) return null;

  const taskProgress = stats.task_analysis.daily_progress / stats.task_analysis.daily_goal * 100;
  const consultProgress = stats.intelligent_consult.daily_progress / stats.intelligent_consult.daily_goal * 100;

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <div className="p-4 border-b bg-gradient-to-r from-blue-50 to-purple-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-500" />
            <h3 className="font-medium text-gray-900">今日目标</h3>
          </div>
          <Link
            to="/habits"
            className="text-sm text-blue-500 hover:text-blue-600 flex items-center gap-1"
          >
            详情
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      <div className="p-4 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
            <BarChart2 className="w-5 h-5 text-blue-500" />
          </div>
          <div className="flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-700">任务分析</span>
              <span className="text-xs text-gray-500">
                {stats.task_analysis.daily_progress}/{stats.task_analysis.daily_goal}
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  taskProgress >= 100 ? 'bg-green-500' : 'bg-blue-500'
                }`}
                style={{ width: `${Math.min(100, taskProgress)}%` }}
              />
            </div>
          </div>
          {stats.task_analysis.consecutive_days > 0 && (
            <div className="flex items-center gap-1 text-orange-500">
              <Flame className="w-4 h-4" />
              <span className="text-xs font-medium">{stats.task_analysis.consecutive_days}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
            <MessageCircle className="w-5 h-5 text-purple-500" />
          </div>
          <div className="flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-700">智能咨询</span>
              <span className="text-xs text-gray-500">
                {stats.intelligent_consult.daily_progress}/{stats.intelligent_consult.daily_goal}
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  consultProgress >= 100 ? 'bg-green-500' : 'bg-purple-500'
                }`}
                style={{ width: `${Math.min(100, consultProgress)}%` }}
              />
            </div>
          </div>
          {stats.intelligent_consult.consecutive_days > 0 && (
            <div className="flex items-center gap-1 text-orange-500">
              <Flame className="w-4 h-4" />
              <span className="text-xs font-medium">{stats.intelligent_consult.consecutive_days}</span>
            </div>
          )}
        </div>

        <div className="pt-3 border-t flex justify-between items-center text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            <span>本周分析 {stats.task_analysis.weekly_count}次</span>
          </div>
          <div className="flex items-center gap-1">
            <MessageCircle className="w-3 h-3" />
            <span>本周咨询 {stats.intelligent_consult.weekly_count}次</span>
          </div>
        </div>
      </div>
    </div>
  );
}
