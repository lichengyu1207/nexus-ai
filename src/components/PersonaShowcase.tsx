import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

type PersonaType = 'zhouyu' | 'luxun';

interface PersonaShowcaseProps {
  onPersonaSelect?: (persona: PersonaType) => void;
  showRandom?: boolean;
}

const PERSONA_CONFIGS = {
  zhouyu: {
    name: '周瑜',
    title: '公瑾',
    style: '儒雅智谋，风度翩翩',
    description: '精通地段分析、时机把握、风险评估',
    colorPrimary: '#1E3A5F',
    colorSecondary: '#D4AF37',
    emoji: '🪭',
    quote: '谈笑间，房价走势了然于胸',
    bgGradient: 'from-blue-900 via-blue-800 to-slate-900',
  },
  luxun: {
    name: '陆逊',
    title: '伯言',
    style: '沉稳隐忍，后发制人',
    description: '精通风险控制、价值洼地挖掘、长期规划',
    colorPrimary: '#2C5F2D',
    colorSecondary: '#B08D57',
    emoji: '⚔️',
    quote: '静观其变，一击必中',
    bgGradient: 'from-green-900 via-green-800 to-slate-900',
  },
};

export const PersonaShowcase: React.FC<PersonaShowcaseProps> = ({
  onPersonaSelect,
  showRandom = true,
}) => {
  const [currentPersona, setCurrentPersona] = useState<PersonaType>('zhouyu');
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (showRandom) {
      const random = Math.random() > 0.5;
      setCurrentPersona(random ? 'zhouyu' : 'luxun');
    }
  }, [showRandom]);

  const config = PERSONA_CONFIGS[currentPersona];

  const togglePersona = () => {
    setIsAnimating(true);
    setCurrentPersona(prev => prev === 'zhouyu' ? 'luxun' : 'zhouyu');
    setTimeout(() => setIsAnimating(false), 500);
  };

  return (
    <div className={`min-h-[400px] relative overflow-hidden rounded-2xl bg-gradient-to-br ${config.bgGradient}`}>
      {/* 背景装饰 */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-10 left-10 w-32 h-32 border border-white/20 rounded-full" />
        <div className="absolute bottom-10 right-10 w-48 h-48 border border-white/20 rounded-full" />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 border border-white/10 rounded-full" />
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentPersona}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -50 }}
          transition={{ duration: 0.5 }}
          className="relative z-10 p-8 flex flex-col items-center justify-center h-full"
        >
          {/* 角色头像 */}
          <motion.div
            className="relative mb-6"
            whileHover={{ scale: 1.05 }}
            onClick={togglePersona}
          >
            <div
              className="w-32 h-32 rounded-full flex items-center justify-center text-5xl shadow-2xl cursor-pointer"
              style={{
                background: `linear-gradient(135deg, ${config.colorPrimary}, ${config.colorSecondary}40)`,
                border: `3px solid ${config.colorSecondary}`,
              }}
            >
              <span className="text-white font-bold text-3xl">{config.name[0]}</span>
            </div>
            
            <motion.div
              className="absolute -right-2 -top-2 text-2xl"
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ repeat: Infinity, duration: 3 }}
            >
              {config.emoji}
            </motion.div>
          </motion.div>

          {/* 角色名称 */}
          <h2 className="text-3xl font-bold text-white mb-2">
            {config.name} · {config.title}
          </h2>
          
          <p className="text-white/80 text-sm mb-4">
            {config.style}
          </p>

          {/* 角色描述 */}
          <div className="bg-white/10 backdrop-blur-sm rounded-lg px-4 py-2 mb-4">
            <p className="text-white/90 text-sm text-center">
              {config.description}
            </p>
          </div>

          {/* 名言 */}
          <motion.p
            className="text-white/60 text-xs italic"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            "{config.quote}"
          </motion.p>

          {/* 切换按钮 */}
          <motion.button
            onClick={togglePersona}
            className="mt-6 px-4 py-2 bg-white/20 hover:bg-white/30 text-white text-sm rounded-full backdrop-blur-sm transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            切换查看另一位都督
          </motion.button>

          {/* 选择按钮 */}
          {onPersonaSelect && (
            <motion.button
              onClick={() => onPersonaSelect(currentPersona)}
              className="mt-4 px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-medium rounded-xl shadow-lg"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              选择{config.name}作为我的专属都督
            </motion.button>
          )}
        </motion.div>
      </AnimatePresence>

      {/* 嘟嘟装饰 */}
      <motion.div
        className="absolute bottom-4 left-4 text-4xl"
        animate={{ y: [0, -5, 0] }}
        transition={{ repeat: Infinity, duration: 2 }}
      >
        🐼
      </motion.div>
    </div>
  );
};

export default PersonaShowcase;
