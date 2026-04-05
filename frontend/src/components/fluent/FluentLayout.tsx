import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  Users,
  MessageSquare,
  ShoppingCart,
  Building2,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bell,
  Search,
  User,
  LogOut,
  Sun,
  Moon,
} from 'lucide-react';

interface FluentLayoutProps {
  children: React.ReactNode;
  currentPage?: string;
  onNavigate?: (page: string) => void;
  user?: {
    name: string;
    avatar?: string;
    credits?: number;
  };
}

const menuItems = [
  { id: 'dashboard', label: '仪表盘', icon: Home },
  { id: 'agents', label: '智能体管理', icon: Users },
  { id: 'consultation', label: '智能咨询', icon: MessageSquare },
  { id: 'market', label: '人才市场', icon: ShoppingCart },
  { id: 'knowledge', label: '小区知识库', icon: Building2 },
  { id: 'settings', label: '设置', icon: Settings },
];

const FluentLayout: React.FC<FluentLayoutProps> = ({
  children,
  currentPage = 'dashboard',
  onNavigate,
  user = { name: '用户', credits: 1000 },
}) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const sidebarVariants = {
    expanded: { width: 240 },
    collapsed: { width: 72 },
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-fluent-deepOcean-600 dark:to-fluent-deepOcean-800">
        <motion.header
          className="fixed top-0 left-0 right-0 h-16 z-40 backdrop-blur-xl bg-white/70 dark:bg-fluent-deepOcean-500/70 border-b border-white/20"
          initial={{ y: -64 }}
          animate={{ y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center justify-between h-full px-4">
            <div className="flex items-center gap-4">
              <motion.div
                className="flex items-center gap-2"
                whileHover={{ scale: 1.02 }}
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-fluent-deepOcean-500 to-fluent-deepOcean-700 flex items-center justify-center">
                  <span className="text-fluent-gold-400 font-bold text-lg">督</span>
                </div>
                {!sidebarCollapsed && (
                  <span className="font-heading text-xl text-fluent-deepOcean-500 dark:text-white">
                    房都督
                  </span>
                )}
              </motion.div>
            </div>

            <div className="flex-1 max-w-xl mx-8">
              <motion.div
                className="relative"
                animate={{ scale: searchOpen ? 1.02 : 1 }}
              >
                <input
                  type="text"
                  placeholder="搜索小区、智能体、任务..."
                  className="w-full px-4 py-2 pl-10 rounded-xl bg-white/50 dark:bg-white/10 border border-white/30 focus:border-fluent-gold-500 focus:ring-2 focus:ring-fluent-gold-500/20 outline-none transition-all"
                  onFocus={() => setSearchOpen(true)}
                  onBlur={() => setSearchOpen(false)}
                />
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              </motion.div>
            </div>

            <div className="flex items-center gap-3">
              <motion.button
                className="p-2 rounded-lg hover:bg-white/50 dark:hover:bg-white/10 transition-colors"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setDarkMode(!darkMode)}
              >
                {darkMode ? (
                  <Sun className="w-5 h-5 text-fluent-gold-400" />
                ) : (
                  <Moon className="w-5 h-5 text-gray-600" />
                )}
              </motion.button>

              <motion.button
                className="p-2 rounded-lg hover:bg-white/50 dark:hover:bg-white/10 transition-colors relative"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <Bell className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              </motion.button>

              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600">
                <span className="text-fluent-deepOcean-900 font-medium text-sm">
                  💰 {user.credits?.toLocaleString() || 0}
                </span>
              </div>

              <motion.div
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl cursor-pointer hover:bg-white/50 dark:hover:bg-white/10 transition-colors"
                whileHover={{ scale: 1.02 }}
              >
                <img
                  src={user.avatar || '/default-avatar.png'}
                  alt={user.name}
                  className="w-8 h-8 rounded-full"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-white">
                  {user.name}
                </span>
              </motion.div>
            </div>
          </div>
        </motion.header>

        <motion.aside
          className="fixed left-0 top-16 bottom-0 z-30 backdrop-blur-xl bg-fluent-deepOcean-500/95 border-r border-white/10"
          variants={sidebarVariants}
          animate={sidebarCollapsed ? 'collapsed' : 'expanded'}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
        >
          <nav className="flex flex-col h-full py-4">
            <div className="flex-1 space-y-1 px-3">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <motion.button
                    key={item.id}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2.5 rounded-xl
                      transition-all duration-200
                      ${
                        isActive
                          ? 'bg-fluent-gold-500/20 text-fluent-gold-400 border border-fluent-gold-500/30'
                          : 'text-white/70 hover:bg-white/10 hover:text-white'
                      }
                    `}
                    onClick={() => onNavigate?.(item.id)}
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <AnimatePresence>
                      {!sidebarCollapsed && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          className="text-sm font-medium whitespace-nowrap"
                        >
                          {item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    {isActive && !sidebarCollapsed && (
                      <motion.div
                        className="ml-auto w-1.5 h-1.5 rounded-full bg-fluent-gold-400"
                        layoutId="activeIndicator"
                      />
                    )}
                  </motion.button>
                );
              })}
            </div>

            <div className="px-3 pt-4 border-t border-white/10">
              <motion.button
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-white/70 hover:bg-white/10 hover:text-white transition-colors"
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
              >
                <LogOut className="w-5 h-5 flex-shrink-0" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      className="text-sm font-medium whitespace-nowrap"
                    >
                      退出登录
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>
            </div>

            <motion.button
              className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-fluent-gold-500 flex items-center justify-center shadow-lg"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              {sidebarCollapsed ? (
                <ChevronRight className="w-4 h-4 text-white" />
              ) : (
                <ChevronLeft className="w-4 h-4 text-white" />
              )}
            </motion.button>
          </nav>
        </motion.aside>

        <motion.main
          className="pt-16 min-h-screen transition-all duration-300"
          animate={{ marginLeft: sidebarCollapsed ? 72 : 240 }}
          transition={{ duration: 0.3 }}
        >
          <div className="p-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {children}
            </motion.div>
          </div>
        </motion.main>
      </div>
    </div>
  );
};

export default FluentLayout;
