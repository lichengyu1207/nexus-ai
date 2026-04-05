import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ecosystemApi from '@/api/ecosystem';

const EcosystemPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const { data: status } = useQuery({
    queryKey: ['ecosystemStatus'],
    queryFn: ecosystemApi.getStatus,
  });

  const { data: agentsData, isLoading } = useQuery({
    queryKey: ['ecosystemAgents'],
    queryFn: ecosystemApi.getAgents,
  });

  const { data: statistics } = useQuery({
    queryKey: ['ecosystemStatistics'],
    queryFn: ecosystemApi.getStatistics,
  });

  const spawnMutation = useMutation({
    mutationFn: (agentType: 'attack' | 'defense' | 'memory') => 
      ecosystemApi.spawnAgent({ agent_type: agentType }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ecosystemAgents', 'ecosystemStatus'] }),
  });

  const evolveMutation = useMutation({
    mutationFn: ecosystemApi.triggerSelection,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ecosystemAgents', 'ecosystemStatus'] }),
  });

  const agents = agentsData?.agents || [];

  const getAgentTypeColor = (type: string) => {
    switch (type) {
      case 'attack': return 'bg-red-500';
      case 'defense': return 'bg-blue-500';
      case 'memory': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'alive': return 'text-green-500';
      case 'dead': return 'text-red-500';
      case 'dormant': return 'text-yellow-500';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">活体生态系统</h2>
        <div className="flex gap-2">
          <button
            onClick={() => evolveMutation.mutate()}
            disabled={evolveMutation.isPending}
            className="px-4 py-2 bg-green-500 text-white rounded-lg text-sm disabled:opacity-50"
          >
            {evolveMutation.isPending ? '进化中...' : '触发进化'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-gray-700 to-gray-800 rounded-xl p-5 text-white"
        >
          <p className="text-gray-300 text-sm">总智能体</p>
          <p className="text-3xl font-bold mt-1">{status?.total_agents || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-5 text-white"
        >
          <p className="text-red-100 text-sm">攻击者</p>
          <p className="text-3xl font-bold mt-1">{status?.attack_agents || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white"
        >
          <p className="text-blue-100 text-sm">防御者</p>
          <p className="text-3xl font-bold mt-1">{status?.defense_agents || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white"
        >
          <p className="text-purple-100 text-sm">记忆者</p>
          <p className="text-3xl font-bold mt-1">{status?.memory_agents || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white"
        >
          <p className="text-green-100 text-sm">世代</p>
          <p className="text-3xl font-bold mt-1">{status?.generation || 0}</p>
        </motion.div>
      </div>

      {/* Spawn Controls */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">生成智能体</h3>
        <div className="grid grid-cols-3 gap-4">
          <button
            onClick={() => spawnMutation.mutate('attack')}
            disabled={spawnMutation.isPending}
            className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 hover:bg-red-100 dark:hover:bg-red-900/30 disabled:opacity-50"
          >
            <span className="text-2xl">⚔️</span>
            <p className="font-medium mt-2">攻击者</p>
            <p className="text-xs text-gray-500">主动进攻型</p>
          </button>
          <button
            onClick={() => spawnMutation.mutate('defense')}
            disabled={spawnMutation.isPending}
            className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 hover:bg-blue-100 dark:hover:bg-blue-900/30 disabled:opacity-50"
          >
            <span className="text-2xl">🛡️</span>
            <p className="font-medium mt-2">防御者</p>
            <p className="text-xs text-gray-500">保护型智能体</p>
          </button>
          <button
            onClick={() => spawnMutation.mutate('memory')}
            disabled={spawnMutation.isPending}
            className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800 hover:bg-purple-100 dark:hover:bg-purple-900/30 disabled:opacity-50"
          >
            <span className="text-2xl">🧠</span>
            <p className="font-medium mt-2">记忆者</p>
            <p className="text-xs text-gray-500">知识存储型</p>
          </button>
        </div>
      </div>

      {/* Agents List */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">智能体列表</h3>
        {isLoading ? (
          <p className="text-gray-500 text-center py-8">加载中...</p>
        ) : agents.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无智能体</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
            {agents.map((agent) => (
              <div
                key={agent.id}
                onClick={() => setSelectedAgent(agent.id)}
                className={`p-4 rounded-lg cursor-pointer transition-colors ${
                  selectedAgent === agent.id
                    ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-500'
                    : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full ${getAgentTypeColor(agent.agent_type)} flex items-center justify-center text-white`}>
                    {agent.agent_type === 'attack' ? '⚔️' : agent.agent_type === 'defense' ? '🛡️' : '🧠'}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-sm truncate">{agent.id.slice(0, 12)}...</p>
                    <div className="flex items-center gap-2 text-xs">
                      <span className={getStatusColor(agent.status)}>{agent.status}</span>
                      <span className="text-gray-400">Gen.{agent.generation}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                  <span>适应度: {agent.fitness.toFixed(2)}</span>
                  <span>能量: {agent.energy.toFixed(1)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Statistics */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">生态统计</h3>
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
            <p className="text-2xl font-bold">{statistics?.total_spawned || 0}</p>
            <p className="text-xs text-gray-500">总生成</p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
            <p className="text-2xl font-bold">{statistics?.total_deaths || 0}</p>
            <p className="text-xs text-gray-500">总死亡</p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
            <p className="text-2xl font-bold">{statistics?.total_reproductions || 0}</p>
            <p className="text-xs text-gray-500">总繁殖</p>
          </div>
          <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
            <p className="text-2xl font-bold">{statistics?.avg_lifespan?.toFixed(0) || 0}</p>
            <p className="text-xs text-gray-500">平均寿命</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EcosystemPage;
