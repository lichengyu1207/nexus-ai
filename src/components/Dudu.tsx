import React from 'react';
import { motion } from 'framer-motion';

type ActionType = 'wave' | 'think' | 'happy' | 'alert' | 'celebrate' | 'confused';
type PositionType = 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left' | 'center';

interface DuduProps {
  action?: ActionType;
  position?: PositionType;
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  onClick?: () => void;
}

const POSITION_MAP = {
  'bottom-right': 'bottom-4 right-4',
  'bottom-left': 'bottom-4 left-4',
  'top-right': 'top-4 right-4',
  'top-left': 'top-4 left-4',
  'center': 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2',
};

const SIZE_MAP = {
  sm: 'w-12 h-12',
  md: 'w-16 h-16',
  lg: 'w-24 h-24',
};

const ACTION_CONFIGS = {
  wave: {
    emoji: '👋',
    containerAnimation: {
      rotate: [0, 10, -10, 0],
    },
    duration: 2,
  },
  think: {
    emoji: '🤔',
    containerAnimation: {
      y: [0, -5, 0],
    },
    duration: 1.5,
  },
  happy: {
    emoji: '🎉',
    containerAnimation: {
      scale: [1, 1.1, 1],
    },
    duration: 1,
  },
  alert: {
    emoji: '⚠️',
    containerAnimation: {
      x: [0, -5, 5, 0],
    },
    duration: 0.5,
  },
  celebrate: {
    emoji: '🎊',
    containerAnimation: {
      rotate: [0, 10, -10, 0],
      y: [0, -10, 0],
    },
    duration: 0.8,
  },
  confused: {
    emoji: '😵',
    containerAnimation: {
      rotate: [0, 5, -5, 0],
    },
    duration: 1,
  },
};

const DUDU_MESSAGES = {
  wave: '嘟嘟带你，读懂房市！',
  think: '都督正在推演中...',
  happy: '恭喜主公！',
  alert: '风险预警！',
  celebrate: '太棒了！',
  confused: '嘟嘟迷路了...',
};

export const Dudu: React.FC<DuduProps> = ({
  action = 'wave',
  position = 'bottom-right',
  size = 'md',
  message,
  onClick,
}) => {
  const config = ACTION_CONFIGS[action];
  const displayMessage = message || DUDU_MESSAGES[action];

  return (
    <motion.div
      className={`fixed ${POSITION_MAP[position]} z-50 cursor-pointer`}
      animate={config.containerAnimation}
      transition={{ 
        duration: config.duration, 
        repeat: Infinity, 
        ease: 'easeInOut' 
      }}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
    >
      <div className={`relative ${SIZE_MAP[size]} flex flex-col items-center`}>
        {/* 消息气泡 */}
        {displayMessage && (
          <motion.div
            className="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-white px-3 py-1.5 rounded-full text-xs whitespace-nowrap shadow-lg border border-amber-200"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            {displayMessage}
          </motion.div>
        )}
        
        {/* 熊猫主体 */}
        <motion.div
          className="w-full h-full rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-lg"
          style={{ border: '3px solid #B45C42' }}
          whileHover={{ rotate: [0, -5, 5, 0] }}
          transition={{ duration: 0.3 }}
        >
          <span className="text-2xl">🐼</span>
        </motion.div>
        
        {/* 动作表情 */}
        <motion.div
          className="absolute -bottom-1 -right-1 text-lg"
          animate={{ 
            scale: [1, 1.2, 1],
            rotate: [0, 10, -10, 0]
          }}
          transition={{ 
            duration: 1.5, 
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        >
          {config.emoji}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default Dudu;
