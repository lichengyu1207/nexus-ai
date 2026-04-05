import React from 'react';
import { motion } from 'framer-motion';

interface CharacterAvatarProps {
  persona: 'zhouyu' | 'luxun' | string;
  emotion?: 'default' | 'thinking' | 'happy' | 'serious';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const personaConfig = {
  zhouyu: {
    name: '周瑜',
    title: '东吴大都督',
    color: 'from-red-500 to-orange-500',
    bgColor: 'bg-gradient-to-br from-red-50 to-orange-50',
    borderColor: 'border-red-200',
    avatar: '🦅',
    description: '儒雅从容、足智多谋',
  },
  luxun: {
    name: '陆逊',
    title: '东吴名将',
    color: 'from-blue-500 to-cyan-500',
    bgColor: 'bg-gradient-to-br from-blue-50 to-cyan-50',
    borderColor: 'border-blue-200',
    avatar: '🛡️',
    description: '沉稳内敛、心思缜密',
  },
};

const emotionStyles = {
  default: { scale: 1, rotate: 0 },
  thinking: { scale: 1.05, rotate: -5 },
  happy: { scale: 1.1, rotate: 5 },
  serious: { scale: 1, rotate: 0 },
};

const sizeConfig = {
  sm: { container: 'w-10 h-10', text: 'text-xs', avatar: 'text-lg' },
  md: { container: 'w-14 h-14', text: 'text-sm', avatar: 'text-2xl' },
  lg: { container: 'w-20 h-20', text: 'text-base', avatar: 'text-4xl' },
};

export const CharacterAvatar: React.FC<CharacterAvatarProps> = ({
  persona,
  emotion = 'default',
  size = 'md',
  className = '',
}) => {
  const config = personaConfig[persona as keyof typeof personaConfig] || personaConfig.zhouyu;
  const emotionStyle = emotionStyles[emotion];
  const sizeStyle = sizeConfig[size];

  return (
    <motion.div
      className={`
        relative ${sizeStyle.container} rounded-full
        ${config.bgColor} border-2 ${config.borderColor}
        flex items-center justify-center
        shadow-lg cursor-pointer
        ${className}
      `}
      animate={emotionStyle}
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
    >
      <span className={sizeStyle.avatar}>{config.avatar}</span>
      
      {emotion === 'thinking' && (
        <motion.div
          className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ repeat: Infinity, duration: 1 }}
        />
      )}
    </motion.div>
  );
};

export const CharacterCard: React.FC<{
  persona: string;
  showDescription?: boolean;
}> = ({ persona, showDescription = true }) => {
  const config = personaConfig[persona as keyof typeof personaConfig] || personaConfig.zhouyu;

  return (
    <div className={`${config.bgColor} rounded-xl p-4 border ${config.borderColor}`}>
      <div className="flex items-center gap-3">
        <CharacterAvatar persona={persona} size="lg" />
        <div>
          <h3 className="font-bold text-gray-900">{config.name}</h3>
          <p className="text-sm text-gray-500">{config.title}</p>
          {showDescription && (
            <p className="text-xs text-gray-400 mt-1">{config.description}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default CharacterAvatar;
