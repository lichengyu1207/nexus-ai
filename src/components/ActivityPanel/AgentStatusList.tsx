import { motion } from 'framer-motion';
import type { AgentStatus, AgentHealthStatus } from '../types';

interface AgentStatusListProps {
  agents: AgentStatus[];
}

const statusConfig: Record<AgentHealthStatus, { color: string; bgColor: string; label: string }> = {
  healthy: { color: 'bg-green-500', bgColor: 'bg-green-500/20', label: '健康' },
  busy: { color: 'bg-yellow-500', bgColor: 'bg-yellow-500/20', label: '繁忙' },
  error: { color: 'bg-red-500', bgColor: 'bg-red-500/20', label: '异常' },
};

export function AgentStatusList({ agents }: AgentStatusListProps) {
  if (agents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        暂无智能体状态
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {agents.map((agent, index) => {
        const config = statusConfig[agent.status];
        return (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center justify-between p-3 rounded-lg
              bg-slate-800/50 hover:bg-slate-700/50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="relative">
                <motion.div
                  animate={{
                    scale: [1, 1.2, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }}
                  className={`w-3 h-3 rounded-full ${config.color}`}
                />
                <div
                  className={`absolute inset-0 w-3 h-3 rounded-full ${config.color}
                    opacity-50 blur-sm`}
                />
              </div>
              <div>
                <p className="text-white text-sm font-medium">{agent.name}</p>
                <p className={`text-xs ${config.color.replace('bg-', 'text-')}`}>
                  {config.label}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-xs">任务数</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                agent.currentTasks > 0 ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-gray-400'
              }`}>
                {agent.currentTasks}
              </span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
