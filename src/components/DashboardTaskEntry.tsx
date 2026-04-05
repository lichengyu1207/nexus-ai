import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import CharacterAvatar from './CharacterAvatar';
import Dudu from './Dudu';

interface DashboardTaskEntryProps {
  persona?: 'zhouyu' | 'luxun';
}

const PERSONA_CONFIGS = {
  zhouyu: {
    name: '周瑜',
    buttonText: '调兵遣将',
    welcomeText: '让周瑜都督为您调兵遣将',
    colorPrimary: '#1E3A5F',
  },
  luxun: {
    name: '陆逊',
    buttonText: '布阵发令',
    welcomeText: '让陆逊都督为您布阵发令',
    colorPrimary: '#2C5F2D',
  },
};

export const DashboardTaskEntry: React.FC<DashboardTaskEntryProps> = ({
  persona = 'zhouyu',
}) => {
  const navigate = useNavigate();
  const config = PERSONA_CONFIGS[persona];

  const handleClick = () => {
    navigate('/task-analysis');
  };

  return (
    <motion.div
      className="relative bg-gradient-to-r from-primary-50 to-white rounded-2xl p-6 shadow-lg overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h3 className="text-2xl font-bold mb-2">开始新的房产分析</h3>
          <p className="text-gray-600 mb-4">{config.welcomeText}</p>
          <motion.button
            onClick={handleClick}
            className="text-white px-6 py-3 rounded-full font-semibold shadow-lg"
            style={{ backgroundColor: config.colorPrimary }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {config.buttonText}
          </motion.button>
        </div>
        <div className="flex items-center gap-4">
          <CharacterAvatar persona={persona} emotion="default" size="lg" />
          <Dudu action="wave" position="bottom-right" size="sm" />
        </div>
      </div>
    </motion.div>
  );
};

export default DashboardTaskEntry;
