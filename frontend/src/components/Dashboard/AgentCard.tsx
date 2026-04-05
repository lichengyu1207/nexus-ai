import React from 'react';
import { Link } from 'react-router-dom';

interface AgentCardProps {
  agent: {
    id: string;
    name: string;
    avatar: string;
    department: string;
    departmentIcon: string;
    status: 'idle' | 'busy' | 'auto' | 'offline';
    currentTask?: string;
    efficiency: number;
    level: number;
    workTime: string;
    todayTasks: number;
    totalEarnings: number;
  };
  onClick?: () => void;
}

const statusConfig = {
  idle: {
    label: '空闲',
    color: 'bg-fluent-jade-500',
    bgColor: 'bg-fluent-jade-50',
    textColor: 'text-fluent-jade-700',
    dotClass: 'status-idle',
  },
  busy: {
    label: '忙碌',
    color: 'bg-fluent-gold-500',
    bgColor: 'bg-fluent-gold-50',
    textColor: 'text-fluent-gold-700',
    dotClass: 'status-busy',
  },
  auto: {
    label: '自主工作',
    color: 'bg-purple-500',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-700',
    dotClass: 'status-autonomous',
  },
  offline: {
    label: '离线',
    color: 'bg-gray-400',
    bgColor: 'bg-gray-50',
    textColor: 'text-gray-500',
    dotClass: 'bg-gray-400',
  },
};

const departmentIcons: Record<string, string> = {
  '吏部': '👥',
  '户部': '💰',
  '礼部': '📜',
  '兵部': '⚔️',
  '刑部': '⚖️',
  '工部': '🔧',
  '内阁': '🏛️',
  'default': '🤖',
};

const AgentCard: React.FC<AgentCardProps> = ({ agent, onClick }) => {
  const config = statusConfig[agent.status];
  const deptIcon = departmentIcons[agent.department] || departmentIcons['default'];

  return (
    <div
      onClick={onClick}
      className="acrylic rounded-xl shadow-fluent-md p-4 border border-white/30 hover:shadow-fluent-lg hover:border-fluent-gold-300 transition-all duration-300 cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-fluent-deepOcean-400 to-fluent-deepOcean-600 flex items-center justify-center text-2xl shadow-fluent-sm group-hover:scale-105 transition-transform">
              {agent.avatar || deptIcon}
            </div>
            <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full ${config.dotClass} border-2 border-white`}></div>
          </div>
          <div>
            <h4 className="font-semibold text-fluent-deepOcean-500 group-hover:text-fluent-gold-600 transition-colors">
              {agent.name}
            </h4>
            <div className="flex items-center gap-1 text-sm text-fluent-deepOcean-300">
              <span>{deptIcon}</span>
              <span>{agent.department}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-xs px-2 py-0.5 rounded-full bg-fluent-gold-100 text-fluent-gold-700 font-medium">
            Lv.{agent.level}
          </span>
        </div>
      </div>

      <div className={`text-sm px-2 py-1 rounded-lg ${config.bgColor} ${config.textColor} mb-3`}>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${config.color} animate-pulse`}></span>
          <span>{config.label}</span>
          {agent.workTime && agent.status !== 'idle' && (
            <span className="text-xs opacity-70">· {agent.workTime}</span>
          )}
        </div>
      </div>

      {agent.status !== 'idle' && agent.currentTask && (
        <div className="text-sm text-fluent-deepOcean-400 mb-3 line-clamp-2">
          📋 {agent.currentTask}
        </div>
      )}

      {agent.status === 'idle' && (
        <div className="text-sm text-fluent-jade-600 mb-3">
          ✅ 可接受新任务
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-fluent-deepOcean-300 pt-2 border-t border-fluent-deepOcean-100">
        <div className="flex items-center gap-1">
          <span>⚡</span>
          <span>效率 {Math.round(agent.efficiency * 100)}%</span>
        </div>
        <div className="flex items-center gap-1">
          <span>📊</span>
          <span>今日 {agent.todayTasks} 任务</span>
        </div>
        <div className="flex items-center gap-1">
          <span>💎</span>
          <span>{agent.totalEarnings} 积分</span>
        </div>
      </div>
    </div>
  );
};

export default AgentCard;
