import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

interface NavItem {
  path: string;
  icon: React.ReactNode;
  label: string;
}

/**
 * 极简主义折叠侧边栏组件
 */
export const Sidebar: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  const navItems: NavItem[] = [
    { path: '/dashboard', icon: '🏠', label: '仪表盘' },
    { path: '/tasks', icon: '📋', label: '任务中心' },
    { path: '/teams', icon: '👥', label: '团队管理' },
    { path: '/market', icon: '🏪', label: '人才市场' },
  ];

  const moreItems: NavItem[] = [
    { path: '/consult', icon: '💬', label: '智能咨询' },
    { path: '/recruit', icon: '📢', label: '智能体招募' },
    { path: '/auto-work', icon: '🤖', label: '自主工作' },
    { path: '/evolution', icon: '⚡', label: '自我进化' },
    { path: '/ecosystem', icon: '🌐', label: '活体生态' },
    { path: '/governance', icon: '⚖️', label: '三省六部' },
    { path: '/five-end', icon: '🔄', label: '五端协同' },
    { path: '/learning', icon: '📚', label: '学习系统' },
    { path: '/counterstrike', icon: '🛡️', label: '反击系统' },
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <motion.aside
      animate={{ width: isExpanded ? 200 : 64 }}
      transition={{ duration: 0.15, ease: 'easeOut' }}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
      className="fixed left-0 top-0 h-full glass border-r border-border-light z-40 sidebar"
    >
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="flex items-center justify-center h-16 border-b border-border-light">
          <div className="text-xl font-bold text-accent-gold">房</div>
          {isExpanded && (
            <span className="ml-2 text-white font-semibold">房都督AI</span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${isActive(item.path)
                ? 'bg-white/10 text-white'
                : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
                }`}
            >
              <span className="text-lg">{item.icon}</span>
              {isExpanded && <span className="text-sm">{item.label}</span>}
            </Link>
          ))}

          {/* More Section */}
          {isExpanded && (
            <div className="mt-4">
              <div className="px-3 py-1 text-xs text-text-disabled uppercase">更多</div>
              {moreItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md transition-colors ${isActive(item.path)
                    ? 'bg-white/10 text-white'
                    : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
                    }`}
                >
                  <span className="text-lg">{item.icon}</span>
                  <span className="text-sm">{item.label}</span>
                </Link>
              ))}
            </div>
          )}
        </nav>

        {/* User Info */}
        <div className="p-3 border-t border-border-light">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center">
              <span className="text-accent-gold">{user?.full_name?.charAt(0) || 'U'}</span>
            </div>
            {isExpanded && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">
                  {user?.full_name || user?.email?.split('@')[0] || '用户'}
                </p>
                <p className="text-xs text-text-secondary truncate">{user?.email}</p>
              </div>
            )}
          </div>
          {isExpanded && (
            <button
              onClick={logout}
              className="mt-2 w-full flex items-center gap-2 px-3 py-1.5 text-sm text-text-secondary hover:text-status-error hover:bg-status-error/10 rounded-md transition-colors"
            >
              <span>🚪</span>
              <span>退出登录</span>
            </button>
          )}
        </div>
      </div>
    </motion.aside>
  );
};
