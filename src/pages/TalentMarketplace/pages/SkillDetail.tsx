import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeftIcon, PlayIcon, StarIcon, CodeBracketIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import type { Skill } from '../types';
import { SKILL_CATEGORIES } from '../types';

async function fetchSkill(id: string): Promise<Skill> {
  const response = await fetch(`/api/skills/${id}`);
  if (!response.ok) throw new Error('Failed to fetch skill');
  return response.json();
}

export function SkillDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: skill, isLoading, error } = useQuery({
    queryKey: ['skill', id],
    queryFn: () => fetchSkill(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-slate-800 rounded w-1/4" />
            <div className="h-64 bg-slate-800 rounded-xl" />
            <div className="h-32 bg-slate-800 rounded-xl" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !skill) {
    return (
      <div className="min-h-screen bg-slate-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">加载技能详情失败</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-amber-500 text-slate-900 rounded-lg"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

  const category = SKILL_CATEGORIES[skill.category] || { label: skill.category, icon: 'CubeIcon' };

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        <motion.button
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          返回技能市场
        </motion.button>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 overflow-hidden"
        >
          <div className="p-6 border-b border-slate-700/50">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                  <span className="text-2xl">⚡</span>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white mb-2">{skill.name}</h1>
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-1 text-xs bg-amber-500/20 text-amber-400 rounded-full">
                      {category.label}
                    </span>
                    <div className="flex items-center gap-1">
                      <StarIcon className="w-4 h-4 text-amber-400 fill-amber-400" />
                      <span className="text-sm text-slate-300">{skill.rating.toFixed(1)}</span>
                    </div>
                    <span className="text-sm text-slate-400">
                      {skill.callCount.toLocaleString()} 次调用
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-2xl font-bold text-amber-400">
                  ¥{skill.price}
                </div>
                <div className="text-sm text-slate-400">
                  {skill.priceType === 'per_use' ? '每次调用' : '月订阅'}
                </div>
              </div>
            </div>
          </div>

          <div className="p-6">
            <h2 className="text-lg font-semibold text-white mb-3">描述</h2>
            <p className="text-slate-300 leading-relaxed">{skill.description}</p>
          </div>

          {skill.documentation && (
            <div className="p-6 border-t border-slate-700/50">
              <div className="flex items-center gap-2 mb-3">
                <DocumentTextIcon className="w-5 h-5 text-amber-400" />
                <h2 className="text-lg font-semibold text-white">文档</h2>
              </div>
              <div className="bg-slate-900/50 rounded-xl p-4 text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                {skill.documentation}
              </div>
            </div>
          )}

          {skill.exampleCode && (
            <div className="p-6 border-t border-slate-700/50">
              <div className="flex items-center gap-2 mb-3">
                <CodeBracketIcon className="w-5 h-5 text-amber-400" />
                <h2 className="text-lg font-semibold text-white">示例代码</h2>
              </div>
              <pre className="bg-slate-900/50 rounded-xl p-4 text-sm text-slate-300 overflow-x-auto">
                <code>{skill.exampleCode}</code>
              </pre>
            </div>
          )}

          <div className="p-6 border-t border-slate-700/50">
            <h2 className="text-lg font-semibold text-white mb-3">标签</h2>
            <div className="flex flex-wrap gap-2">
              {skill.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 text-sm bg-slate-700/50 text-slate-300 rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div className="p-6 border-t border-slate-700/50 flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex-1 py-3 bg-amber-500 text-slate-900 font-semibold rounded-xl hover:bg-amber-400 transition-colors flex items-center justify-center gap-2"
            >
              <PlayIcon className="w-5 h-5" />
              {skill.priceType === 'per_use' ? '立即调用' : '订阅技能'}
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-6 py-3 border border-amber-500/50 text-amber-400 font-semibold rounded-xl hover:bg-amber-500/10 transition-colors"
            >
              查看演示
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
