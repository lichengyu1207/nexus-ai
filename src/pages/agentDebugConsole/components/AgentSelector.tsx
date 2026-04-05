import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MagnifyingGlassIcon, PlayIcon, StopIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import type { Agent } from '../types';
import { AGENT_STATUS_CONFIG } from '../types';

interface AgentSelectorProps {
  agents: Agent[];
  selectedAgentId: string | null;
  onSelect: (agentId: string) => void;
  onStart: (agentId: string) => void;
  onStop: (agentId: string) => void;
  isLoading?: boolean;
}

export function AgentSelector({
  agents,
  selectedAgentId,
  onSelect,
  onStart,
  onStop,
  isLoading = false,
}: AgentSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  const filteredAgents = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleAgentClick = (agentId: string) => {
    onSelect(agentId);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl hover:border-amber-500/30 transition-colors min-w-[280px]"
      >
        <div className="flex items-center gap-3 flex-1">
          <div
            className={`
            w-3 h-3 rounded-full
            ${selectedAgent?.status === 'running' ? 'bg-green-400 animate-pulse' : 
              selectedAgent?.status === 'paused' ? 'bg-amber-400' : 
              selectedAgent?.status === 'error' ? 'bg-red-400' : 'bg-slate-500'}
          `}
          />
          <div className="text-left">
            <p className="text-white font-medium truncate">
              {selectedAgent?.name || '选择智能体'}
            </p>
            <p className="text-xs text-slate-400">
              {selectedAgent ? AGENT_STATUS_CONFIG[selectedAgent.status].label : '点击选择'}
            </p>
          </div>
        </div>
        <ChevronDownIcon
          className={`w-5 h-5 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700/50 rounded-xl shadow-xl z-50 max-h-80 overflow-hidden"
          >
            <div className="p-2 border-b border-slate-700/50">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="搜索智能体..."
                  className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
                />
              </div>
            </div>

            <div className="overflow-y-auto max-h-60">
              {isLoading ? (
                <div className="p-4 text-center text-slate-400 text-sm">加载中...</div>
              ) : filteredAgents.length === 0 ? (
                <div className="p-4 text-center text-slate-500 text-sm">没有找到智能体</div>
              ) : (
                filteredAgents.map((agent) => (
                  <div
                    key={agent.id}
                    onClick={() => handleAgentClick(agent.id)}
                    className={`
                      flex items-center gap-3 px-3 py-2 cursor-pointer transition-colors
                      ${selectedAgentId === agent.id ? 'bg-amber-500/20' : 'hover:bg-slate-700/50'}
                    `}
                  >
                    <div
                      className={`
                        w-2.5 h-2.5 rounded-full flex-shrink-0
                        ${agent.status === 'running' ? 'bg-green-400' : 
                          agent.status === 'paused' ? 'bg-amber-400' : 
                          agent.status === 'error' ? 'bg-red-400' : 'bg-slate-500'}
                      `}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white truncate">{agent.name}</p>
                      <p className="text-xs text-slate-400">{agent.type}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      {agent.status === 'running' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onStop(agent.id);
                          }}
                          className="p-1 text-slate-400 hover:text-red-400 transition-colors"
                        >
                          <StopIcon className="w-4 h-4" />
                        </button>
                      )}
                      {agent.status !== 'running' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onStart(agent.id);
                          }}
                          className="p-1 text-slate-400 hover:text-green-400 transition-colors"
                        >
                          <PlayIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
