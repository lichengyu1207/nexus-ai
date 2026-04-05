/**
 * 平台启动动画组件
 * Splash Animation Component
 * 
 * 展示平台加载时的酷炫启动动画
 */

import React, { useState, useEffect, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface SplashAnimationProps {
  logo?: string;
  appName?: string;
  duration?: number;
  onComplete: () => void;
  skipEnabled?: boolean;
}

const departments = [
  { id: 'li', name: '礼部', icon: '📜', color: '#3B82F6' },
  { id: 'gong', name: '工部', icon: '📊', color: '#F97316' },
  { id: 'hu', name: '户部', icon: '💰', color: '#EAB308' },
  { id: 'bing', name: '兵部', icon: '📡', color: '#22C55E' },
  { id: 'li_guan', name: '吏部', icon: '👑', color: '#A855F7' },
  { id: 'xing', name: '刑部', icon: '🛡️', color: '#EF4444' },
];

const LogoComponent: React.FC<{ logo?: string; appName?: string }> = memo(({ logo, appName }) => (
  <motion.div
    className="flex flex-col items-center"
    initial={{ scale: 0, rotate: -180 }}
    animate={{ scale: 1, rotate: 0 }}
    transition={{ type: 'spring', stiffness: 200, damping: 20 }}
  >
    <motion.div
      className="w-32 h-32 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-2xl"
      animate={{
        boxShadow: [
          '0 0 0 0 rgba(99, 102, 241, 0.4)',
          '0 0 0 30px rgba(99, 102, 241, 0)',
        ],
      }}
      transition={{ duration: 1.5, repeat: Infinity }}
    >
      {logo ? (
        <img src={logo} alt="Logo" className="w-20 h-20" />
      ) : (
        <span className="text-5xl">🏛️</span>
      )}
    </motion.div>
    
    {appName && (
      <motion.h1
        className="mt-6 text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        {appName}
      </motion.h1>
    )}
  </motion.div>
));

LogoComponent.displayName = 'LogoComponent';

const AgentOrbit: React.FC<{
  departments: typeof departments;
  onComplete: () => void;
}> = memo(({ departments, onComplete }) => {
  const [phase, setPhase] = useState<'orbit' | 'gather' | 'complete'>('orbit');

  useEffect(() => {
    const orbitTimer = setTimeout(() => setPhase('gather'), 1500);
    const gatherTimer = setTimeout(() => setPhase('complete'), 2500);
    const completeTimer = setTimeout(onComplete, 3000);

    return () => {
      clearTimeout(orbitTimer);
      clearTimeout(gatherTimer);
      clearTimeout(completeTimer);
    };
  }, [onComplete]);

  const radius = 150;

  return (
    <div className="relative w-80 h-80">
      {departments.map((dept, index) => {
        const angle = (index / departments.length) * 2 * Math.PI - Math.PI / 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;

        return (
          <motion.div
            key={dept.id}
            className="absolute"
            style={{
              left: '50%',
              top: '50%',
            }}
            initial={{
              x: 0,
              y: 0,
              scale: 0,
              opacity: 0,
            }}
            animate={
              phase === 'orbit'
                ? {
                    x,
                    y,
                    scale: 1,
                    opacity: 1,
                  }
                : phase === 'gather'
                ? {
                    x: 0,
                    y: 0,
                    scale: 0.8,
                    opacity: 0.8,
                  }
                : {
                    x: 0,
                    y: 0,
                    scale: 0,
                    opacity: 0,
                  }
            }
            transition={{
              type: 'spring',
              stiffness: 200,
              damping: 20,
              delay: index * 0.1,
            }}
          >
            <motion.div
              className="w-16 h-16 rounded-full flex flex-col items-center justify-center shadow-lg"
              style={{ backgroundColor: `${dept.color}20`, border: `2px solid ${dept.color}` }}
              animate={
                phase === 'orbit'
                  ? {
                      y: [0, -10, 0],
                    }
                  : {}
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: index * 0.2,
              }}
            >
              <span className="text-2xl">{dept.icon}</span>
              <span className="text-xs font-medium" style={{ color: dept.color }}>
                {dept.name}
              </span>
            </motion.div>
          </motion.div>
        );
      })}
      
      <motion.div
        className="absolute left-1/2 top-1/2 w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"
        style={{ transform: 'translate(-50%, -50%)' }}
        initial={{ scale: 1 }}
        animate={phase === 'gather' ? { scale: 1.5 } : { scale: 1 }}
        transition={{ type: 'spring', stiffness: 200 }}
      >
        <span className="text-3xl">🏛️</span>
      </motion.div>
      
      {phase === 'orbit' && (
        <motion.div
          className="absolute left-1/2 top-1/2"
          style={{ transform: 'translate(-50%, -50%)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="w-80 h-80 rounded-full border-2 border-dashed border-gray-200" />
        </motion.div>
      )}
    </div>
  );
});

AgentOrbit.displayName = 'AgentOrbit';

const LoadingProgress: React.FC = memo(() => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 2;
      });
    }, 50);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-64">
      <div className="flex justify-between text-xs text-gray-500 mb-2">
        <span>系统初始化中...</span>
        <span>{progress}%</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.1 }}
        />
      </div>
    </div>
  );
});

LoadingProgress.displayName = 'LoadingProgress';

const SplashAnimation: React.FC<SplashAnimationProps> = memo(({
  logo,
  appName = '房都督',
  duration = 3000,
  onComplete,
  skipEnabled = true,
}) => {
  const [phase, setPhase] = useState<'logo' | 'agents' | 'loading'>('logo');

  useEffect(() => {
    const logoTimer = setTimeout(() => setPhase('agents'), 500);
    const agentsTimer = setTimeout(() => setPhase('loading'), duration - 1000);

    return () => {
      clearTimeout(logoTimer);
      clearTimeout(agentsTimer);
    };
  }, [duration]);

  const handleSkip = useCallback(() => {
    onComplete();
  }, [onComplete]);

  return (
    <motion.div
      className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={skipEnabled ? handleSkip : undefined}
    >
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 bg-white rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              opacity: [0.2, 1, 0.2],
              scale: [1, 1.5, 1],
            }}
            transition={{
              duration: 2 + Math.random() * 2,
              repeat: Infinity,
              delay: Math.random() * 2,
            }}
          />
        ))}
      </div>
      
      <div className="relative z-10 flex flex-col items-center">
        <AnimatePresence mode="wait">
          {phase === 'logo' && (
            <motion.div
              key="logo"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <LogoComponent logo={logo} appName={appName} />
            </motion.div>
          )}
          
          {phase === 'agents' && (
            <motion.div
              key="agents"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <AgentOrbit departments={departments} onComplete={onComplete} />
            </motion.div>
          )}
          
          {phase === 'loading' && (
            <motion.div
              key="loading"
              className="flex flex-col items-center"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <LogoComponent logo={logo} appName={appName} />
              <div className="mt-8">
                <LoadingProgress />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      
      {skipEnabled && (
        <motion.button
          className="absolute bottom-8 right-8 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          点击跳过
        </motion.button>
      )}
      
      <motion.div
        className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white/50 text-xs"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2 }}
      >
        © 2024 房都督 - 智能房产估值平台
      </motion.div>
    </motion.div>
  );
});

SplashAnimation.displayName = 'SplashAnimation';

export default SplashAnimation;
