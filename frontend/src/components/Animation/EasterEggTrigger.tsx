/**
 * 彩蛋触发器组件
 * Easter Egg Trigger Component
 * 
 * 监听特定操作序列，触发隐藏彩蛋
 */

import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface EasterEgg {
  id: string;
  name: string;
  trigger: {
    type: 'click_sequence' | 'konami' | 'text_input' | 'time_based' | 'custom';
    sequence?: string[];
    target?: string;
    timePattern?: { hour: number; minute: number };
    customChecker?: () => boolean;
  };
  animation: {
    type: 'confetti' | 'dance' | 'particles' | 'custom';
    duration: number;
    customComponent?: React.ReactNode;
  };
  sound?: string;
  maxTriggersPerDay: number;
  cooldown: number;
}

export interface EasterEggTriggerProps {
  eggs: EasterEgg[];
  onTrigger?: (egg: EasterEgg) => void;
  children?: React.ReactNode;
}

interface TriggerState {
  clickCounts: Record<string, number>;
  lastClickTime: Record<string, number>;
  inputBuffer: string;
  triggeredToday: Record<string, number>;
  lastResetDate: string;
}

const defaultEggs: EasterEgg[] = [
  {
    id: 'agent_dance',
    name: '智能体跳舞',
    trigger: {
      type: 'click_sequence',
      target: 'agent',
      sequence: ['click', 'click', 'click', 'click', 'click', 'click', 'click', 'click', 'click', 'click'],
    },
    animation: {
      type: 'dance',
      duration: 3000,
    },
    maxTriggersPerDay: 3,
    cooldown: 60000,
  },
  {
    id: 'konami',
    name: '科乐美秘籍',
    trigger: {
      type: 'konami',
      sequence: ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'],
    },
    animation: {
      type: 'confetti',
      duration: 5000,
    },
    maxTriggersPerDay: 1,
    cooldown: 300000,
  },
];

const ConfettiAnimation: React.FC<{ duration: number }> = memo(({ duration }) => {
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'];
  const confettiCount = 100;

  return (
    <motion.div
      className="fixed inset-0 pointer-events-none z-[9999]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {[...Array(confettiCount)].map((_, i) => {
        const color = colors[i % colors.length];
        const startX = Math.random() * window.innerWidth;
        const delay = Math.random() * 0.5;

        return (
          <motion.div
            key={i}
            className="absolute"
            style={{
              left: startX,
              top: -20,
              width: 10,
              height: 10,
              backgroundColor: color,
              borderRadius: Math.random() > 0.5 ? '50%' : '0',
            }}
            initial={{ y: -20, rotate: 0, opacity: 1 }}
            animate={{
              y: window.innerHeight + 100,
              rotate: Math.random() * 720 - 360,
              opacity: [1, 1, 0],
            }}
            transition={{
              duration: duration / 1000,
              delay,
              ease: 'linear',
            }}
          />
        );
      })}
    </motion.div>
  );
});

ConfettiAnimation.displayName = 'ConfettiAnimation';

const DanceAnimation: React.FC<{ duration: number }> = memo(({ duration }) => (
  <motion.div
    className="fixed inset-0 pointer-events-none z-[9999] flex items-center justify-center"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
  >
    <motion.div
      className="text-8xl"
      animate={{
        y: [0, -30, 0],
        rotate: [-10, 10, -10],
        scale: [1, 1.2, 1],
      }}
      transition={{
        duration: 0.5,
        repeat: Math.floor(duration / 500),
        ease: 'easeInOut',
      }}
    >
      🕺
    </motion.div>
    <motion.div
      className="absolute text-6xl"
      style={{ left: '30%' }}
      animate={{
        y: [0, -20, 0],
        rotate: [10, -10, 10],
      }}
      transition={{
        duration: 0.4,
        repeat: Math.floor(duration / 400),
        ease: 'easeInOut',
      }}
    >
      💃
    </motion.div>
    <motion.div
      className="absolute text-6xl"
      style={{ right: '30%' }}
      animate={{
        y: [0, -25, 0],
        rotate: [-5, 5, -5],
      }}
      transition={{
        duration: 0.45,
        repeat: Math.floor(duration / 450),
        ease: 'easeInOut',
      }}
    >
      🎉
    </motion.div>
  </motion.div>
));

DanceAnimation.displayName = 'DanceAnimation';

