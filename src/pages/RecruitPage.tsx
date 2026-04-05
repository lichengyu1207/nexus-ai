import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import recruitApi, { RecruitResult, RecruitStats, UserAgent } from '@/api/recruit';

const rarityColors: Record<string, string> = {
  N: 'bg-gray-500',
  R: 'bg-blue-500',
  SR: 'bg-purple-500',
  SSR: 'bg-yellow-500',
  UR: 'bg-red-500',
};

const rarityGlow: Record<string, string> = {
  N: '',
  R: 'shadow-blue-500/50',
  SR: 'shadow-purple-500/50',
  SSR: 'shadow-yellow-500/50 animate-pulse',
  UR: 'shadow-red-500/50 animate-pulse',
};

const RecruitPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [recruitResult, setRecruitResult] = useState<RecruitResult | null>(null);
  const [showResult, setShowResult] = useState(false);

  const { data: statsData } = useQuery({
    queryKey: ['recruitStats'],
    queryFn: recruitApi.getStats,
  });
  const stats = statsData?.stats;

  const { data: agentsData, isLoading: agentsLoading } = useQuery({
    queryKey: ['myAgents'],
    queryFn: recruitApi.getMyAgents,
  });
  const agents = agentsData?.agents || [];

  const basicRecruitMutation = useMutation({
    mutationFn: recruitApi.basicRecruit,
    onSuccess: (data) => {
      setRecruitResult(data);
      setShowResult(true);
      queryClient.invalidateQueries({ queryKey: ['recruitStats', 'myAgents'] });
    },
  });

  const premiumRecruitMutation = useMutation({
    mutationFn: recruitApi.premiumRecruit,
    onSuccess: (data) => {
      setRecruitResult(data);
      setShowResult(true);
      queryClient.invalidateQueries({ queryKey: ['recruitStats', 'myAgents'] });
    },
  });

  const handleBasicRecruit = () => {
    basicRecruitMutation.mutate();
  };

  const handlePremiumRecruit = () => {
    premiumRecruitMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">智能体招募</h2>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white"
        >
          <p className="text-blue-100 text-sm">总招募次数</p>
          <p className="text-3xl font-bold mt-1">{stats?.total_recruits || 0}</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white"
        >
          <p className="text-purple-100 text-sm">SR保底进度</p>
          <p className="text-3xl font-bold mt-1">{stats?.pity_counter_sr || 0}/10</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-yellow-500 to-yellow-600 rounded-xl p-5 text-white"
        >
          <p className="text-yellow-100 text-sm">SSR保底进度</p>
          <p className="text-3xl font-bold mt-1">{stats?.pity_counter_ssr || 0}/50</p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white"
        >
          <p className="text-green-100 text-sm">拥有智能体</p>
          <p className="text-3xl font-bold mt-1">{agents?.length || 0}</p>
        </motion.div>
      </div>

      {/* Recruit Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">普通招募</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">消耗 100 积分进行普通招募</p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleBasicRecruit}
            disabled={basicRecruitMutation.isPending}
            className="w-full py-3 bg-blue-500 text-white rounded-lg font-medium disabled:opacity-50"
          >
            {basicRecruitMutation.isPending ? '招募中...' : '普通招募 (100积分)'}
          </motion.button>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">高级招募</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">消耗 500 积分，更高概率获得稀有智能体</p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handlePremiumRecruit}
            disabled={premiumRecruitMutation.isPending}
            className="w-full py-3 bg-purple-500 text-white rounded-lg font-medium disabled:opacity-50"
          >
            {premiumRecruitMutation.isPending ? '招募中...' : '高级招募 (500积分)'}
          </motion.button>
        </div>
      </div>

      {/* Recruit Result Modal */}
      <AnimatePresence>
        {showResult && recruitResult && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowResult(false)}
          >
            <motion.div
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.5, opacity: 0 }}
              className={`bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md mx-4 shadow-2xl ${rarityGlow[recruitResult.rarity]}`}
              onClick={e => e.stopPropagation()}
            >
              <div className="text-center">
                <div className={`w-24 h-24 mx-auto rounded-full ${rarityColors[recruitResult.rarity]} flex items-center justify-center text-white text-3xl font-bold mb-4`}>
                  {recruitResult.rarity}
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {recruitResult.agent_name}
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  {recruitResult.department} · Lv.{recruitResult.level}
                </p>
                <div className="flex flex-wrap justify-center gap-2 mb-4">
                  {recruitResult.skills?.map((skill, idx) => (
                    <span key={idx} className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm">
                      {skill.name} Lv.{skill.level}
                    </span>
                  ))}
                </div>
                <button
                  onClick={() => setShowResult(false)}
                  className="px-6 py-2 bg-primary-500 text-white rounded-lg"
                >
                  确定
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* My Agents */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">我的智能体</h3>
        {agentsLoading ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">加载中...</p>
        ) : agents?.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">暂无智能体，快去招募吧！</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents?.map((agent) => (
              <div
                key={agent.id}
                className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-10 h-10 rounded-full ${rarityColors[agent.rarity]} flex items-center justify-center text-white font-bold`}>
                    {agent.rarity}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{agent.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{agent.department} · Lv.{agent.level}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {agent.skills?.slice(0, 3).map((skill, idx) => (
                    <span key={idx} className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 rounded text-xs">
                      {skill.name}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecruitPage;
