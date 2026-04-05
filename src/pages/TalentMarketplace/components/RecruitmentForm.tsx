import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { Recruitment, BudgetType } from '../types';
import { BUDGET_TYPE_CONFIG } from '../types';

export interface RecruitmentFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<Recruitment>) => void;
  isLoading?: boolean;
  initialData?: Partial<Recruitment>;
}

const SKILL_OPTIONS = [
  '数据分析',
  '房产估值',
  '模型训练',
  '报告生成',
  'API集成',
  '自然语言处理',
  '图像识别',
  '风险评估',
];

export function RecruitmentForm({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  initialData,
}: RecruitmentFormProps) {
  const [formData, setFormData] = useState<Partial<Recruitment>>({
    title: initialData?.title ?? '',
    description: initialData?.description ?? '',
    requiredSkills: initialData?.requiredSkills ?? [],
    budgetType: initialData?.budgetType ?? 'fixed',
    budget: initialData?.budget ?? 0,
    deadline: initialData?.deadline ?? '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleSkillToggle = (skill: string) => {
    setFormData((prev) => ({
      ...prev,
      requiredSkills: prev.requiredSkills?.includes(skill)
        ? prev.requiredSkills.filter((s) => s !== skill)
        : [...(prev.requiredSkills ?? []), skill],
    }));
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-gray-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
          >
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <h2 className="text-lg font-semibold text-white">
                {initialData ? '编辑招募' : '发布招募'}
              </h2>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  招募标题 <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                  placeholder="输入招募标题"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  详细描述 <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  rows={4}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 resize-none"
                  placeholder="描述您的需求、期望交付物等"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  所需技能
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {SKILL_OPTIONS.map((skill) => (
                    <button
                      key={skill}
                      type="button"
                      onClick={() => handleSkillToggle(skill)}
                      className={`px-2 py-1 text-xs rounded-full transition-colors ${
                        formData.requiredSkills?.includes(skill)
                          ? 'bg-amber-500 text-gray-900'
                          : 'bg-white/5 text-gray-300 hover:bg-white/10'
                      }`}
                    >
                      {skill}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    预算类型
                  </label>
                  <select
                    value={formData.budgetType}
                    onChange={(e) =>
                      setFormData({ ...formData, budgetType: e.target.value as BudgetType })
                    }
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                  >
                    {Object.entries(BUDGET_TYPE_CONFIG).map(([key, config]) => (
                      <option key={key} value={key} className="bg-gray-800">
                        {config.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    预算金额 <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="number"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: Number(e.target.value) })}
                    required
                    min={0}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                    placeholder="¥0"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  截止日期
                </label>
                <input
                  type="date"
                  value={formData.deadline}
                  onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !formData.title || !formData.description}
                  className={`
                    flex-1 py-2 text-sm font-medium rounded-lg transition-colors
                    ${
                      isLoading || !formData.title || !formData.description
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : 'bg-amber-500 text-gray-900 hover:bg-amber-400'
                    }
                  `}
                >
                  {isLoading ? '提交中...' : initialData ? '保存修改' : '发布招募'}
                </button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
