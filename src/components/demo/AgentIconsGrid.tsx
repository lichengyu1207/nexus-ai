import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDemoStore } from '@/stores/demoStore';
import agentsData from '@/data/agentsData.json';

const AgentIconsGrid: React.FC = () => {
  const { agentsStatus, currentScene } = useDemoStore();
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null);

  const agents = agentsData.agents;

  return (
    <div className="relative p-8">
      <motion.h3
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-xl font-bold text-white mb-6 text-center"
      >
        六部智能体协同工作
      </motion.h3>
      
      <div className="grid grid-cols-3 gap-4 md:gap-6">
        {agents.map((agent, index) => {
          const status = agentsStatus[agent.id]?.status || 'idle';
          const message = agentsStatus[agent.id]?.message || '';
          const progress = agentsStatus[agent.id]?.progress || 0;
          
          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              onHoverStart={() => setHoveredAgent(agent.id)}
              onHoverEnd={() => setHoveredAgent(null)}
              className="relative"
            >
              <motion.div
                animate={{
                  scale: status === 'working' ? [1, 1.05, 1] : 1,
                }}
                transition={{
                  duration: 0.5,
                  repeat: status === 'working' ? Infinity : 0,
                }}
                className={`
                  relative p-4 rounded-2xl backdrop-blur-sm cursor-pointer
                  transition-all duration-300
                  ${status === 'working' 
                    ? 'bg-white/20 ring-2 ring-white/30' 
                    : status === 'done'
                    ? 'bg-green-500/20 ring-2 ring-green-500/50'
                    : 'bg-white/5 hover:bg-white/10'
                  }
                `}
              >
                {status === 'working' && (
                  <motion.div
                    className="absolute inset-0 rounded-2xl"
                    style={{ 
                      background: `linear-gradient(90deg, transparent, ${agent.color}20, transparent)` 
                    }}
                    animate={{ x: ['-100%', '100%'] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                  />
                )}
                
                <div className="relative z-10">
                  <div className="flex items-center justify-center mb-2">
                    <motion.div
                      animate={{ 
                        rotate: status === 'working' ? [0, 360] : 0,
                      }}
                      transition={{ 
                        duration: 2, 
                        repeat: status === 'working' ? Infinity : 0,
                        ease: 'linear',
                      }}
                      className="text-4xl"
                    >
                      {agent.icon}
                    </motion.div>
                  </div>
                  
                  <h4 className="text-white font-semibold text-center text-sm md:text-base">
                    {agent.name}
                  </h4>
                  
                  <p className="text-white/50 text-xs text-center mt-1">
                    {agent.role}
                  </p>
                  
                  {status === 'working' && message && (
                    <motion.p
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-xs text-center mt-2 text-purple-300"
                    >
                      {message}
                    </motion.p>
                  )}
                  
                  {status === 'done' && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center"
                    >
                      <span className="text-white text-sm">✓</span>
                    </motion.div>
                  )}
                </div>
                
                {status === 'working' && (
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10 rounded-b-2xl overflow-hidden">
                    <motion.div
                      className="h-full"
                      style={{ backgroundColor: agent.color }}
                      initial={{ width: '0%' }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                )}
              </motion.div>
              
              <AnimatePresence>
                {hoveredAgent === agent.id && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute z-50 left-1/2 -translate-x-1/2 top-full mt-2 w-64 p-4 bg-slate-800/95 backdrop-blur-xl rounded-xl shadow-xl border border-white/10"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">{agent.icon}</span>
                      <div>
                        <h5 className="text-white font-semibold">{agent.fullName}</h5>
                        <p className="text-white/50 text-xs">{agent.role}</p>
                      </div>
                    </div>
                    <p className="text-white/70 text-sm mb-3">{agent.description}</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-2 py-0.5 bg-white/10 rounded text-xs text-white/80"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>
      
      {currentScene === 'scene2' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-6 text-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 rounded-full">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="w-2 h-2 bg-green-400 rounded-full"
            />
            <span className="text-white/70 text-sm">智能体协同分析中...</span>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AgentIconsGrid;
