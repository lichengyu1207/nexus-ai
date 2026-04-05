import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import skillApi, { Skill, SkillListParams } from '@/api/skill';

const CATEGORY_INFO: Record<string, { name: string; icon: string; color: string }> = {
  'general': { name: '通用', icon: '🔧', color: '#6B7280' },
  'analysis': { name: '分析', icon: '📊', color: '#3B82F6' },
  'visualization': { name: '可视化', icon: '📈', color: '#10B981' },
  'gis': { name: 'GIS', icon: '🗺️', color: '#F59E0B' },
  'nlp': { name: 'NLP', icon: '💬', color: '#8B5CF6' },
  'data': { name: '数据处理', icon: '🗄️', color: '#EF4444' },
};

const TYPE_INFO: Record<string, { name: string; color: string }> = {
  'builtin': { name: '内置', color: '#10B981' },
  'external': { name: '外部', color: '#3B82F6' },
  'custom': { name: '自定义', color: '#8B5CF6' },
};

const SkillPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<SkillListParams>({ page: 1, size: 20 });
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [showInvokeModal, setShowInvokeModal] = useState(false);
  const [invokeInput, setInvokeInput] = useState('{}');

  const { data: skillsData, isLoading, error, refetch } = useQuery({
    queryKey: ['skills', filters],
    queryFn: () => skillApi.listSkills(filters),
  });

  const { data: walletBalance } = useQuery({
    queryKey: ['walletBalance'],
    queryFn: () => skillApi.getWalletBalance(),
  });

  const invokeMutation = useMutation({
    mutationFn: ({ skillId, input }: { skillId: string; input: Record<string, unknown> }) =>
      skillApi.invokeSkill(skillId, { input_data: input }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['walletBalance'] });
    },
  });

  const purchaseMutation = useMutation({
    mutationFn: (skillId: string) => skillApi.purchaseSkill(skillId, 'test-user'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills', filters] });
      queryClient.invalidateQueries({ queryKey: ['walletBalance'] });
    },
  });

  const handleInvoke = async () => {
    if (!selectedSkill) return;
    try {
      const input = JSON.parse(invokeInput);
      await invokeMutation.mutateAsync({ skillId: selectedSkill.id, input });
      setShowInvokeModal(false);
    } catch (err) {
      console.error('Invalid JSON or invoke failed:', err);
    }
  };

  const handlePurchase = async (skill: Skill) => {
    if (confirm(`确定要购买 ${skill.name} 吗？将花费 ${skill.cost_points} 积分。`)) {
      await purchaseMutation.mutateAsync(skill.id);
    }
  };

  const skills = skillsData?.skills || [];
  const total = skillsData?.total || 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">技能市场</h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                发现、购买和使用各种AI技能
              </p>
            </div>
            {walletBalance && (
              <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow">
                <span className="text-amber-500">💰</span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {walletBalance.available_points.toLocaleString()} 积分
                </span>
              </div>
            )}
          </div>
        </motion.div>

        <div className="mb-6 flex flex-wrap gap-4">
          <select
            value={filters.category || ''}
            onChange={(e) => setFilters({ ...filters, category: e.target.value || undefined, page: 1 })}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">全部分类</option>
            {Object.entries(CATEGORY_INFO).map(([key, info]) => (
              <option key={key} value={key}>{info.name}</option>
            ))}
          </select>

          <select
            value={filters.type || ''}
            onChange={(e) => setFilters({ ...filters, type: e.target.value || undefined, page: 1 })}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="">全部类型</option>
            {Object.entries(TYPE_INFO).map(([key, info]) => (
              <option key={key} value={key}>{info.name}</option>
            ))}
          </select>

          <input
            type="text"
            placeholder="搜索技能..."
            value={filters.keyword || ''}
            onChange={(e) => setFilters({ ...filters, keyword: e.target.value || undefined, page: 1 })}
            className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400">
            加载失败，请重试
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full"
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {skills.map((skill, index) => {
                const categoryInfo = CATEGORY_INFO[skill.category] || { name: skill.category, icon: '📦', color: '#6B7280' };
                const typeInfo = TYPE_INFO[skill.type] || { name: skill.type, color: '#6B7280' };

                return (
                  <motion.div
                    key={skill.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.05 }}
                    className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow"
                  >
                    <div className="h-2" style={{ background: categoryInfo.color }} />
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
                            style={{ background: `${categoryInfo.color}20` }}
                          >
                            {categoryInfo.icon}
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900 dark:text-white">{skill.name}</h3>
                            <div className="flex items-center gap-2">
                              <span
                                className="px-2 py-0.5 text-xs rounded-full"
                                style={{ background: `${typeInfo.color}20`, color: typeInfo.color }}
                              >
                                {typeInfo.name}
                              </span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                v{skill.version}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-amber-500">⭐</span>
                          <span className="text-sm text-gray-600 dark:text-gray-300">
                            {skill.avg_rating?.toFixed(1) || 'N/A'}
                          </span>
                        </div>
                      </div>

                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
                        {skill.description}
                      </p>

                      <div className="flex flex-wrap gap-1 mb-4">
                        {skill.tags?.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>

                      <div className="flex items-center justify-between mb-3">
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          下载 {skill.download_count || 0} 次
                        </div>
                        <div className="font-semibold text-primary-600 dark:text-primary-400">
                          {skill.cost_points > 0 ? `${skill.cost_points} 积分` : '免费'}
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <motion.button
                          onClick={() => {
                            setSelectedSkill(skill);
                            setShowInvokeModal(true);
                            setInvokeInput('{}');
                          }}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          className="flex-1 px-3 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium"
                        >
                          使用
                        </motion.button>
                        {skill.cost_points > 0 && (
                          <motion.button
                            onClick={() => handlePurchase(skill)}
                            disabled={purchaseMutation.isPending}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className="px-3 py-2 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-lg text-sm font-medium"
                          >
                            购买
                          </motion.button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}

        {skills.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <span className="text-4xl mb-4 block">🔍</span>
            <p className="text-gray-500 dark:text-gray-400">暂无技能</p>
          </div>
        )}

        {total > (filters.size || 20) && (
          <div className="mt-6 flex justify-center gap-2">
            <button
              onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
              disabled={(filters.page || 1) <= 1}
              className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm disabled:opacity-50"
            >
              上一页
            </button>
            <span className="px-4 py-2 text-gray-600 dark:text-gray-300">
              第 {filters.page} 页
            </span>
            <button
              onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
              disabled={(filters.page || 1) * (filters.size || 20) >= total}
              className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm disabled:opacity-50"
            >
              下一页
            </button>
          </div>
        )}

        <AnimatePresence>
          {showInvokeModal && selectedSkill && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
              onClick={() => setShowInvokeModal(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                  使用技能: {selectedSkill.name}
                </h3>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    输入参数 (JSON格式)
                  </label>
                  <textarea
                    value={invokeInput}
                    onChange={(e) => setInvokeInput(e.target.value)}
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                    placeholder='{"key": "value"}'
                  />
                </div>

                {invokeMutation.data && (
                  <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">执行结果:</div>
                    <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto">
                      {JSON.stringify(invokeMutation.data, null, 2)}
                    </pre>
                  </div>
                )}

                <div className="flex gap-2">
                  <motion.button
                    onClick={handleInvoke}
                    disabled={invokeMutation.isPending}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex-1 px-4 py-2 bg-primary-500 text-white rounded-lg font-medium disabled:opacity-50"
                  >
                    {invokeMutation.isPending ? '执行中...' : '执行'}
                  </motion.button>
                  <button
                    onClick={() => setShowInvokeModal(false)}
                    className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg font-medium"
                  >
                    关闭
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default SkillPage;
