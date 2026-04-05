import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import learningApi from '@/api/learning';

const LearningPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const { data: status } = useQuery({ queryKey: ['learningStatus'], queryFn: learningApi.getStatus });
  const { data: experiences } = useQuery({ queryKey: ['learningExperiences'], queryFn: () => learningApi.getExperiences(selectedAgent || '', 20), enabled: !!selectedAgent });
  const { data: abTests } = useQuery({ queryKey: ['learningABTests'], queryFn: () => learningApi.getABTests('running') });

  const trainMutation = useMutation({
    mutationFn: (agentId: string) => learningApi.startTraining({ agent_id: agentId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['learningStatus'] }),
  });

  const reflectionMutation = useMutation({
    mutationFn: (agentId: string) => learningApi.triggerReflection({ agent_id: agentId }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['learningStatus'] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">学习系统</h2>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-green-500 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">已注册智能体</p>
          <p className="text-2xl font-bold">{status?.registered_agents || 0}</p>
        </div>
        <div className="bg-blue-500 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">活跃训练</p>
          <p className="text-2xl font-bold">{status?.active_trainings || 0}</p>
        </div>
        <div className="bg-purple-500 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">总经验数</p>
          <p className="text-2xl font-bold">{status?.total_experiences || 0}</p>
        </div>
        <div className="bg-orange-500 rounded-xl p-4 text-white">
          <p className="text-sm opacity-80">平均健康分</p>
          <p className="text-2xl font-bold">{status?.avg_health_score?.toFixed(1) || 0}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-4">快速操作</h3>
          <div className="space-y-3">
            <button
              onClick={() => selectedAgent && trainMutation.mutate(selectedAgent)}
              disabled={!selectedAgent || trainMutation.isPending}
              className="w-full py-2 bg-primary-500 text-white rounded-lg disabled:opacity-50"
            >
              {trainMutation.isPending ? '训练中...' : '开始训练'}
            </button>
            <button
              onClick={() => selectedAgent && reflectionMutation.mutate(selectedAgent)}
              disabled={!selectedAgent || reflectionMutation.isPending}
              className="w-full py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50"
            >
              {reflectionMutation.isPending ? '反思中...' : '触发反思'}
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold mb-4">A/B测试</h3>
          <div className="space-y-2">
            {abTests?.tests?.slice(0, 5).map((test) => (
              <div key={test.test_id} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{test.test_id.slice(0, 8)}</span>
                  <span className="text-xs text-green-600">运行中</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  A: {test.results.version_a.success_rate.toFixed(1)}% vs B: {test.results.version_b.success_rate.toFixed(1)}%
                </p>
              </div>
            ))}
            {(!abTests?.tests || abTests.tests.length === 0) && (
              <p className="text-center py-4 text-gray-500 text-sm">暂无运行中的测试</p>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold mb-4">经验记录</h3>
        {experiences?.experiences?.length === 0 ? (
          <p className="text-center py-8 text-gray-500">选择一个智能体查看经验记录</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {experiences?.experiences?.map((exp) => (
              <div key={exp.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div>
                  <p className="font-medium text-sm">{exp.task_type}</p>
                  <p className="text-xs text-gray-500">{exp.success ? '成功' : '失败'} · {exp.duration}ms</p>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs ${exp.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  +{exp.reward}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LearningPage;
