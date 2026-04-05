import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import AgentCard from '../components/Dashboard/AgentCard';
import TaskCard from '../components/Dashboard/TaskCard';
import TaskAssignmentPanel from '../components/Dashboard/TaskAssignmentPanel';
import LiveLog from '../components/Dashboard/LiveLog';

interface Agent {
  id: string;
  name: string;
  avatar: string;
  department: string;
  status: 'idle' | 'busy' | 'auto' | 'offline';
  currentTask?: string;
  efficiency: number;
  level: number;
  workTime: string;
  todayTasks: number;
  totalEarnings: number;
}

interface Task {
  id: string;
  type: 'analysis' | 'consult' | 'auto' | 'batch';
  description: string;
  progress: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  assignedAgents: Array<{ id: string; name: string; avatar: string }>;
  startTime: string;
  estimatedEndTime?: string;
}

interface Stats {
  total_agents: number;
  online_agents: number;
  busy_agents: number;
  auto_work_agents: number;
  idle_agents: number;
  total_reward: number;
  today_work_seconds: number;
  pending_tasks: number;
}

interface UserInfo {
  id: string;
  email: string;
  username: string;
  role: string;
  integral: number;
}

const DashboardPage: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [showTaskPanel, setShowTaskPanel] = useState(false);
  const [activeTab, setActiveTab] = useState<'agents' | 'tasks'>('agents');

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [agentsRes, tasksRes, statsRes, userRes] = await Promise.all([
        fetch('http://localhost:8000/api/dashboard/agents-status', { headers }).then(r => r.json()).catch(() => ({ agents: [] })),
        fetch('http://localhost:8000/api/dashboard/current-tasks', { headers }).then(r => r.json()).catch(() => ({ tasks: [] })),
        fetch('http://localhost:8000/api/dashboard/stats', { headers }).then(r => r.json()).catch(() => ({ stats: null })),
        fetch('http://localhost:8000/api/auth/me', { headers }).then(r => r.json()).catch(() => null),
      ]);

      if (agentsRes.agents) {
        setAgents(agentsRes.agents.map((a: any) => ({
          id: a.id,
          name: a.name,
          avatar: a.rarity === 'UR' ? '👑' : a.rarity === 'SSR' ? '⭐' : a.rarity === 'SR' ? '💎' : '🤖',
          department: a.department,
          status: a.status === 'working' ? 'auto' : a.status,
          currentTask: a.current_task_description,
          efficiency: a.efficiency || 1.0,
          level: a.level,
          workTime: formatWorkTime(a.work_duration_seconds),
          todayTasks: a.performance_today || 0,
          totalEarnings: a.total_reward || 0,
        })));
      }

      if (tasksRes.tasks) {
        setTasks(tasksRes.tasks.map((t: any) => ({
          id: t.id,
          type: t.type === 'auto_task' ? 'auto' : t.task_type || 'analysis',
          description: t.description || '任务进行中...',
          progress: t.progress || 50,
          status: t.status === 'assigned' ? 'processing' : t.status,
          assignedAgents: t.assigned_agents || [],
          startTime: t.start_time || new Date().toISOString(),
        })));
      }

      if (statsRes.stats) setStats(statsRes.stats);
      if (userRes) setUser(userRes);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatWorkTime = (seconds: number): string => {
    if (!seconds) return '';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}小时${minutes}分`;
    if (minutes > 0) return `${minutes}分钟`;
    return `${seconds}秒`;
  };

  const formatWorkDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}小时${minutes}分`;
  };

  const handleStartTask = async (taskType: string, input: string, agentIds: string[]) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/dashboard/start-task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          task_type: taskType,
          input,
          agent_ids: agentIds,
          auto_assign: false,
        }),
      });

      if (response.ok) {
        fetchDashboardData();
      }
    } catch (error) {
      console.error('Failed to start task:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="w-12 h-12 border-4 border-fluent-gold-400 border-t-fluent-gold-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto pb-20 space-y-6">
      <div className="acrylic rounded-2xl shadow-fluent-md p-4 flex items-center justify-between border border-white/30">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-fluent-deepOcean-400 to-fluent-deepOcean-600 text-white flex items-center justify-center text-xl font-bold shadow-fluent-sm">
            {user?.username?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div>
            <p className="font-semibold text-fluent-deepOcean-500">{user?.username || '用户'}</p>
            <p className="text-sm text-fluent-deepOcean-300">{user?.role === 'admin' ? '管理员' : '普通用户'}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-fluent-deepOcean-300">当前积分</p>
            <p className="text-2xl font-bold text-fluent-gold-500">{user?.integral || 0}</p>
          </div>
          <Link
            to="/dashboard/recharge"
            className="bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-4 py-2 rounded-xl hover:shadow-gold-glow transition-all duration-300 font-medium"
          >
            充值
          </Link>
          {user?.role === 'admin' && (
            <Link
              to="/admin"
              className="bg-gradient-to-r from-fluent-deepOcean-400 to-fluent-deepOcean-600 text-white px-4 py-2 rounded-xl hover:shadow-fluent-lg transition-all duration-300"
            >
              管理后台
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="acrylic rounded-xl shadow-fluent-md p-4 border border-white/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-fluent-deepOcean-100 flex items-center justify-center text-xl">
              🤖
            </div>
            <div>
              <p className="text-2xl font-bold text-fluent-deepOcean-500">{stats?.total_agents || 0}</p>
              <p className="text-sm text-fluent-deepOcean-300">智能体总数</p>
            </div>
          </div>
        </div>
        <div className="acrylic rounded-xl shadow-fluent-md p-4 border border-white/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-fluent-jade-100 flex items-center justify-center text-xl">
              ✅
            </div>
            <div>
              <p className="text-2xl font-bold text-fluent-jade-600">{stats?.idle_agents || 0}</p>
              <p className="text-sm text-fluent-deepOcean-300">空闲中</p>
            </div>
          </div>
        </div>
        <div className="acrylic rounded-xl shadow-fluent-md p-4 border border-white/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-fluent-gold-100 flex items-center justify-center text-xl">
              ⚡
            </div>
            <div>
              <p className="text-2xl font-bold text-fluent-gold-600">{stats?.busy_agents || 0}</p>
              <p className="text-sm text-fluent-deepOcean-300">忙碌中</p>
            </div>
          </div>
        </div>
        <div className="acrylic rounded-xl shadow-fluent-md p-4 border border-white/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center text-xl">
              🔄
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-600">{stats?.auto_work_agents || 0}</p>
              <p className="text-sm text-fluent-deepOcean-300">自主工作</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('agents')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === 'agents'
                ? 'bg-fluent-gold-500 text-fluent-deepOcean-500'
                : 'bg-fluent-deepOcean-100 text-fluent-deepOcean-500 hover:bg-fluent-deepOcean-200'
            }`}
          >
            🤖 智能体状态
          </button>
          <button
            onClick={() => setActiveTab('tasks')}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === 'tasks'
                ? 'bg-fluent-gold-500 text-fluent-deepOcean-500'
                : 'bg-fluent-deepOcean-100 text-fluent-deepOcean-500 hover:bg-fluent-deepOcean-200'
            }`}
          >
            📋 当前任务 ({tasks.length})
          </button>
        </div>
        <button
          onClick={() => setShowTaskPanel(true)}
          className="bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-4 py-2 rounded-xl hover:shadow-gold-glow transition-all duration-300 font-medium flex items-center gap-2"
        >
          <span>🚀</span>
          <span>启动新任务</span>
        </button>
      </div>

      {activeTab === 'agents' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.length > 0 ? (
            agents.map(agent => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onClick={() => console.log('Agent clicked:', agent.id)}
              />
            ))
          ) : (
            <div className="col-span-full text-center py-12 acrylic rounded-xl border border-white/30">
              <p className="text-fluent-deepOcean-300 mb-2">暂无智能体</p>
              <Link
                to="/dashboard/market"
                className="text-fluent-gold-500 hover:text-fluent-gold-600 font-medium"
              >
                去人才市场招募 →
              </Link>
            </div>
          )}
        </div>
      )}

      {activeTab === 'tasks' && (
        <div className="space-y-4">
          {tasks.length > 0 ? (
            tasks.map(task => (
              <TaskCard key={task.id} task={task} />
            ))
          ) : (
            <div className="text-center py-12 acrylic rounded-xl border border-white/30">
              <p className="text-fluent-deepOcean-300 mb-2">暂无进行中的任务</p>
              <button
                onClick={() => setShowTaskPanel(true)}
                className="text-fluent-gold-500 hover:text-fluent-gold-600 font-medium"
              >
                启动新任务 →
              </button>
            </div>
          )}
        </div>
      )}

      <LiveLog maxEntries={30} />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Link
          to="/dashboard/property-analysis"
          className="acrylic rounded-2xl shadow-fluent-md p-4 text-center hover:shadow-fluent-lg hover:border-fluent-gold-300 transition-all duration-300 border border-white/30 group"
        >
          <span className="text-3xl group-hover:scale-110 transition-transform inline-block">🏠</span>
          <p className="mt-2 font-medium text-fluent-deepOcean-500">房产分析</p>
          <p className="text-xs text-fluent-deepOcean-300">深度分析报告</p>
        </Link>
        <Link
          to="/dashboard/my-reports"
          className="acrylic rounded-2xl shadow-fluent-md p-4 text-center hover:shadow-fluent-lg hover:border-fluent-gold-300 transition-all duration-300 border border-white/30 group"
        >
          <span className="text-3xl group-hover:scale-110 transition-transform inline-block">📋</span>
          <p className="mt-2 font-medium text-fluent-deepOcean-500">我的报告</p>
          <p className="text-xs text-fluent-deepOcean-300">查看历史报告</p>
        </Link>
        <Link
          to="/dashboard/market"
          className="acrylic rounded-2xl shadow-fluent-md p-4 text-center hover:shadow-fluent-lg hover:border-fluent-gold-300 transition-all duration-300 border border-white/30 group"
        >
          <span className="text-3xl group-hover:scale-110 transition-transform inline-block">🏪</span>
          <p className="mt-2 font-medium text-fluent-deepOcean-500">人才市场</p>
          <p className="text-xs text-fluent-deepOcean-300">招募智能体</p>
        </Link>
        <Link
          to="/dashboard/settings"
          className="acrylic rounded-2xl shadow-fluent-md p-4 text-center hover:shadow-fluent-lg hover:border-fluent-gold-300 transition-all duration-300 border border-white/30 group"
        >
          <span className="text-3xl group-hover:scale-110 transition-transform inline-block">⚙️</span>
          <p className="mt-2 font-medium text-fluent-deepOcean-500">账户设置</p>
          <p className="text-xs text-fluent-deepOcean-300">个人信息管理</p>
        </Link>
      </div>

      <div className="acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
        <h3 className="text-lg font-semibold mb-4 text-center text-fluent-deepOcean-500">为什么选择房都督AI</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center p-4 group">
            <span className="text-3xl group-hover:scale-110 transition-transform inline-block">🔒</span>
            <p className="mt-2 font-medium text-fluent-deepOcean-500">数据加密</p>
            <p className="text-xs text-fluent-deepOcean-300">银行级安全</p>
          </div>
          <div className="text-center p-4 group">
            <span className="text-3xl group-hover:scale-110 transition-transform inline-block">👥</span>
            <p className="mt-2 font-medium text-fluent-deepOcean-500">10万+用户</p>
            <p className="text-xs text-fluent-deepOcean-300">信赖之选</p>
          </div>
          <div className="text-center p-4 group">
            <span className="text-3xl group-hover:scale-110 transition-transform inline-block">⚡</span>
            <p className="mt-2 font-medium text-fluent-deepOcean-500">秒级响应</p>
            <p className="text-xs text-fluent-deepOcean-300">快速分析</p>
          </div>
          <div className="text-center p-4 group">
            <span className="text-3xl group-hover:scale-110 transition-transform inline-block">🕐</span>
            <p className="mt-2 font-medium text-fluent-deepOcean-500">7×24服务</p>
            <p className="text-xs text-fluent-deepOcean-300">全天在线</p>
          </div>
        </div>
      </div>

      <div className="fixed bottom-6 right-6 z-50">
        <div className="relative group">
          <div className="w-16 h-16 bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 rounded-full flex items-center justify-center text-3xl shadow-gold-glow cursor-pointer hover:scale-110 transition-transform animate-float">
            🐶
          </div>
          <div className="absolute bottom-full right-0 mb-2 acrylic rounded-xl shadow-fluent-lg p-3 w-48 text-sm opacity-0 group-hover:opacity-100 transition-opacity border border-white/30">
            <p className="text-fluent-deepOcean-500">有什么可以帮您的吗？</p>
          </div>
        </div>
      </div>

      <TaskAssignmentPanel
        isOpen={showTaskPanel}
        onClose={() => setShowTaskPanel(false)}
        onSubmit={handleStartTask}
      />
    </div>
  );
};

export default DashboardPage;
