import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import trainingApi, { 
  TrainingStatus, 
  PopulationStatus, 
  TrainRequest, 
  EvaluateRequest,
  TrainingHistory 
} from '@/api/training';

const TrainingDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [isTraining, setIsTraining] = useState(false);
  const [activeTab, setActiveTab] = useState<'status' | 'population' | 'history'>('status');

  const { data: status, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['selfplay', 'status'],
    queryFn: () => trainingApi.getStatus(),
    refetchInterval: 5000,
  });

  const { data: population, isLoading: populationLoading, refetch: refetchPopulation } = useQuery({
    queryKey: ['selfplay', 'population'],
    queryFn: () => trainingApi.getPopulation(),
    refetchInterval: 10000,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['selfplay', 'history'],
    queryFn: () => trainingApi.getHistory(50),
  });

  const trainMutation = useMutation({
    mutationFn: (request: TrainRequest) => trainingApi.train(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['selfplay'] });
    },
  });

  const evaluateMutation = useMutation({
    mutationFn: (request: EvaluateRequest) => trainingApi.evaluate(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['selfplay'] });
    },
  });

  const handleStartTraining = useCallback(async () => {
    setIsTraining(true);
    try {
      await trainMutation.mutateAsync({ num_episodes: 10, update_interval: 5 });
    } finally {
      setIsTraining(false);
    }
  }, [trainMutation]);

  const handleEvaluate = useCallback(async () => {
    await evaluateMutation.mutateAsync({ num_games: 10 });
  }, [evaluateMutation]);

  const getStatusColor = (winRate: number): string => {
    if (winRate >= 0.6) return 'text-green-500';
    if (winRate >= 0.4) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">自博弈训练引擎</h2>
        <div className="flex items-center gap-2">
          {status?.is_training && (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              训练中
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-5 text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-100 text-sm">总训练回合</p>
              <p className="text-3xl font-bold mt-1">{status?.total_episodes || 0}</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <span className="text-2xl">🎮</span>
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-red-400 to-orange-500 rounded-xl p-5 text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-100 text-sm">攻击者胜率</p>
              <p className="text-3xl font-bold mt-1">
                {((status?.best_attacker_win_rate || 0) * 100).toFixed(1)}%
              </p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <span className="text-2xl">⚔️</span>
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl p-5 text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">防御者胜率</p>
              <p className="text-3xl font-bold mt-1">
                {((status?.best_defender_win_rate || 0) * 100).toFixed(1)}%
              </p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <span className="text-2xl">🛡️</span>
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">种群大小</p>
              <p className="text-3xl font-bold mt-1">{status?.population_size || 0}</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <span className="text-2xl">👥</span>
            </div>
          </div>
        </motion.div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <div className="flex">
            {[
              { id: 'status', label: '训练控制', icon: '🎮' },
              { id: 'population', label: '种群状态', icon: '👥' },
              { id: 'history', label: '训练历史', icon: '📊' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'status' | 'population' | 'history')}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'text-primary-600 border-b-2 border-primary-600 bg-primary-50 dark:bg-primary-900/20'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          <AnimatePresence mode="wait">
            {activeTab === 'status' && (
              <motion.div
                key="status"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-6"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">训练配置</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">训练回合数</label>
                        <input
                          type="number"
                          defaultValue={10}
                          min={1}
                          max={100}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          id="train-episodes"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleStartTraining}
                        disabled={isTraining || trainMutation.isPending}
                        className="flex-1 py-2 bg-red-500 text-white rounded-lg font-medium disabled:opacity-50"
                      >
                        {isTraining || trainMutation.isPending ? '训练中...' : '开始训练'}
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleEvaluate}
                        disabled={evaluateMutation.isPending}
                        className="flex-1 py-2 bg-blue-500 text-white rounded-lg font-medium disabled:opacity-50"
                      >
                        {evaluateMutation.isPending ? '评估中...' : '开始评估'}
                      </motion.button>
                    </div>
                  </div>

                  {evaluateMutation.data && (
                    <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">评估结果</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">攻击者胜率</span>
                          <p className={`text-lg font-bold ${getStatusColor(evaluateMutation.data.attacker_win_rate)}`}>
                            {(evaluateMutation.data.attacker_win_rate * 100).toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">防御者胜率</span>
                          <p className={`text-lg font-bold ${getStatusColor(evaluateMutation.data.defender_win_rate)}`}>
                            {(evaluateMutation.data.defender_win_rate * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === 'population' && (
              <motion.div
                key="population"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-4"
              >
                <div className="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                    <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                    攻击者种群 ({population?.attacker_population?.length || 0})
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {populationLoading ? (
                      <p className="text-gray-500 dark:text-gray-400 text-center py-4">加载中...</p>
                    ) : population?.attacker_population?.length === 0 ? (
                      <p className="text-gray-500 dark:text-gray-400 text-center py-4">暂无攻击者</p>
                    ) : (
                      population?.attacker_population?.map((agent) => (
                        <div key={agent.agent_id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-600 rounded">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                              {agent.agent_id.slice(0, 8)}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs">
                            <span className={getStatusColor(agent.win_rate)}>
                              {(agent.win_rate * 100).toFixed(1)}%
                            </span>
                            <span className="text-gray-400">{agent.total_games}局</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                    <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                    防御者种群 ({population?.defender_population?.length || 0})
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {populationLoading ? (
                      <p className="text-gray-500 dark:text-gray-400 text-center py-4">加载中...</p>
                    ) : population?.defender_population?.length === 0 ? (
                      <p className="text-gray-500 dark:text-gray-400 text-center py-4">暂无防御者</p>
                    ) : (
                      population?.defender_population?.map((agent) => (
                        <div key={agent.agent_id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-600 rounded">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                              {agent.agent_id.slice(0, 8)}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-xs">
                            <span className={getStatusColor(agent.win_rate)}>
                              {(agent.win_rate * 100).toFixed(1)}%
                            </span>
                            <span className="text-gray-400">{agent.total_games}局</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'history' && (
              <motion.div
                key="history"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="overflow-x-auto"
              >
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-2 text-gray-500 dark:text-gray-400">回合</th>
                      <th className="text-left py-2 text-gray-500 dark:text-gray-400">胜者</th>
                      <th className="text-left py-2 text-gray-500 dark:text-gray-400">攻击者奖励</th>
                      <th className="text-left py-2 text-gray-500 dark:text-gray-400">防御者奖励</th>
                      <th className="text-left py-2 text-gray-500 dark:text-gray-400">时长</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyLoading ? (
                      <tr>
                        <td colSpan={5} className="text-center py-4 text-gray-500 dark:text-gray-400">
                          加载中...
                        </td>
                      </tr>
                    ) : history?.history?.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="text-center py-4 text-gray-500 dark:text-gray-400">
                          暂无训练记录
                        </td>
                      </tr>
                    ) : (
                      history?.history?.slice(-10).reverse().map((item, idx) => (
                        <tr key={idx} className="border-b border-gray-100 dark:border-gray-700">
                          <td className="py-2 text-gray-900 dark:text-white">{item.episode}</td>
                          <td className="py-2">
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              item.winner === 'attacker' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
                            }`}>
                              {item.winner === 'attacker' ? '攻击者' : '防御者'}
                            </span>
                          </td>
                          <td className="py-2 text-gray-600 dark:text-gray-300">
                            {item.attacker_reward.toFixed(2)}
                          </td>
                          <td className="py-2 text-gray-600 dark:text-gray-300">
                            {item.defender_reward.toFixed(2)}
                          </td>
                          <td className="py-2 text-gray-500 dark:text-gray-400">
                            {item.duration.toFixed(2)}s
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default TrainingDashboard;
