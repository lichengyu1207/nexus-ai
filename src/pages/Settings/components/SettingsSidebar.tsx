import { motion } from 'framer-motion';
import type { SettingsTab } from '../types';

interface SettingsSidebarProps {
  activeKey: SettingsTab;
  onSelect: (key: SettingsTab) => void;
  isAdmin: boolean;
}

interface MenuItem {
  key: SettingsTab;
  label: string;
  icon: string;
  isAdmin?: boolean;
}

const menuItems: MenuItem[] = [
  { key: 'profile', label: '个人资料', icon: '👤' },
  { key: 'theme', label: '主题设置', icon: '🎨' },
  { key: 'language', label: '语言设置', icon: '🌐' },
  { key: 'notifications', label: '通知设置', icon: '🔔' },
  { key: 'voice', label: '配音设置', icon: '🔊' },
];

const adminMenuItems: MenuItem[] = [
  { key: 'agent-permissions', label: '智能体权限', icon: '🤖', isAdmin: true },
  { key: 'audit-logs', label: '审计日志', icon: '📋', isAdmin: true },
  { key: 'mcp-tools', label: 'MCP工具管理', icon: '🔧', isAdmin: true },
  { key: 'global-config', label: '全局配置', icon: '⚙️', isAdmin: true },
];

export function SettingsSidebar({ activeKey, onSelect, isAdmin }: SettingsSidebarProps) {
  return (
    <nav className="w-[280px] bg-slate-900/50 backdrop-blur-md border-r border-slate-700/50 p-4">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white mb-1">设置</h2>
        <p className="text-sm text-gray-500">管理您的账户和偏好</p>
      </div>

      <div className="space-y-1">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2 px-3">
          个人设置
        </p>
        {menuItems.map((item) => (
          <motion.button
            key={item.key}
            whileHover={{ x: 4 }}
            onClick={() => onSelect(item.key)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left
              transition-colors ${
                activeKey === item.key
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span className="text-sm font-medium">{item.label}</span>
          </motion.button>
        ))}
      </div>

      {isAdmin && (
        <div className="mt-6 space-y-1">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2 px-3">
            系统治理
          </p>
          {adminMenuItems.map((item) => (
            <motion.button
              key={item.key}
              whileHover={{ x: 4 }}
              onClick={() => onSelect(item.key)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left
                transition-colors ${
                  activeKey === item.key
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
                }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span className="text-sm font-medium">{item.label}</span>
            </motion.button>
          ))}
        </div>
      )}
    </nav>
  );
}
