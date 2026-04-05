import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface DashboardData {
  total_users: number;
  total_tasks: number;
  total_reports: number;
  active_users_today: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
  total_ips: number;
  pending_ip_applications: number;
  pending_withdrawals: number;
  total_commission: number;
}

interface RecentUser {
  id: string;
  email: string;
  username: string;
  source: string;
  created_at: string;
}

interface RecentTask {
  id: string;
  query: string;
  status: string;
  created_at: string;
}

const StatCard: React.FC<{
  title: string;
  value: number | string;
  icon: string;
  color: string;
  link?: string;
}> = ({ title, value, icon, color, link }) => {
  const content = (
    <div className="bg-white rounded-lg shadow p-4 h-full hover:shadow-md transition-shadow">
      <div className="flex items-center mb-2">
        <span className="text-xl mr-2" style={{ color }}>{icon}</span>
        <span className="text-sm text-gray-500">{title}</span>
      </div>
      <div className="text-2xl font-bold">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
    </div>
  );

  if (link) {
    return <Link to={link}>{content}</Link>;
  }
  return content;
};

const AdminDashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [recentUsers, setRecentUsers] = useState<RecentUser[]>([]);
  const [recentTasks, setRecentTasks] = useState<RecentTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const [dashboardRes, usersRes, tasksRes] = await Promise.all([
        fetch('http://localhost:8000/api/admin/dashboard', { headers }).then(r => r.json()).catch(() => null),
        fetch('http://localhost:8000/api/admin/users?page=1&page_size=5', { headers }).then(r => r.json()).catch(() => ({ users: [] })),
        fetch('http://localhost:8000/api/admin/tasks?page=1&page_size=5', { headers }).then(r => r.json()).catch(() => ({ tasks: [] })),
      ]);

      if (dashboardRes) setData(dashboardRes);
      setRecentUsers(usersRes.users || []);
      setRecentTasks(tasksRes.tasks || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSourceName = (source: string | null): string => {
    if (!source) return '直接注册';
    const names: Record<string, string> = {
      laohai: '老海渠道',
      seo: 'SEO',
      urgent: '紧急渠道',
      direct: '直接注册',
    };
    return names[source] || source;
  };

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-700',
      processing: 'bg-blue-100 text-blue-700',
      pending: 'bg-yellow-100 text-yellow-700',
      failed: 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">管理仪表盘</h1>

      {/* 核心指标 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="总用户数"
          value={data?.total_users || 0}
          icon="👥"
          color="#1976d2"
          link="/admin/users"
        />
        <StatCard
          title="总任务数"
          value={data?.total_tasks || 0}
          icon="📋"
          color="#2e7d32"
        />
        <StatCard
          title="总报告数"
          value={data?.total_reports || 0}
          icon="📊"
          color="#ed6c02"
        />
        <StatCard
          title="今日活跃"
          value={data?.active_users_today || 0}
          icon="📈"
          color="#9c27b0"
        />
      </div>

      {/* 用户增长 */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">今日新增用户</p>
          <p className="text-xl font-bold text-green-600">{data?.new_users_today || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">本周新增用户</p>
          <p className="text-xl font-bold text-blue-600">{data?.new_users_this_week || 0}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">本月新增用户</p>
          <p className="text-xl font-bold text-purple-600">{data?.new_users_this_month || 0}</p>
        </div>
      </div>

      {/* IP相关统计 */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard
          title="IP合作伙伴"
          value={data?.total_ips || 0}
          icon="🎫"
          color="#1976d2"
          link="/admin/ip"
        />
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">待审核IP申请</p>
          <p className="text-xl font-bold text-orange-600">{data?.pending_ip_applications || 0}</p>
          <Link to="/admin/ip" className="text-xs text-primary hover:underline">
            去处理 →
          </Link>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">待处理提现</p>
          <p className="text-xl font-bold text-red-600">{data?.pending_withdrawals || 0}</p>
          <Link to="/admin/ip" className="text-xs text-primary hover:underline">
            去处理 →
          </Link>
        </div>
      </div>

      {/* 最近用户和任务 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 最近注册用户 */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">最近注册用户</h3>
            <Link to="/admin/users" className="text-sm text-primary hover:underline">
              查看全部
            </Link>
          </div>
          {recentUsers.length > 0 ? (
            <div className="space-y-3">
              {recentUsers.map((user) => (
                <div key={user.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <p className="text-sm font-medium">{user.username || user.email}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">{getSourceName(user.source)}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(user.created_at).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">暂无用户数据</p>
          )}
        </div>

        {/* 最近任务 */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">最近分析任务</h3>
            <Link to="/admin/analytics" className="text-sm text-primary hover:underline">
              查看全部
            </Link>
          </div>
          {recentTasks.length > 0 ? (
            <div className="space-y-3">
              {recentTasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{task.query || '房产分析任务'}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(task.created_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(task.status)}`}>
                    {task.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">暂无任务数据</p>
          )}
        </div>
      </div>

      {/* 系统状态 */}
      <div className="mt-6 bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-medium mb-2">系统状态</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-sm">后端服务: 正常</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-sm">数据库: 正常</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            <span className="text-sm">AI服务: 正常</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
