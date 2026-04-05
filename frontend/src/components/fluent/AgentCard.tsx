import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface AgentCardProps {
  agent: {
    id: string;
    name: string;
    avatar?: string;
    level?: number;
    department?: string;
    status: 'idle' | 'busy' | 'working' | 'autonomous';
    currentTask?: string;
    rarity?: 'common' | 'rare' | 'epic' | 'legendary';
  };
  onClick?: () => void;
}

const statusConfig = {
  idle: { color: 'bg-green-500', glow: 'shadow-[0_0_15px_rgba(34,197,94,0.4)]', label: '空闲' },
  busy: { color: 'bg-fluent-gold-500', glow: 'shadow-[0_0_15px_rgba(212,175,55,0.4)]', label: '忙碌' },
  working: { color: 'bg-blue-500', glow: 'shadow-[0_0_15px_rgba(59,130,246,0.4)]', label: '工作中' },
  autonomous: { color: 'bg-purple-500', glow: 'shadow-[0_0_15px_rgba(168,85,247,0.4)]', label: '自主' },
};

const rarityBorders = {
  common: 'border-gray-300',
  rare: 'border-blue-400',
  epic: 'border-purple-400',
  legendary: 'border-fluent-gold-500',
};

const AgentCard: React.FC<AgentCardProps> = ({ agent, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);
  const status = statusConfig[agent.status] || statusConfig.idle;
  const rarityBorder = rarityBorders[agent.rarity || 'common'];

  return (
    <motion.div
      className={`
        relative rounded-2xl overflow-hidden cursor-pointer
        transition-all duration-300 ease-fluent
        border-2 ${rarityBorder}
        bg-white
      `}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      animate={isHovered ? { boxShadow: status.glow } : {}}
    >
      <div className="p-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <motion.div
              className={`absolute inset-0 rounded-full ${status.color} opacity-30`}
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <img
              src={agent.avatar || '/default-avatar.png'}
              alt={agent.name}
              className="w-12 h-12 rounded-full object-cover relative z-10 border-2 border-white"
            />
            <div
              className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full ${status.color} border-2 border-white`}
            />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-fluent-deepOcean-500 truncate">
              {agent.name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium text-white ${status.color}`}
              >
                {status.label}
              </span>
              {agent.level && (
                <span className="text-xs text-fluent-gold-500 font-medium">
                  Lv.{agent.level}
                </span>
              )}
            </div>
          </div>
        </div>
        {agent.department && (
          <div className="mt-2 text-xs text-gray-500">{agent.department}</div>
        )}
        {agent.currentTask && (
          <div className="mt-2 px-3 py-2 bg-fluent-deepOcean-50 rounded-lg">
            <p className="text-xs text-gray-600 truncate">
              📋 {agent.currentTask}
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default AgentCard;