const ParticlesAnimation: React.FC<{ duration: number }> = memo(({ duration }) => (
  <motion.div
    className="fixed inset-0 pointer-events-none z-[9999]"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
  >
    {[...Array(50)].map((_, i) => (
      <motion.div
        key={i}
        className="absolute w-2 h-2 rounded-full bg-gradient-to-r from-pink-500 to-purple-500"
        style={{
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 100}%`,
        }}
        initial={{ scale: 0, opacity: 0 }}
        animate={{
          scale: [0, 2, 0],
          opacity: [0, 1, 0],
        }}
        transition={{
          duration: duration / 1000,
          delay: Math.random() * 0.5,
          ease: 'easeOut',
        }}
      />
    ))}
  </motion.div>
));

ParticlesAnimation.displayName = 'ParticlesAnimation';

const EasterEggNotification: React.FC<{
  egg: EasterEgg;
  onClose: () => void;
}> = memo(({ egg, onClose }) => (
  <motion.div
    className="fixed top-4 left-1/2 transform -translate-x-1/2 z-[9999]"
    initial={{ opacity: 0, y: -50 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -50 }}
  >
    <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-full shadow-lg flex items-center gap-3">
      <span className="text-2xl">🎉</span>
      <span className="font-medium">发现彩蛋: {egg.name}</span>
      <button
        onClick={onClose}
        className="ml-2 w-6 h-6 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center"
      >
        ✕
      </button>
    </div>
  </motion.div>
));

EasterEggNotification.displayName = 'EasterEggNotification';

const EasterEggTrigger: React.FC<EasterEggTriggerProps> = memo(({
  eggs = defaultEggs,
  onTrigger,
  children,
}) => {
  const [activeEgg, setActiveEgg] = useState<EasterEgg | null>(null);
  const [showNotification, setShowNotification] = useState(false);
  const stateRef = useRef<TriggerState>({
    clickCounts: {},
    lastClickTime: {},
    inputBuffer: '',
    triggeredToday: {},
    lastResetDate: new Date().toDateString(),
  });

  const checkAndResetDaily = useCallback(() => {
    const today = new Date().toDateString();
    if (stateRef.current.lastResetDate !== today) {
      stateRef.current.triggeredToday = {};
      stateRef.current.lastResetDate = today;
    }
  }, []);

  const canTrigger = useCallback((egg: EasterEgg): boolean => {
    checkAndResetDaily();

    const state = stateRef.current;
    const triggeredCount = state.triggeredToday[egg.id] || 0;

    if (triggeredCount >= egg.maxTriggersPerDay) {
      return false;
    }

    const lastTrigger = state.lastClickTime[egg.id] || 0;
    if (Date.now() - lastTrigger < egg.cooldown) {
      return false;
    }

    return true;
  }, [checkAndResetDaily]);

  const triggerEgg = useCallback((egg: EasterEgg) => {
    if (!canTrigger(egg)) return;

    stateRef.current.triggeredToday[egg.id] = (stateRef.current.triggeredToday[egg.id] || 0) + 1;
    stateRef.current.lastClickTime[egg.id] = Date.now();

    setActiveEgg(egg);
    setShowNotification(true);
    onTrigger?.(egg);

    setTimeout(() => {
      setActiveEgg(null);
    }, egg.animation.duration);

    setTimeout(() => {
      setShowNotification(false);
    }, 3000);
  }, [canTrigger, onTrigger]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const state = stateRef.current;
      state.inputBuffer += e.key;
      
      if (state.inputBuffer.length > 20) {
        state.inputBuffer = state.inputBuffer.slice(-20);
      }

      eggs.forEach(egg => {
        if (egg.trigger.type === 'konami' && egg.trigger.sequence) {
          const sequence = egg.trigger.sequence.join('');
          if (state.inputBuffer.endsWith(sequence)) {
            triggerEgg(egg);
            state.inputBuffer = '';
          }
        }
      });
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [eggs, triggerEgg]);

  const handleElementClick = useCallback((elementId: string) => {
    const state = stateRef.current;
    const key = elementId;
    state.clickCounts[key] = (state.clickCounts[key] || 0) + 1;

    eggs.forEach(egg => {
      if (egg.trigger.type === 'click_sequence' && egg.trigger.target === elementId) {
        const requiredClicks = egg.trigger.sequence?.length || 10;
        if (state.clickCounts[key] >= requiredClicks) {
          triggerEgg(egg);
          state.clickCounts[key] = 0;
        }
      }
    });
  }, [eggs, triggerEgg]);

  const renderAnimation = () => {
    if (!activeEgg) return null;

    switch (activeEgg.animation.type) {
      case 'confetti':
        return <ConfettiAnimation duration={activeEgg.animation.duration} />;
      case 'dance':
        return <DanceAnimation duration={activeEgg.animation.duration} />;
      case 'particles':
        return <ParticlesAnimation duration={activeEgg.animation.duration} />;
      case 'custom':
        return activeEgg.animation.customComponent;
      default:
        return null;
    }
  };

  return (
    <>
      {children}
      
      <AnimatePresence>
        {activeEgg && renderAnimation()}
        {showNotification && activeEgg && (
          <EasterEggNotification
            egg={activeEgg}
            onClose={() => setShowNotification(false)}
          />
        )}
      </AnimatePresence>
    </>
  );
});

EasterEggTrigger.displayName = 'EasterEggTrigger';

export const useEasterEggTrigger = () => {
  const handleClick = useCallback((elementId: string) => {
    const event = new CustomEvent('easter-egg-click', { detail: { elementId } });
    window.dispatchEvent(event);
  }, []);

  return { handleClick };
};

export default EasterEggTrigger;
