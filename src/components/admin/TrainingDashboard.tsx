import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import trainingApi, { TrainingSession, TrainingEpisode, TrainingConfig } from '../../api/training';

const TrainingDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  const [showStartModal, setShowStartModal] = useState(false);
  const [selectedSession, setSelectedSession] = useState<TrainingSession | null>(null);
  const [config, setConfig] = useState<TrainingConfig>({
    episodes: 100,
    redCount: 3,
    blueCount: 3,
  });

  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ['training-sessions'],
    queryFn: trainingApi.getTrainingSessions,
    staleTime: 10 * 1000,
  });

  const { data: currentTraining, isLoading: currentLoading } = useQuery({
    queryKey: ['current-training'],
    queryFn: trainingApi.getCurrentTraining,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && data.status === 'running') {
        return 2000;
      }
      return 10000;
    },
  });

  const { data: metricsHistory } = useQuery({
    queryKey: ['training-metrics', selectedSession?.id],
    queryFn: () => selectedSession ? trainingApi.getMetricsHistory(selectedSession.id) : null,
    enabled: !!selectedSession,
  });

  const { data: recentEpisodes = [] } = useQuery({
    queryKey: ['training-episodes', currentTraining?.id],
    queryFn: () => currentTraining ? trainingApi.getRecentEpisodes(currentTraining.id, 10) : [],
    enabled: !!currentTraining,
    refetchInterval: 5000,
  });

  const startMutation = useMutation({
    mutationFn: trainingApi.startTraining,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-sessions'] });
      queryClient.invalidateQueries({ queryKey: ['current-training'] });
      setShowStartModal(false);
    },
  });

  const stopMutation = useMutation({
    mutationFn: trainingApi.stopTraining,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-training'] });
    },
  });

  const handleStartTraining = useCallback(() => {
    startMutation.mutate(config);
  }, [config, startMutation]);

  const handleStopTraining = useCallback(() => {
    if (currentTraining) {
      stopMutation.mutate(currentTraining.id);
    }
  }, [currentTraining, stopMutation]);

  const progress = currentTraining
    ? (currentTraining.episodes / currentTraining.targetEpisodes) * 100
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">自博弈训练监控</h1>
          <p className="text-gray-500 mt-1">红蓝对抗训练引擎</p>
        </div>
        {!currentTraining && (
          <motion.button
            onClick={() => setShowStartModal(true)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg font-medium"
          >
            启动新训练
          </motion.button>
        )}
      </div>

      {currentTraining && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl border border-gray-200 overflow-hidden"
        >
          <div className="p-4 bg-gradient-to-r from-red-500 to-blue-500 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">{currentTraining.name}</h2>
                <p className="text-white/80 text-sm">
                  红队 {currentTraining.redAgents} vs 蓝队 {currentTraining.blueAgents}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                  {currentTraining.status === 'running' ? '运行中' : currentTraining.status}
                </span>
                {currentTraining.status === 'running' && (
                  <motion.button
                    onClick={handleStopTraining}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-3 py-1 bg-red-500 text-white rounded-full text-sm font-medium"
                  >
                    停止
                  </motion.button>
                )}
              </div>
            </div>
          </div>

          <div className="p-4">
            <div className="mb-4">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-gray-500">训练进度</span>
                <span className="font-medium">
                  {currentTraining.episodes} / {currentTraining.targetEpisodes} 对局
                </span>
              </div>
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-red-500 to-blue-500 rounded-full"
                  animate={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-red-50 rounded-lg">
                <p className="text-xs text-red-600 mb-1">红队胜率</p>
                <p className="text-xl font-bold text-red-700">
                  {(currentTraining.metrics.redWinRate * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-600 mb-1">蓝队胜率</p>
                <p className="text-xl font-bold text-blue-700">
                  {(currentTraining.metrics.blueWinRate * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-xs text-green-600 mb-1">攻击成功率</p>
                <p className="text-xl font-bold text-green-700">
                  {(currentTraining.metrics.attackSuccessRate * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <p className="text-xs text-purple-600 mb-1">防御成功率</p>
                <p className="text-xl font-bold text-purple-700">
                  {(currentTraining.metrics.defenseSuccessRate * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h3 className="font-semibold text-gray-900 mb-4">最近对局</h3>
          {recentEpisodes.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无对局记录</p>
          ) : (
            <div className="space-y-2">
              {recentEpisodes.map((episode, index) => (
                <motion.div
                  key={episode.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500">#{episode.episodeNumber}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-red-600 font-medium">
                        R: {episode.redReward.toFixed(2)}
                      </span>
                      <span className="text-gray-300">|</span>
                      <span className="text-blue-600 font-medium">
                        B: {episode.blueReward.toFixed(2)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span>{episode.duration}ms</span>
                    <span className={episode.redReward > episode.blueReward ? 'text-red-500' : 'text-blue-500'}>
                      {episode.redReward > episode.blueReward ? '红胜' : '蓝胜'}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h3 className="font-semibold text-gray-900 mb-4">训练历史</h3>
          {sessionsLoading ? (
            <div className="flex items-center justify-center py-8">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full"
              />
            </div>
          ) : sessions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无训练历史</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-auto">
              {sessions.slice(0, 5).map((session) => (
                <div
                  key={session.id}
                  onClick={() => setSelectedSession(session)}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                >
                  <div>
                    <p className="font-medium text-gray-900">{session.name}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(session.startTime).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs ${
                        session.status === 'completed'
                          ? 'bg-green-100 text-green-700'
                          : session.status === 'running'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {session.status}
                    </span>
                    <span className="text-sm text-gray-500">
                      {session.episodes} 对局
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <AnimatePresence>
        {showStartModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowStartModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl p-6 max-w-md w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold text-gray-900 mb-4">启动新训练</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    对局数量
                  </label>
                  <input
                    type="number"
                    value={config.episodes}
                    onChange={(e) => setConfig({ ...config, episodes: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    min={10}
                    max={10000}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      红队数量
                    </label>
                    <input
                      type="number"
                      value={config.redCount}
                      onChange={(e) => setConfig({ ...config, redCount: Number(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      min={1}
                      max={10}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      蓝队数量
                    </label>
                    <input
                      type="number"
                      value={config.blueCount}
                      onChange={(e) => setConfig({ ...config, blueCount: Number(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      min={1}
                      max={10}
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowStartModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium"
                >
                  取消
                </button>
                <motion.button
                  onClick={handleStartTraining}
                  disabled={startMutation.isPending}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-lg font-medium disabled:opacity-50"
                >
                  {startMutation.isPending ? '启动中...' : '启动训练'}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TrainingDashboard;
