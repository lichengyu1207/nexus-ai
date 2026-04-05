import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import marketApi, { AgentTemplate } from '../../api/market';

interface AgentMarketProps {
  onAgentSelect?: (agent: AgentTemplate) => void;
  onRecruitSuccess?: () => void;
}

const DEPARTMENT_INFO: Record<string, { name: string; icon: string; color: string; description: string }> = {
  '吏部': { name: '吏部', icon: '📚', color: '#3B82F6', description: '教育资源分析专家' },
  '工部': { name: '工部', icon: '🏗️', color: '#F59E0B', description: '城市规划与建设专家' },
  '户部': { name: '户部', icon: '💰', color: '#10B981', description: '房价数据采集专家' },
  '兵部': { name: '兵部', icon: '🛡️', color: '#EF4444', description: '风险评估专家' },
  '礼部': { name: '礼部', icon: '🎭', color: '#8B5CF6', description: '社区文化分析专家' },
  '刑部': { name: '刑部', icon: '⚖️', color: '#6366F1', description: '法律合规专家' },
};

const RARITY_COLORS: Record<string, string> = {
  'N': '#9CA3AF',
  'R': '#3B82F6',
  'SR': '#8B5CF6',
  'SSR': '#F59E0B',
  'UR': '#EF4444',
};

const AgentMarket: React.FC<AgentMarketProps> = ({ onAgentSelect, onRecruitSuccess }) => {
  const [agents, setAgents] = useState<AgentTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');
  const [recruitingAgent, setRecruitingAgent] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await marketApi.getAvailableAgents(selectedDepartment || undefined);
      setAgents(response.agents || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载智能体市场失败');
    } finally {
      setIsLoading(false);
    }
  }, [selectedDepartment]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const handleRecruit = useCallback(async (agent: AgentTemplate) => {
    try {
      setRecruitingAgent(agent.id);
      const result = await marketApi.recruitAgent(agent.id);
      if (result.success) {
        onRecruitSuccess?.();
        fetchAgents();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '招募失败');
    } finally {
      setRecruitingAgent(null);
    }
  }, [fetchAgents, onRecruitSuccess]);

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">智能体人才市场</h2>
        <div className="flex items-center gap-4">
          <select
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">全部部门</option>
            {Object.entries(DEPARTMENT_INFO).map(([key, info]) => (
              <option key={key} value={key}>
                {info.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {agents.map((agent, index) => {
            const deptInfo = DEPARTMENT_INFO[agent.department] || { name: agent.department, icon: '👤', color: '#6B7280', description: '' };
            const rarityColor = RARITY_COLORS[agent.rarity] || '#6B7280';
            const isRecruiting = recruitingAgent === agent.id;

            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow"
              >
                <div className="h-2" style={{ background: rarityColor }} />
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
                    <div className="flex items-center gap-1 px-2 py-1 rounded-full" style={{ background: `${rarityColor}20` }}>
                      <span className="text-xs" style={{ color: rarityColor }}>{agent.rarity}</span>
                    </div>
                  </div>

                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{agent.description || deptInfo.description}</p>

                  <div className="flex flex-wrap gap-1 mb-4">
                    {agent.skills?.slice(0, 3).map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 text-xs rounded-full"
                        style={{
                          background: `${deptInfo.color}15`,
                          color: deptInfo.color,
                        }}
                      >
                        {skill.name}
                      </span>
                    ))}
                    {agent.skills?.length > 3 && (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                        +{agent.skills.length - 3}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-sm">
                      <span className="text-gray-500 dark:text-gray-400">招募价格</span>
                      <span className="ml-2 font-semibold text-primary-600 dark:text-primary-400">
                        {agent.base_cost?.toLocaleString() || '免费'}
                      </span>
                    </div>

                    <motion.button
                      onClick={() => handleRecruit(agent)}
                      disabled={isRecruiting || !!recruitingAgent}
                      whileHover={{ scale: isRecruiting ? 1 : 1.02 }}
                      whileTap={{ scale: isRecruiting ? 1 : 0.98 }}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isRecruiting
                          ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                          : 'bg-primary-500 text-white hover:bg-primary-600'
                      }`}
                    >
                      {isRecruiting ? '招募中...' : '招募'}
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {agents.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <span className="text-4xl mb-4 block">🔍</span>
          <p className="text-gray-500 dark:text-gray-400">暂无可招募的智能体</p>
        </div>
      )}
    </div>
  );
};

export default AgentMarket;
