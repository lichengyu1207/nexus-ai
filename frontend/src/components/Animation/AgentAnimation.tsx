/**
 * 智能体动画状态机组件
 * Agent Animation State Machine Component
 * 
 * 根据智能体的真实运行状态切换动画
 */

import React, { useState, useEffect, useRef, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export type AgentStatus = 'idle' | 'busy' | 'thinking' | 'success' | 'error' | 'sleeping';

export type AgentDepartment = 
  | 'li' | 'gong' | 'hu' | 'bing' | 'li_guan' | 'xing'
  | 'attack' | 'defense' | 'memory';

export interface AgentAnimationProps {
  agentId: string;
  department: AgentDepartment;
  status: AgentStatus;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  onClick?: () => void;
  className?: string;
}

const departmentConfig: Record<AgentDepartment, {
  name: string;
  color: string;
  bgColor: string;
  icon: string;
}> = {
  li: { name: '礼部', color: '#3B82F6', bgColor: '#EFF6FF', icon: '📜' },
  gong: { name: '工部', color: '#F97316', bgColor: '#FFF7ED', icon: '📊' },
  hu: { name: '户部', color: '#EAB308', bgColor: '#FEFCE8', icon: '💰' },
  bing: { name: '兵部', color: '#22C55E', bgColor: '#F0FDF4', icon: '📡' },
  li_guan: { name: '吏部', color: '#A855F7', bgColor: '#FAF5FF', icon: '👑' },
  xing: { name: '刑部', color: '#EF4444', bgColor: '#FEF2F2', icon: '🛡️' },
  attack: { name: '攻击', color: '#1F2937', bgColor: '#F3F4F6', icon: '⚔️' },
  defense: { name: '防御', color: '#6B7280', bgColor: '#F9FAFB', icon: '🛡️' },
  memory: { name: '记忆', color: '#F3F4F6', bgColor: '#FFFFFF', icon: '✨' },
};

const statusAnimations = {
  idle: {
    y: [0, -5, 0],
    transition: { duration: 2, repeat: Infinity, ease: 'easeInOut' }
  },
  busy: {
    scale: [1, 1.05, 1],
    transition: { duration: 0.5, repeat: Infinity, ease: 'easeInOut' }
  },
  thinking: {
    rotate: [-5, 5, -5],
    transition: { duration: 1, repeat: Infinity, ease: 'easeInOut' }
  },
  success: {
    scale: [1, 1.2, 1],
    y: [0, -20, 0],
    transition: { duration: 0.6, repeat: 1 }
  },
  error: {
    x: [-5, 5, -5, 5, 0],
    transition: { duration: 0.4, repeat: 2 }
  },
  sleeping: {
    opacity: [0.6, 0.8, 0.6],
    transition: { duration: 3, repeat: Infinity, ease: 'easeInOut' }
  }
};

const statusEffects: Record<AgentStatus, React.ReactNode> = {
  idle: null,
  busy: (
    <motion.div
      className="absolute -top-2 -right-2"
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    >
      <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />
    </motion.div>
  ),
  thinking: (
    <motion.div
      className="absolute -top-8 left-1/2 transform -translate-x-1/2"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="bg-white px-2 py-1 rounded-full shadow-lg text-xs flex items-center gap-1">
        <motion.span
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          💭
        </motion.span>
        <span>思考中...</span>
      </div>
    </motion.div>
  ),
  success: (
    <motion.div
      className="absolute inset-0 pointer-events-none"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: [0, 1.5], opacity: [1, 0] }}
      transition={{ duration: 0.6 }}
    >
      <div className="w-full h-full rounded-full bg-green-400/30" />
    </motion.div>
  ),
  error: (
    <motion.div
      className="absolute -top-1 -right-1"
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
    >
      <span className="text-red-500 text-lg">❗</span>
    </motion.div>
  ),
  sleeping: (
    <motion.div
      className="absolute -top-2 right-0"
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ duration: 2, repeat: Infinity }}
    >
      <span className="text-sm">💤</span>
    </motion.div>
  ),
};

const sizeConfig = {
  small: { container: 'w-10 h-10', icon: 'text-lg', label: 'text-xs' },
  medium: { container: 'w-14 h-14', icon: 'text-2xl', label: 'text-sm' },
  large: { container: 'w-20 h-20', icon: 'text-3xl', label: 'text-base' },
};

const AgentAnimation: React.FC<AgentAnimationProps> = memo(({
  agentId,
  department,
  status,
  size = 'medium',
  showLabel = true,
  onClick,
  className = '',
}) => {
  const [currentStatus, setCurrentStatus] = useState<AgentStatus>(status);
  const [clickCount, setClickCount] = useState(0);
  const [showEasterEgg, setShowEasterEgg] = useState(false);
  const prevStatusRef = useRef<AgentStatus>(status);

  const config = departmentConfig[department];
  const sizes = sizeConfig[size];

  useEffect(() => {
    if (status !== prevStatusRef.current) {
      if (status === 'success' || status === 'error') {
        setCurrentStatus(status);
        const timer = setTimeout(() => {
          setCurrentStatus('idle');
        }, status === 'success' ? 2000 : 3000);
        return () => clearTimeout(timer);
      } else {
        setCurrentStatus(status);
      }
      prevStatusRef.current = status;
    }
  }, [status]);

  const handleClick = useCallback(() => {
    setClickCount(prev => prev + 1);
    
    if (clickCount >= 9) {
      setShowEasterEgg(true);
      setClickCount(0);
      setTimeout(() => setShowEasterEgg(false), 3000);
    }
    
    onClick?.();
  }, [clickCount, onClick]);

  return (
    <div className={`relative inline-flex flex-col items-center ${className}`}>
      <motion.div
        className={`
          ${sizes.container}
          rounded-full
          flex items-center justify-center
          cursor-pointer
          relative
          shadow-md
          hover:shadow-lg
          transition-shadow
        `}
        style={{ 
          backgroundColor: config.bgColor,
          border: `2px solid ${config.color}`,
        }}
        animate={statusAnimations[currentStatus]}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleClick}
      >
        <AnimatePresence>
          {statusEffects[currentStatus]}
        </AnimatePresence>
        
        <motion.span 
          className={sizes.icon}
          animate={currentStatus === 'sleeping' ? { opacity: 0.6 } : {}}
        >
          {config.icon}
        </motion.span>
        
        {currentStatus === 'busy' && (
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{ borderColor: config.color }}
            animate={{
              boxShadow: [
                `0 0 0 0 ${config.color}40`,
                `0 0 0 10px ${config.color}00`,
              ],
            }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
      </motion.div>
      
      {showLabel && (
        <motion.span
          className={`${sizes.label} mt-1 font-medium`}
          style={{ color: config.color }}
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {config.name}
        </motion.span>
      )}
      
      <AnimatePresence>
        {showEasterEgg && (
          <motion.div
            className="absolute -top-16 left-1/2 transform -translate-x-1/2"
            initial={{ opacity: 0, scale: 0, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0, y: -20 }}
          >
            <div className="bg-gradient-to-r from-pink-500 to-purple-500 text-white px-4 py-2 rounded-full shadow-lg whitespace-nowrap">
              🎉 发现彩蛋！智能体跳舞中~
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

AgentAnimation.displayName = 'AgentAnimation';

export default AgentAnimation;
