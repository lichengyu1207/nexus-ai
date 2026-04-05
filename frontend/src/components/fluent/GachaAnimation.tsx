import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface GachaAnimationProps {
  isOpen: boolean;
  onClose: () => void;
  agent?: {
    name: string;
    avatar?: string;
    rarity: 'common' | 'rare' | 'epic' | 'legendary';
    level?: number;
    department?: string;
  };
}

const rarityConfig = {
  common: {
    color: 'from-gray-400 to-gray-600',
    glow: 'shadow-gray-400/50',
    label: '普通',
    bgEffect: 'bg-gray-500/20',
  },
  rare: {
    color: 'from-blue-400 to-blue-600',
    glow: 'shadow-blue-400/50',
    label: '稀有',
    bgEffect: 'bg-blue-500/20',
  },
  epic: {
    color: 'from-purple-400 to-purple-600',
    glow: 'shadow-purple-400/50',
    label: '史诗',
    bgEffect: 'bg-purple-500/20',
  },
  legendary: {
    color: 'from-fluent-gold-400 to-fluent-gold-600',
    glow: 'shadow-fluent-gold-400/50',
    label: '传说',
    bgEffect: 'bg-fluent-gold-500/20',
  },
};

const GachaAnimation: React.FC<GachaAnimationProps> = ({ isOpen, onClose, agent }) => {
  const [phase, setPhase] = useState<'scroll' | 'reveal' | 'result'>('scroll');

  const config = agent ? rarityConfig[agent.rarity] : rarityConfig.common;

  const handleAnimationComplete = () => {
    if (phase === 'scroll') {
      setTimeout(() => setPhase('reveal'), 500);
    } else if (phase === 'reveal') {
      setTimeout(() => setPhase('result'), 800);
    }
  };

  const handleClose = () => {
    setPhase('scroll');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={phase === 'result' ? handleClose : undefined}
      >
        {phase === 'scroll' && (
          <motion.div
            className="relative"
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.5, opacity: 0 }}
            onAnimationComplete={handleAnimationComplete}
          >
            <div className="w-64 h-96 bg-gradient-to-b from-amber-100 to-amber-200 rounded-lg shadow-2xl relative overflow-hidden border-4 border-amber-700">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-48 h-80 bg-amber-50 rounded border-2 border-amber-600 flex items-center justify-center">
                  <motion.div
                    className="text-6xl"
                    animate={{ rotate: [0, 10, -10, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity }}
                  >
                    📜
                  </motion.div>
                </div>
              </div>
              <motion.div
                className="absolute inset-x-0 top-0 h-full bg-gradient-to-b from-amber-300/50 to-transparent"
                animate={{ y: [-100, 400] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            </div>
            <motion.div
              className="absolute -inset-4 rounded-xl"
              animate={{
                boxShadow: [
                  '0 0 20px rgba(212,175,55,0.3)',
                  '0 0 60px rgba(212,175,55,0.6)',
                  '0 0 20px rgba(212,175,55,0.3)',
                ],
              }}
              transition={{ duration: 1, repeat: Infinity }}
            />
          </motion.div>
        )}

        {phase === 'reveal' && (
          <motion.div
            className="relative"
            initial={{ scale: 1.5, rotateY: 180 }}
            animate={{ scale: 1, rotateY: 0 }}
            transition={{ duration: 0.8 }}
            onAnimationComplete={handleAnimationComplete}
          >
            <div className={`w-80 h-96 rounded-2xl bg-gradient-to-br ${config.color} p-1`}>
              <div className="w-full h-full bg-white rounded-xl flex flex-col items-center justify-center p-6">
                <motion.div
                  className="text-8xl mb-4"
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                >
                  ✨
                </motion.div>
                <motion.div
                  className="text-2xl font-bold text-fluent-deepOcean-500"
                  animate={{ opacity: [0, 1] }}
                  transition={{ duration: 0.3 }}
                >
                  {config.label}
                </motion.div>
              </div>
            </div>
            <motion.div
              className="absolute -inset-8 pointer-events-none"
              animate={{
                background: [
                  'radial-gradient(circle, rgba(212,175,55,0.3) 0%, transparent 70%)',
                  'radial-gradient(circle, rgba(212,175,55,0.6) 0%, transparent 70%)',
                  'radial-gradient(circle, rgba(212,175,55,0.3) 0%, transparent 70%)',
                ],
              }}
              transition={{ duration: 0.5, repeat: Infinity }}
            />
          </motion.div>
        )}

        {phase === 'result' && agent && (
          <motion.div
            className="relative"
            initial={{ scale: 0, y: 50 }}
            animate={{ scale: 1, y: 0 }}
            transition={{ type: 'spring', damping: 15 }}
          >
            <div className={`w-80 rounded-2xl bg-gradient-to-br ${config.color} p-1 shadow-2xl ${config.glow}`}>
              <div className="w-full bg-white rounded-xl p-6">
                <div className="text-center">
                  <motion.div
                    className="relative inline-block"
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <img
                      src={agent.avatar || '/default-avatar.png'}
                      alt={agent.name}
                      className="w-32 h-32 rounded-full mx-auto border-4 border-fluent-gold-400 shadow-lg"
                    />
                    <motion.div
                      className="absolute inset-0 rounded-full border-4 border-fluent-gold-400"
                      animate={{ scale: [1, 1.1, 1], opacity: [1, 0.5, 1] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    />
                  </motion.div>
                  <h2 className="text-2xl font-bold mt-4 text-fluent-deepOcean-500">
                    {agent.name}
                  </h2>
                  <div className="flex justify-center gap-2 mt-2">
                    <span className={`px-3 py-1 rounded-full text-white text-sm bg-gradient-to-r ${config.color}`}>
                      {config.label}
                    </span>
                    {agent.level && (
                      <span className="px-3 py-1 rounded-full bg-fluent-gold-100 text-fluent-gold-600 text-sm font-medium">
                        Lv.{agent.level}
                      </span>
                    )}
                  </div>
                  {agent.department && (
                    <p className="text-gray-500 mt-2">{agent.department}</p>
                  )}
                </div>
                <motion.button
                  className="w-full mt-6 py-3 bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-white font-semibold rounded-xl"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleClose}
                >
                  确认招募
                </motion.button>
              </div>
            </div>
            <motion.div
              className="absolute -inset-4 pointer-events-none"
              animate={{
                boxShadow: [
                  `0 0 30px ${config.glow.replace('shadow-', '').replace('/50', '')}`,
                  `0 0 60px ${config.glow.replace('shadow-', '').replace('/50', '')}`,
                  `0 0 30px ${config.glow.replace('shadow-', '').replace('/50', '')}`,
                ],
              }}
              transition={{ duration: 1.5, repeat: Infinity }}
            />
          </motion.div>
        )}

        {phase === 'result' && (
          <motion.div
            className="absolute inset-0 pointer-events-none overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {[...Array(20)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 bg-fluent-gold-400 rounded-full"
                initial={{
                  x: Math.random() * window.innerWidth,
                  y: -10,
                  opacity: 1,
                }}
                animate={{
                  y: window.innerHeight + 10,
                  opacity: [1, 0],
                }}
                transition={{
                  duration: 2 + Math.random() * 2,
                  delay: Math.random() * 0.5,
                  repeat: Infinity,
                }}
              />
            ))}
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default GachaAnimation;
