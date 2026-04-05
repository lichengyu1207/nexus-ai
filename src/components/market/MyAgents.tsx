import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import marketApi, { UserAgent } from '../../api/market';

interface MyAgentsProps {
  onAgentSelect?: (agent: UserAgent) => void;
}

const DEPARTMENT_INFO: Record<string, { name: string; icon: string; color: string }> = {
  '吏部': { name: '吏部', icon: '📚', color: '#3B82F6' },
  '工部': { name: '工部', icon: '🏗️', color: '#F59E0B' },
  '户部': { name: '户部', icon: '💰', color: '#10B981' },
  '兵部': { name: '兵部', icon: '🛡️', color: '#EF4444' },
  '礼部': { name: '礼部', icon: '🎭', color: '#8B5CF6' },
  '刑部': { name: '刑部', icon: '⚖️', color: '#6366F1' },
};

const STATUS_INFO: Record<string, { label: string; color: string }> = {
  idle: { label: '闲置', color: '#9CA3AF' },
  working: { label: '工作中', color: '#10B981' },
  training: { label: '培训中', color: '#3B82F6' },
};

const MyAgents: React.FC<MyAgentsProps> = ({ onAgentSelect }) => {
  const queryClient = useQueryClient();
  const [selectedAgent, setSelectedAgent] = useState<UserAgent | null>(null);

  const { data: agentsData, isLoading, error, refetch } = useQuery({
    queryKey: ['my-agents'],
    queryFn: marketApi.getUserAgents,
    staleTime: 30 * 1000,
  });

  const agents = agentsData?.agents || [];

  const upgradeMutation = useMutation({
    mutationFn: (userAgentId: string) => marketApi.upgradeAgent(userAgentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-agents'] });
    },
  });

  const dismissMutation = useMutation({
    mutationFn: (userAgentId: string) => marketApi.dismissAgent(userAgentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-agents'] });
    },
  });

  const handleUpgrade = useCallback(async (agent: UserAgent) => {
    try {
      await upgradeMutation.mutateAsync(agent.id);
    } catch (err) {
      console.error('Upgrade failed:', err);
    }
  }, [upgradeMutation]);

  const handleDismiss = useCallback(async (agent: UserAgent) => {
    if (confirm(`确定要解雇 ${agent.name} 吗？将返还部分积分。`)) {
      try {
        await dismissMutation.mutateAsync(agent.id);
      } catch (err) {
        console.error('Dismiss failed:', err);
      }
    }
  }, [dismissMutation]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full"
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <span className="text-4xl mb-4 block">⚠️</span>
        <p className="text-gray-500 dark:text-gray-400">加载失败</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">我的智能体</h2>
        <span className="text-sm text-gray-500 dark:text-gray-400">共 {agents.length} 个</span>
      </div>

      {agents.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-xl">
          <span className="text-4xl mb-4 block">🎭</span>
          <p className="text-gray-500 dark:text-gray-400 mb-4">您还没有招募任何智能体</p>
          <p className="text-sm text-gray-400 dark:text-gray-500">前往人才市场招募您的第一个智能体</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <AnimatePresence>
            {agents.map((agent, index) => {
              const deptInfo = DEPARTMENT_INFO[agent.department] || { name: agent.department, icon: '👤', color: '#6B7280' };
              const statusInfo = STATUS_INFO[agent.status] || { label: '未知', color: '#6B7280' };
              const expProgress = agent.next_level_exp > 0 ? (agent.experience / agent.next_level_exp) * 100 : 0;

              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => setSelectedAgent(selectedAgent?.id === agent.id ? null : agent)}
                >
                  <div className="h-2" style={{ background: deptInfo.color }} />
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
                          style={{ background: `${deptInfo.color}20` }}
                        >
                          {deptInfo.icon}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900 dark:text-white">{agent.name}</h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400">{deptInfo.name}</p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full">
                          <span className="text-xs text-gray-600 dark:text-gray-300">Lv.{agent.level}</span>
                        </div>
                        <div
                          className="px-2 py-0.5 rounded-full text-xs"
                          style={{
                            background: `${statusInfo.color}20`,
                            color: statusInfo.color,
                          }}
                        >
                          {statusInfo.label}
                        </div>
                      </div>
                    </div>

                    <div className="mb-3">
                      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                        <span>经验值</span>
                        <span>{agent.experience}/{agent.next_level_exp}</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full rounded-full"
                          style={{ background: deptInfo.color }}
                          initial={{ width: 0 }}
                          animate={{ width: `${expProgress}%` }}
                        />
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1 mb-3">
                      {agent.skills?.slice(0, 2).map((skill, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 text-xs rounded-full"
                          style={{
                            background: `${deptInfo.color}15`,
                            color: deptInfo.color,
                          }}
                        >
                          {skill.name} Lv.{skill.level}
                        </span>
                      ))}
                      {agent.skills?.length > 2 && (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                          +{agent.skills.length - 2}
                        </span>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <motion.button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUpgrade(agent);
                        }}
                        disabled={upgradeMutation.isPending}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="flex-1 px-3 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {upgradeMutation.isPending ? '升级中...' : '升级'}
                      </motion.button>
                      <motion.button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDismiss(agent);
                        }}
                        disabled={dismissMutation.isPending}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="px-3 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium"
                      >
                        解雇
                      </motion.button>
                    </div>
                  </div>

                  <AnimatePresence>
                    {selectedAgent?.id === agent.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4"
                      >
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">技能详情</h4>
                        <div className="space-y-2">
                          {agent.skills?.map((skill, idx) => (
                            <div key={idx} className="flex items-center justify-between">
                              <span className="text-sm text-gray-700 dark:text-gray-300">{skill.name}</span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">Lv.{skill.level}</span>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default MyAgents;
