import React, { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  UsersIcon,
  ChartBarIcon,
  CogIcon,
  HomeIcon,
  ClipboardDocumentListIcon,
  MapPinIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  ComputerDesktopIcon,
  SunIcon,
  MoonIcon,
  GlobeAltIcon,
  ChatBubbleLeftRightIcon,
  BeakerIcon,
  BookOpenIcon,
  EnvelopeIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  FaceSmileIcon,
  BoltIcon,
  DocumentTextIcon,
  ServerIcon,
  SparklesIcon,
  TagIcon,
  CpuChipIcon,
  CloudIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';

const navItems = [
  { 
    label: '仪表盘', 
    icon: ChartBarIcon, 
    path: '/admin',
    exact: true 
  },
  { 
    label: '用户管理', 
    icon: UsersIcon, 
    path: '/admin/users' 
  },
  { 
    label: '用户地图', 
    icon: MapPinIcon, 
    path: '/admin/map' 
  },
  { 
    label: '位置管理', 
    icon: GlobeAltIcon, 
    path: '/admin/locations',
    superAdminOnly: true
  },
  { 
    label: '用户反馈', 
    icon: ChatBubbleLeftRightIcon, 
    path: '/admin/feedback' 
  },
  { 
    label: 'A/B 测试', 
    icon: BeakerIcon, 
    path: '/admin/ab-tests' 
  },
  { 
    label: '知识库', 
    icon: BookOpenIcon, 
    path: '/admin/knowledge-base' 
  },
  { 
    label: '用户沟通', 
    icon: EnvelopeIcon, 
    path: '/admin/user-communication' 
  },
  { 
    label: '举报管理', 
    icon: ExclamationTriangleIcon, 
    path: '/admin/reports' 
  },
  { 
    label: '合规管理', 
    icon: ShieldCheckIcon, 
    path: '/admin/compliance' 
  },
  { 
    label: '吉祥物管理', 
    icon: FaceSmileIcon, 
    path: '/admin/mascot',
    superAdminOnly: true
  },
  { 
    label: '性能监控', 
    icon: BoltIcon, 
    path: '/admin/performance',
    superAdminOnly: true
  },
  { 
    label: '日志管理', 
    icon: DocumentTextIcon, 
    path: '/admin/logs',
    superAdminOnly: true
  },
  { 
    label: '系统监控', 
    icon: ServerIcon, 
    path: '/admin/monitor',
    superAdminOnly: true
  },
  { 
    label: '积分管理', 
    icon: CurrencyDollarIcon, 
    path: '/admin/integral',
    superAdminOnly: true
  },
  { 
    label: '套餐管理', 
    icon: TagIcon, 
    path: '/admin/plans',
    superAdminOnly: true
  },
  { 
    label: '充值订单', 
    icon: CurrencyDollarIcon, 
    path: '/admin/recharge',
    superAdminOnly: true
  },
  { 
    label: 'IP管理', 
    icon: UsersIcon, 
    path: '/admin/ip-management',
    superAdminOnly: true
  },
  { 
    label: '来源统计', 
    icon: GlobeAltIcon, 
    path: '/admin/source-stats',
    superAdminOnly: true
  },
  { 
    label: '数据采集', 
    icon: ServerIcon, 
    path: '/admin/data-collection',
    superAdminOnly: true
  },
  { 
    label: '城市数据', 
    icon: GlobeAltIcon, 
    path: '/admin/geo',
    superAdminOnly: true
  },
  { 
    label: '系统设置', 
    icon: CogIcon, 
    path: '/admin/settings' 
  },
  { 
    label: '审计日志', 
    icon: ClipboardDocumentListIcon, 
    path: '/admin/audit' 
  },
  { 
    label: '统计分析', 
    icon: ChartBarIcon, 
    path: '/admin/stats' 
  },
  { 
    label: '自博弈训练', 
    icon: CpuChipIcon, 
    path: '/admin/training',
    superAdminOnly: true
  },
  { 
    label: '集群监控', 
    icon: CloudIcon, 
    path: '/admin/cluster',
    superAdminOnly: true
  },
];

const AdminLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isActive = (path: string, exact: boolean = false) => {
    if (exact) {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const getRoleBadge = () => {
    if (user?.role === 'super_admin') {
      return (
        <span className="px-2 py-0.5 text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded">
          超级管理员
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
        管理员
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 z-50 h-full w-64 
        bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Logo & Close */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700">
          <Link to="/admin" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">A</span>
            </div>
            <span className="text-lg font-bold text-gray-900 dark:text-white">管理后台</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 180px)' }}>
          {navItems
            .filter((item) => !item.superAdminOnly || user?.role === 'super_admin')
            .map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                  transition-colors
                  ${isActive(item.path, item.exact)
                    ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            ))}
        </nav>

        {/* Back to site */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <Link
            to="/dashboard"
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <HomeIcon className="w-5 h-5" />
            返回前台
          </Link>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between h-full px-4">
            {/* Mobile menu button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>

            {/* Title */}
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white hidden lg:block">
              {navItems.find(item => isActive(item.path, item.exact))?.label || '管理后台'}
            </h1>

            {/* Right side */}
            <div className="flex items-center gap-3">
              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {theme === 'dark' ? (
                  <SunIcon className="w-5 h-5" />
                ) : (
                  <MoonIcon className="w-5 h-5" />
                )}
              </button>

              {/* User info */}
              <div className="flex items-center gap-3">
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {user?.full_name || user?.email}
                  </p>
                  {getRoleBadge()}
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="退出登录"
                >
                  <ArrowRightOnRectangleIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
