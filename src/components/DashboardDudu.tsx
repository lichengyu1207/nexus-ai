import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

type PersonaType = 'zhouyu' | 'luxun';
type EmotionType = 'default' | 'thinking' | 'happy' | 'serious';

interface DashboardDuduProps {
  persona?: PersonaType;
  onChatClick?: () => void;
}

const PERSONA_CONFIGS = {
  zhouyu: {
    name: '周瑜',
    title: '公瑾',
    colorPrimary: '#1E3A5F',
    colorSecondary: '#D4AF37',
    greetings: [
      '主公早，今日有何吩咐？',
      '主公，瑜已备好羽扇，随时听令。',
      '今日天朗气清，正是看房好时机。',
      '卿来得正好，瑜有几处良盘欲荐。',
    ],
    tips: [
      '谈笑间，房价走势了然于胸',
      '羽扇轻摇，数据尽在掌握',
      '择一处良居，如遇知音',
    ],
  },
  luxun: {
    name: '陆逊',
    title: '伯言',
    colorPrimary: '#2C5F2D',
    colorSecondary: '#B08D57',
    greetings: [
      '主公请坐，逊有要事相商。',
      '主公，今日房市有变，需细察。',
      '时机未至，当静观其变。',
      '逊已推演多日，只待主公到来。',
    ],
    tips: [
      '静观其变，一击必中',
      '火烧连营，扫除风险',
      '不争一时，赢在长远',
    ],
  },
};

export const DashboardDudu: React.FC<DashboardDuduProps> = ({
  persona = 'zhouyu',
  onChatClick,
}) => {
  const navigate = useNavigate();
  const [emotion, setEmotion] = useState<EmotionType>('default');
  const [greeting, setGreeting] = useState('');
  const [tip, setTip] = useState('');
  const [showTooltip, setShowTooltip] = useState(false);
  const [interactionCount, setInteractionCount] = useState(0);

  const config = PERSONA_CONFIGS[persona];

  useEffect(() => {
    const hour = new Date().getHours();
    let timeGreeting = '';
    
    if (hour < 6) {
      timeGreeting = '夜深了，主公还不休息？';
    } else if (hour < 12) {
      timeGreeting = '主公早！';
    } else if (hour < 18) {
      timeGreeting = '主公午安！';
    } else {
      timeGreeting = '主公晚上好！';
    }
    
    const randomGreeting = config.greetings[Math.floor(Math.random() * config.greetings.length)];
    setGreeting(`${timeGreeting} ${randomGreeting}`);
    
    setTip(config.tips[Math.floor(Math.random() * config.tips.length)]);
  }, [persona]);

  const handleClick = () => {
    setInteractionCount(prev => prev + 1);
    setEmotion('happy');
    setShowTooltip(true);
    
    setTimeout(() => {
      setEmotion('default');
      setShowTooltip(false);
    }, 2000);
  };

  const handleChatClick = () => {
    if (onChatClick) {
      onChatClick();
    } else {
      navigate('/consult');
    }
  };

  const handleStoryClick = () => {
    navigate('/persona-story');
  };

  return (
    <div className="relative">
      {/* 主头像 */}
      <motion.div
        className="relative cursor-pointer"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleClick}
      >
        <div
          className="w-14 h-14 rounded-full flex items-center justify-center shadow-lg"
          style={{
            background: `linear-gradient(135deg, ${config.colorPrimary}, ${config.colorSecondary}40)`,
            border: `2px solid ${config.colorSecondary}`,
          }}
        >
          <span className="text-white font-bold text-lg">{config.name[0]}</span>
        </div>
        
        <motion.div
          className="absolute -right-1 -top-1 text-sm"
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ repeat: Infinity, duration: 3 }}
        >
          {persona === 'zhouyu' ? '🪭' : '⚔️'}
        </motion.div>

        {emotion === 'happy' && (
          <motion.div
            className="absolute -bottom-1 -right-1 text-sm"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
          >
            ✨
          </motion.div>
        )}
      </motion.div>

      {/* Tooltip */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            className="absolute top-full right-0 mt-2 bg-white rounded-lg shadow-lg p-3 w-48 z-50"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <p className="text-sm text-gray-700">{greeting}</p>
            <p className="text-xs text-gray-500 mt-1 italic">"{tip}"</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 快捷菜单 */}
      <motion.div
        className="absolute top-full right-0 mt-2 bg-white rounded-lg shadow-lg overflow-hidden z-40"
        initial={{ opacity: 0, scale: 0.9 }}
        whileHover={{ opacity: 1, scale: 1 }}
      >
        <button
          onClick={handleChatClick}
          className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
        >
          <span>💬</span>
          <span>开始咨询</span>
        </button>
        <button
          onClick={handleStoryClick}
          className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
        >
          <span>📖</span>
          <span>都督故事</span>
        </button>
      </motion.div>

      {/* 互动次数徽章 */}
      {interactionCount > 0 && (
        <motion.div
          className="absolute -top-2 -right-2 bg-amber-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
        >
          {interactionCount}
        </motion.div>
      )}
    </div>
  );
};

export default DashboardDudu;
