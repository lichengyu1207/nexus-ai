import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AnimationTrilogyProps {
  onComplete: () => void;
  duration?: number;
}

const AnimationTrilogy: React.FC<AnimationTrilogyProps> = ({
  onComplete,
  duration = 6000
}) => {
  const [currentPhase, setCurrentPhase] = useState(0);

  const phases = [
    {
      id: 1,
      title: '数据采集',
      subtitle: 'Data Collection',
      icon: '📊',
      color: 'from-blue-500 to-cyan-500',
      description: '正在收集和分析相关数据...'
    },
    {
      id: 2,
      title: '智能推理',
      subtitle: 'AI Reasoning',
      icon: '🧠',
      color: 'from-purple-500 to-pink-500',
      description: 'AI模型正在进行深度推理...'
    },
    {
      id: 3,
      title: '报告生成',
      subtitle: 'Report Generation',
      icon: '📝',
      color: 'from-green-500 to-emerald-500',
      description: '正在生成最终分析报告...'
    }
  ];

  useEffect(() => {
    const phaseDuration = duration / 3;
    const timer = setInterval(() => {
      setCurrentPhase(prev => {
        if (prev >= 2) {
          clearInterval(timer);
          setTimeout(onComplete, 500);
          return prev;
        }
        return prev + 1;
      });
    }, phaseDuration);

    return () => clearInterval(timer);
  }, [duration, onComplete]);

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="w-full max-w-4xl px-8">
        {/* Progress dots */}
        <div className="flex justify-center gap-4 mb-12">
          {phases.map((phase, index) => (
            <motion.div
              key={phase.id}
              initial={{ scale: 0.8, opacity: 0.3 }}
              animate={{
                scale: currentPhase === index ? 1.2 : 1,
                opacity: currentPhase >= index ? 1 : 0.3
              }}
              className={`w-3 h-3 rounded-full bg-gradient-to-r ${phase.color}`}
            />
          ))}
        </div>

        {/* Main content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentPhase}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            {/* Icon */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1, rotate: [0, 10, -10, 0] }}
              transition={{ duration: 0.5 }}
              className="text-8xl mb-8"
            >
              {phases[currentPhase].icon}
            </motion.div>

            {/* Title */}
            <motion.h2
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className={`text-4xl font-bold bg-gradient-to-r ${phases[currentPhase].color} bg-clip-text text-transparent mb-4`}
            >
              {phases[currentPhase].title}
            </motion.h2>

            {/* Subtitle */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-gray-400 text-lg mb-6"
            >
              {phases[currentPhase].subtitle}
            </motion.p>

            {/* Description */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-gray-300"
            >
              {phases[currentPhase].description}
            </motion.p>

            {/* Progress bar */}
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ duration: duration / 3000 }}
              className={`h-1 bg-gradient-to-r ${phases[currentPhase].color} rounded-full mt-8`}
            />
          </motion.div>
        </AnimatePresence>

        {/* Phase indicators */}
        <div className="flex justify-center gap-8 mt-12">
          {phases.map((phase, index) => (
            <motion.div
              key={phase.id}
              initial={{ opacity: 0.3 }}
              animate={{
                opacity: currentPhase >= index ? 1 : 0.3,
                scale: currentPhase === index ? 1.1 : 1
              }}
              className="text-center"
            >
              <div className={`text-2xl mb-2 ${currentPhase >= index ? '' : 'grayscale opacity-50'}`}>
                {phase.icon}
              </div>
              <div className={`text-sm ${currentPhase >= index ? 'text-white' : 'text-gray-500'}`}>
                {phase.title}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AnimationTrilogy;
