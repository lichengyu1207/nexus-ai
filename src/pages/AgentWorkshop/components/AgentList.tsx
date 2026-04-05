import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { Agent } from '../types';

interface AgentListProps {
  agents: Agent[];
  selectedAgentId: string;
  onSelectAgent: (id: string) => void;
  isLoading?: boolean;
}

const statusColors = {
  healthy: 'bg-green-500',
  busy: 'bg-yellow-500',
  error: 'bg-red-500',
};

const statusLabels = {
  healthy: '健康',
  busy: '繁忙',
  error: '异常',
};

const departmentLabels = {
  san: '三省',
  liu: '六部',
};

const AgentCard: React.FC<{
  agent: Agent;
  isSelected: boolean;
  onClick: () => void;
}> = ({ agent, isSelected, onClick }) => {
  return (
    <motion.button
      onClick={onClick}
      className={clsx(
        'w-full text-left p-3 rounded-lg border transition-all duration-200',
        'bg-bg-secondary/60 backdrop-blur-md',
        isSelected
          ? 'border-primary/70 shadow-lg shadow-primary/10'
          : 'border-border-light hover:border-primary/30 hover:bg-bg-secondary/80'
      )}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      role="button"
      tabIndex={0}
      aria-label={`智能体: ${agent.name}, 状态: ${statusLabels[agent.status]}, 当前任务: ${agent.currentTasks}`}
      aria-pressed={isSelected}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div
            className={clsx(
              'w-2.5 h-2.5 rounded-full',
              statusColors[agent.status],
              agent.status === 'busy' && 'animate-pulse'
            )}
            aria-hidden="true"
          />
          <span className="font-medium text-text-primary">{agent.name}</span>
        </div>
        <span className="text-xs text-text-secondary px-2 py-0.5 rounded bg-bg-tertiary">
          {departmentLabels[agent.department]}
        </span>
      </div>

      <p className="text-xs text-text-secondary line-clamp-2 mb-2">{agent.description}</p>

      <div className="flex items-center justify-between text-xs text-text-secondary">
        <div className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span>{agent.currentTasks} 任务</span>
        </div>
        <span className={clsx(
          'text-xs',
          agent.status === 'healthy' && 'text-green-400',
          agent.status === 'busy' && 'text-yellow-400',
          agent.status === 'error' && 'text-red-400'
        )}>
          {statusLabels[agent.status]}
        </span>
      </div>
    </motion.button>
  );
};

const LoadingSkeleton: React.FC = () => (
  <div className="space-y-3">
    {[1, 2, 3].map((i) => (
      <div
        key={i}
        className="w-full h-24 rounded-lg bg-bg-secondary/40 animate-pulse border border-border-light"
      />
    ))}
  </div>
);

export const AgentList: React.FC<AgentListProps> = ({
  agents,
  selectedAgentId,
  onSelectAgent,
  isLoading,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterByStatus, setFilterByStatus] = useState<'all' | 'healthy' | 'busy' | 'error'>('all');
  const [filterByDepartment, setFilterByDepartment] = useState<'all' | 'san' | 'liu'>('all');

  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterByStatus === 'all' || agent.status === filterByStatus;
      const matchesDepartment = filterByDepartment === 'all' || agent.department === filterByDepartment;
      return matchesSearch && matchesStatus && matchesDepartment;
    });
  }, [agents, searchTerm, filterByStatus, filterByDepartment]);

  const groupedAgents = useMemo(() => {
    const san = filteredAgents.filter((a) => a.department === 'san');
    const liu = filteredAgents.filter((a) => a.department === 'liu');
    return { san, liu };
  }, [filteredAgents]);

  if (isLoading) {
    return (
      <div className="w-[280px] h-full bg-bg-primary/50 backdrop-blur-md border-r border-border-light p-4">
        <LoadingSkeleton />
      </div>
    );
  }

  return (
    <div className="w-[280px] h-full bg-bg-primary/50 backdrop-blur-md border-r border-border-light flex flex-col">
      <div className="p-4 border-b border-border-light">
        <h2 className="text-lg font-semibold text-text-primary mb-3">智能体工坊</h2>
        
        <div className="relative mb-3">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="搜索智能体..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-bg-secondary/60 border border-border-light rounded-lg text-text-primary placeholder-text-secondary focus:outline-none focus:border-primary/50 transition-colors"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={filterByStatus}
            onChange={(e) => setFilterByStatus(e.target.value as typeof filterByStatus)}
            className="flex-1 px-2 py-1.5 text-xs bg-bg-secondary/60 border border-border-light rounded-lg text-text-primary focus:outline-none focus:border-primary/50"
          >
            <option value="all">全部状态</option>
            <option value="healthy">健康</option>
            <option value="busy">繁忙</option>
            <option value="error">异常</option>
          </select>
          <select
            value={filterByDepartment}
            onChange={(e) => setFilterByDepartment(e.target.value as typeof filterByDepartment)}
            className="flex-1 px-2 py-1.5 text-xs bg-bg-secondary/60 border border-border-light rounded-lg text-text-primary focus:outline-none focus:border-primary/50"
          >
            <option value="all">全部部门</option>
            <option value="san">三省</option>
            <option value="liu">六部</option>
          </select>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-bg-tertiary scrollbar-track-transparent">
        <AnimatePresence mode="popLayout">
          {groupedAgents.san.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                三省
              </h3>
              <div className="space-y-2">
                {groupedAgents.san.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    isSelected={selectedAgentId === agent.id}
                    onClick={() => onSelectAgent(agent.id)}
                  />
                ))}
              </div>
            </motion.div>
          )}

          {groupedAgents.liu.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h3 className="text-xs font-medium text-text-secondary uppercase tracking-wider mb-2">
                六部
              </h3>
              <div className="space-y-2">
                {groupedAgents.liu.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    isSelected={selectedAgentId === agent.id}
                    onClick={() => onSelectAgent(agent.id)}
                  />
                ))}
              </div>
            </motion.div>
          )}

          {filteredAgents.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-8 text-text-secondary"
            >
              <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm">未找到匹配的智能体</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="p-3 border-t border-border-light text-xs text-text-secondary text-center">
        共 {filteredAgents.length} / {agents.length} 个智能体
      </div>
    </div>
  );
};

export default AgentList;
