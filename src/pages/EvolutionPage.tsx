import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import evolutionApi from '@/api/evolution';

const EvolutionPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const { data: report, isLoading } = useQuery({
    queryKey: ['evolutionReport'],
    queryFn: evolutionApi.getReport,
  });

  const { data: agents } = useQuery({
    queryKey: ['evolutionAgents'],
    queryFn: evolutionApi.getRegisteredAgents,
  });

  const { data: suggestions } = useQuery({
    queryKey: ['evolutionSuggestions'],
    queryFn: evolutionApi.getSuggestions,
  });

  const { data: agentPerformance } = useQuery({
    queryKey: ['agentPerformance', selectedAgent],
    queryFn: () => selectedAgent ? evolutionApi.getAgentPerformance(selectedAgent) : null,
    enabled: !!selectedAgent,
  });

  const diagnoseMutation = useMutation({
    mutationFn: (agentId: string) => evolutionApi.runDiagnosis(agentId, 'comprehensive'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['evolutionSuggestions'] }),
  });

  const approveMutation = useMutation({
    mutationFn: (suggestionId: string) => evolutionApi.approveSuggestion(suggestionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['evolutionSuggestions'] }),
  });

  const applyMutation = useMutation({
    mutationFn: (suggestionId: string) => evolutionApi.applySuggestion(suggestionId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['evolutionSuggestions', 'evolutionReport'] }),
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">自我进化系统</h2>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white"
        >
          <p className="text-green-100 text-sm">健康智能体</p>
          <p className="text-3xl font-bold mt-1">{report?.healthy_agents || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-xl p-5 text-white"
        >
          <p className="text-yellow-100 text-sm">警告状态</p>
          <p className="text-3xl font-bold mt-1">{report?.warning_agents || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-5 text-white"
        >
          <p className="text-red-100 text-sm">临界状态</p>
          <p className="text-3xl font-bold mt-1">{report?.critical_agents || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white"
        >
          <p className="text-blue-100 text-sm">近期改进</p>
          <p className="text-3xl font-bold mt-1">{report?.recent_improvements || 0}</p>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agents List */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">已注册智能体</h3>
          {isLoading ? (
            <p className="text-gray-500 text-center py-8">加载中...</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {agents?.agents?.map((agent) => (
                <div
                  key={agent.agent_id}
                  onClick={() => setSelectedAgent(agent.agent_id)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedAgent === agent.agent_id 
                      ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-500' 
                      : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{agent.agent_name}</p>
                      <p className="text-xs text-gray-500">{agent.department}</p>
                    </div>
                    <span className={`text-sm font-medium ${getStatusColor(agent.status)}`}>
                      {agent.success_rate.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Suggestions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">进化建议</h3>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {suggestions?.suggestions?.filter(s => s.status === 'pending').slice(0, 10).map((suggestion) => (
              <div key={suggestion.id} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{suggestion.agent_name}</span>
                  <span className="text-xs text-gray-500">{suggestion.type}</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{suggestion.description}</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => applyMutation.mutate(suggestion.id)}
                    disabled={applyMutation.isPending}
                    className="flex-1 py-1 text-xs bg-green-500 text-white rounded disabled:opacity-50"
                  >
                    应用
                  </button>
                  <button
                    onClick={() => approveMutation.mutate(suggestion.id)}
                    disabled={approveMutation.isPending}
                    className="flex-1 py-1 text-xs bg-blue-500 text-white rounded disabled:opacity-50"
                  >
                    批准
                  </button>
                </div>
              </div>
            ))}
            {(!suggestions?.suggestions || suggestions.suggestions.length === 0) && (
              <p className="text-gray-500 text-center py-8">暂无待处理建议</p>
            )}
          </div>
        </div>
      </div>

      {/* Agent Performance */}
      <AnimatePresence>
        {selectedAgent && agentPerformance && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {agentPerformance.agent_name} 性能报告
              </h3>
              <button
                onClick={() => diagnoseMutation.mutate(selectedAgent)}
                disabled={diagnoseMutation.isPending}
                className="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm disabled:opacity-50"
              >
                {diagnoseMutation.isPending ? '诊断中...' : '运行诊断'}
              </button>
            </div>
            <div className="grid grid-cols-4 gap-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(agentPerformance.performance_metrics?.success_rate * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">成功率</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {agentPerformance.performance_metrics?.avg_response_time?.toFixed(2)}s
                </p>
                <p className="text-xs text-gray-500">平均响应</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {agentPerformance.performance_metrics?.total_decisions}
                </p>
                <p className="text-xs text-gray-500">总决策数</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {agentPerformance.current_version}
                </p>
                <p className="text-xs text-gray-500">当前版本</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default EvolutionPage;
