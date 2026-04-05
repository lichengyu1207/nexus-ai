import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import agentsData from '@/data/agentsData.json';

interface DynamicInputProps {
  onStart: (input?: string) => void;
}

const DynamicInput: React.FC<DynamicInputProps> = ({ onStart }) => {
  const [inputValue, setInputValue] = useState('帮我分析深圳南山区学区房');
  const [isTyping, setIsTyping] = useState(false);
  const [showBeams, setShowBeams] = useState(false);
  const [cursorVisible, setCursorVisible] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setCursorVisible((prev) => !prev);
    }, 530);
    return () => clearInterval(interval);
  }, []);

  const handlePresetClick = (text: string) => {
    setInputValue(text);
    setIsTyping(true);
    setTimeout(() => setIsTyping(false), 500);
  };

  const handleSubmit = useCallback(() => {
    if (!inputValue.trim()) return;
    setShowBeams(true);
    setTimeout(() => {
      onStart(inputValue);
    }, 1500);
  }, [inputValue, onStart]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto relative">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
      >
        <div className="relative backdrop-blur-xl bg-white/10 rounded-2xl border border-white/20 shadow-2xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-blue-500/10 animate-pulse" />
          
          <div className="relative p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-white/50 text-sm ml-2">房都督智能分析终端</span>
            </div>
            
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={showBeams}
                className="w-full bg-transparent text-white text-lg placeholder-white/30 outline-none pr-12"
                placeholder="输入您的房产分析需求..."
              />
              <span
                className={`absolute right-0 top-0 text-purple-400 text-lg ${
                  cursorVisible && !showBeams ? 'opacity-100' : 'opacity-0'
                }`}
              >
                |
              </span>
            </div>
            
            <div className="flex flex-wrap gap-2 mt-4">
              {agentsData.presets.map((preset) => (
                <motion.button
                  key={preset.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handlePresetClick(preset.text)}
                  disabled={showBeams}
                  className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white/80 backdrop-blur-sm transition-colors flex items-center gap-1"
                >
                  <span>{preset.icon}</span>
                  <span>{preset.text.slice(0, 15)}...</span>
                </motion.button>
              ))}
            </div>
          </div>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSubmit}
          disabled={showBeams || !inputValue.trim()}
          className="mt-4 w-full py-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 text-white rounded-xl text-lg font-semibold shadow-lg shadow-purple-500/30 transition-all"
        >
          {showBeams ? (
            <span className="flex items-center justify-center gap-2">
              <motion.span
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              >
                ⚡
              </motion.span>
              智能体正在解析...
            </span>
          ) : (
            '开始分析 →'
          )}
        </motion.button>
      </motion.div>

      <AnimatePresence>
        {showBeams && (
          <LightBeamsAnimation agents={agentsData.agents} />
        )}
      </AnimatePresence>
    </div>
  );
};

const LightBeamsAnimation: React.FC<{ agents: Array<{ id: string; color: string }> }> = ({ agents }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 pointer-events-none overflow-visible"
    >
      <svg className="absolute inset-0 w-full h-full" style={{ overflow: 'visible' }}>
        {agents.slice(0, 6).map((agent, index) => {
          const startX = 50;
          const startY = 0;
          const positions = [
            { x: -150, y: 200 },
            { x: -50, y: 200 },
            { x: 50, y: 200 },
            { x: 150, y: 200 },
            { x: -100, y: 300 },
            { x: 100, y: 300 },
          ];
          const pos = positions[index];
          
          return (
            <motion.path
              key={agent.id}
              d={`M ${startX} ${startY} Q ${startX + pos.x / 2} ${startY + 100} ${startX + pos.x} ${startY + pos.y}`}
              stroke={agent.color}
              strokeWidth="3"
              fill="none"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: [0, 1, 1, 0] }}
              transition={{
                pathLength: { duration: 1, delay: index * 0.1 },
                opacity: { duration: 1.5, delay: index * 0.1 },
              }}
              strokeLinecap="round"
            />
          );
        })}
      </svg>
      
      {agents.slice(0, 6).map((agent, index) => {
        const positions = [
          { x: -150, y: 200 },
          { x: -50, y: 200 },
          { x: 50, y: 200 },
          { x: 150, y: 200 },
          { x: -100, y: 300 },
          { x: 100, y: 300 },
        ];
        const pos = positions[index];
        
        return (
          <motion.div
            key={`particle-${agent.id}`}
            className="absolute w-4 h-4 rounded-full"
            style={{
              backgroundColor: agent.color,
              boxShadow: `0 0 20px ${agent.color}, 0 0 40px ${agent.color}`,
            }}
            initial={{ 
              x: 0, 
              y: 0, 
              scale: 0,
              opacity: 0 
            }}
            animate={{ 
              x: pos.x, 
              y: pos.y, 
              scale: [0, 1.5, 1],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: 1.2,
              delay: index * 0.15,
              ease: 'easeOut',
            }}
          />
        );
      })}
    </motion.div>
  );
};

export default DynamicInput;
