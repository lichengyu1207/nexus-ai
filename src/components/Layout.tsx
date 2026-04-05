import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { useAppContextStore } from '@/store/appContextStore';
import { teamApi, Team } from '@/services/api';
import {
  HomeIcon,
  ClipboardDocumentListIcon,
  UserCircleIcon,
  UserGroupIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  ShieldCheckIcon,
  ChatBubbleLeftRightIcon,
  ArrowsRightLeftIcon,
  Squares2X2Icon,
  CircleStackIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  MegaphoneIcon,
  AcademicCapIcon,
  BuildingLibraryIcon,
  GlobeAltIcon,
  SparklesIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import NotificationBell from '@/components/NotificationBell';
import SearchBar from '@/components/SearchBar';
import IntegralBadge from '@/components/IntegralBadge';
import Breadcrumb from '@/components/Breadcrumb';
import { InteractiveMascot } from '@/components/mascot/Mascot';

const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { currentTeam, setCurrentTeam } = useAppContextStore();
  const { t } = useTranslation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [teams, setTeams] = useState<Team[]>([]);
  const [showTeamSelector, setShowTeamSelector] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      const data = await teamApi.list();
      setTeams(data);
      if (data.length > 0 && !currentTeam) {
        setCurrentTeam({
          id: data[0].id,
          name: data[0].name,
          skills: [],
          memberCount: data[0].member_count || 0,
        });
      }
    } catch (error) {
      console.error('Failed to load teams:', error);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const coreNavItems = [
    { to: '/dashboard', icon: HomeIcon, label: '仪表盘', highlight: true },
    { to: '/tasks', icon: ClipboardDocumentListIcon, label: '任务中心' },
    { to: '/teams', icon: UserGroupIcon, label: '团队管理' },
    { to: '/consult', icon: ChatBubbleLeftRightIcon, label: '智能咨询' },
  ];

  const secondaryNavItems = [
    { to: '/compare', icon: ArrowsRightLeftIcon, label: '房源对比' },
    { to: '/reports', icon: DocumentTextIcon, label: '我的报告' },
    { to: '/memory', icon: CircleStackIcon, label: '记忆系统' },
  ];

  const marketNavItems = [
    { to: '/market', icon: UserGroupIcon, label: '人才市场' },
    { to: '/skills', icon: Squares2X2Icon, label: '技能市场' },
  ];

  const advancedNavItems = [
    { to: '/recruit', icon: MegaphoneIcon, label: '智能体招募' },
    { to: '/auto-work', icon: Squares2X2Icon, label: '自主工作' },
    { to: '/evolution', icon: SparklesIcon, label: '自我进化' },
    { to: '/ecosystem', icon: CircleStackIcon, label: '活体生态' },
    { to: '/five-end', icon: Squares2X2Icon, label: '五端协同' },
    { to: '/governance', icon: Cog6ToothIcon, label: '三省六部' },
    { to: '/learning', icon: AcademicCapIcon, label: '学习系统' },
    { to: '/counterstrike', icon: ShieldCheckIcon, label: '反击系统' },
  ];

  const otherNavItems = [
    { to: '/ip', icon: UserCircleIcon, label: 'IP计划' },
    { to: '/feedback', icon: ChatBubbleLeftRightIcon, label: '反馈与建议' },
    { to: '/help', icon: Cog6ToothIcon, label: '帮助中心' },
    { to: '/settings', icon: Cog6ToothIcon, label: '设置' },
  ];

  const adminNavItem = { to: '/admin', icon: ShieldCheckIcon, label: '管理后台' };

  const NavItem: React.FC<{
    to: string;
    icon: React.FC<{ className?: string }>;
    label: string;
    highlight?: boolean;
  }> = ({ to, icon: Icon, label, highlight }) => (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
          isActive
            ? highlight
              ? 'bg-primary-600 text-white font-medium shadow-sm'
              : 'bg-primary-50 text-primary-700 font-medium'
            : 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-700'
        }`
      }
      onClick={() => setSidebarOpen(false)}
    >
      <Icon className="w-5 h-5" />
      <span className="text-sm">{label}</span>
    </NavLink>
  );

  const NavSection: React.FC<{ title: string; children: React.ReactNode; collapsible?: boolean; defaultOpen?: boolean }> = ({
    title,
    children,
    collapsible = false,
    defaultOpen = true,
  }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    if (collapsible) {
      return (
        <div className="mb-2">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center justify-between w-full px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider hover:text-gray-600"
          >
            <span>{title}</span>
            {isOpen ? (
              <ChevronDownIcon className="w-4 h-4" />
            ) : (
              <ChevronRightIcon className="w-4 h-4" />
            )}
          </button>
          {isOpen && <div className="space-y-0.5">{children}</div>}
        </div>
      );
    }

    return (
      <div className="mb-3">
        <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
          {title}
        </div>
        <div className="space-y-0.5">{children}</div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 px-4 h-16">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {sidebarOpen ? (
              <XMarkIcon className="w-6 h-6 text-gray-600 dark:text-gray-300" />
            ) : (
              <Bars3Icon className="w-6 h-6 text-gray-600 dark:text-gray-300" />
            )}
          </button>
          <div className="flex-1">
            <SearchBar />
          </div>
          <IntegralBadge />
          <NotificationBell />
        </div>
      </header>

      {/* Desktop Header */}
      <header className="hidden lg:flex fixed top-0 left-64 right-0 z-40 h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 items-center px-6 gap-4">
        <div className="flex-1 max-w-xl">
          <SearchBar />
        </div>

        {/* Current Team Selector */}
        {teams.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowTeamSelector(!showTeamSelector)}
              className="flex items-center gap-2 px-3 py-1.5 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-colors"
            >
              <UserGroupIcon className="w-4 h-4" />
              <span className="text-sm font-medium">
                {currentTeam?.name || '选择团队'}
              </span>
              <ChevronDownIcon className="w-4 h-4" />
            </button>

            {showTeamSelector && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowTeamSelector(false)}
                />
                <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 z-20 overflow-hidden">
                  <div className="p-2 border-b border-gray-100 dark:border-gray-700">
                    <p className="text-xs text-gray-500 px-2">当前工作团队</p>
                  </div>
                  <div className="max-h-60 overflow-y-auto">
                    {teams.map((team) => (
                      <button
                        key={team.id}
                        onClick={() => {
                          setCurrentTeam({
                            id: team.id,
                            name: team.name,
                            skills: [],
                            memberCount: team.member_count || 0,
                          });
                          setShowTeamSelector(false);
                        }}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 ${
                          currentTeam?.id === team.id ? 'bg-primary-50 dark:bg-primary-900/20' : ''
                        }`}
                      >
                        <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                          <span className="text-primary-600 dark:text-primary-400 text-xs font-bold">
                            {team.name.charAt(0)}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {team.name}
                          </p>
                          <p className="text-xs text-gray-500">{team.member_count || 0} 成员</p>
                        </div>
                        {currentTeam?.id === team.id && (
                          <div className="w-2 h-2 bg-primary-500 rounded-full" />
                        )}
                      </button>
                    ))}
                  </div>
                  <div className="p-2 border-t border-gray-100 dark:border-gray-700">
                    <button
                      onClick={() => {
                        setShowTeamSelector(false);
                        navigate('/teams');
                      }}
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg"
                    >
                      <PlusIcon className="w-4 h-4" />
                      创建新团队
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        <IntegralBadge />
        <NotificationBell />
      </header>

      {/* Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/50"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 h-16 border-b border-gray-200 dark:border-gray-700">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-sm">{t('landing.appName').charAt(0)}</span>
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-white">{t('landing.appNameEn')}AI</span>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-3 overflow-y-auto">
            {/* Core Functions */}
            <div className="space-y-0.5 mb-4">
              {coreNavItems.map((item) => (
                <NavItem key={item.to} {...item} />
              ))}
            </div>

            {/* Secondary Functions */}
            <NavSection title="常用功能">
              {secondaryNavItems.map((item) => (
                <NavItem key={item.to} {...item} />
              ))}
            </NavSection>

            {/* Market */}
            <NavSection title="市场">
              {marketNavItems.map((item) => (
                <NavItem key={item.to} {...item} />
              ))}
            </NavSection>

            {/* Advanced - Collapsible */}
            <NavSection title="高级功能" collapsible defaultOpen={false}>
              {advancedNavItems.map((item) => (
                <NavItem key={item.to} {...item} />
              ))}
            </NavSection>

            {/* Other */}
            <NavSection title="其他" collapsible defaultOpen={false}>
              {otherNavItems.map((item) => (
                <NavItem key={item.to} {...item} />
              ))}
            </NavSection>

            {/* Admin */}
            {user?.is_admin && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <NavItem {...adminNavItem} />
              </div>
            )}
          </nav>

          {/* User Info */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center">
                <UserCircleIcon className="w-6 h-6 text-primary-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {user?.full_name || user?.email?.split('@')[0] || '用户'}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
              <span>退出登录</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-64 pt-16 lg:pt-16 min-h-screen">
        <div className="p-6">
          <Breadcrumb />
          <Outlet />
        </div>
      </main>

      {/* Global Interactive Mascot */}
      <InteractiveMascot size="lg" showQuoteBubble />
    </div>
  );
};

export default Layout;
