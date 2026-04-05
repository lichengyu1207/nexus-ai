import React, { useState, useEffect } from 'react';
import {
  BeakerIcon,
  PlayIcon,
  PauseIcon,
  CheckCircleIcon,
  UserGroupIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  PlusIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import api from '@/services/api';
import showToast from '@/utils/toast';

interface Experiment {
  id: string;
  name: string;
  feature: string;
  description: string;
  status: string;
  control_group: string;
  experiment_group: string;
  start_date: string;
  end_date: string;
  config: Record<string, any>;
}

interface ExperimentStats {
  experiment: Experiment;
  control: {
    users?: number;
    tasks_created?: number;
    feedback?: {
      count: number;
      avg_rating: number;
      negative: number;
      positive: number;
    };
    [key: string]: any;
  };
  treatment: {
    users?: number;
    tasks_created?: number;
    feedback?: {
      count: number;
      avg_rating: number;
      negative: number;
      positive: number;
    };
    [key: string]: any;
  };
}

interface OverallStats {
  total_users: number;
  control_users: number;
  treatment_users: number;
  experiments: ExperimentStats[];
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  running: { label: '运行中', color: 'bg-green-100 text-green-700', icon: PlayIcon },
  paused: { label: '已暂停', color: 'bg-yellow-100 text-yellow-700', icon: PauseIcon },
  completed: { label: '已完成', color: 'bg-blue-100 text-blue-700', icon: CheckCircleIcon },
};

const ABTestPage: React.FC = () => {
  const [stats, setStats] = useState<OverallStats | null>(null);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<ExperimentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newExperiment, setNewExperiment] = useState({
    name: '',
    feature: 'query_parsing',
    description: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, expRes] = await Promise.all([
        api.get('ab-tests/stats/overall'),
        api.get('ab-tests/experiments'),
      ]);
      setStats(statsRes.data);
      setExperiments(expRes.data);
    } catch (error) {
      showToast.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExperiment = async () => {
    if (!newExperiment.name || !newExperiment.feature) {
      showToast.error('请填写实验名称和功能');
      return;
    }

    try {
      await api.post('ab-tests/experiments', newExperiment);
      showToast.success('实验创建成功');
      setShowCreateModal(false);
      setNewExperiment({ name: '', feature: 'query_parsing', description: '' });
      fetchData();
    } catch (error: any) {
      showToast.error(error.response?.data?.detail || '创建失败');
    }
  };

  const handleUpdateStatus = async (experimentId: string, status: string) => {
    try {
      await api.put(`/api/ab-tests/experiments/${experimentId}/status?status=${status}`);
      showToast.success('状态已更新');
      fetchData();
    } catch (error) {
      showToast.error('更新失败');
    }
  };

  const handleViewStats = async (experimentId: string) => {
    try {
      const response = await api.get(`/api/ab-tests/experiments/${experimentId}/stats`);
      setSelectedExperiment(response.data);
    } catch (error) {
      showToast.error('获取统计失败');
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  const calculateImprovement = (control: number, treatment: number) => {
    if (!control) return { value: 0, positive: true };
    const change = ((treatment - control) / control) * 100;
    return { value: Math.abs(change).toFixed(1), positive: change >= 0 };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">A/B 测试</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <PlusIcon className="w-5 h-5" />
          创建实验
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">总用户数</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_users}</p>
              </div>
              <UserGroupIcon className="w-8 h-8 text-primary-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">对照组</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.control_users}</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-blue-600 font-bold text-sm">C</span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">实验组</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.treatment_users}</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                <span className="text-green-600 font-bold text-sm">T</span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">运行中实验</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {experiments.filter(e => e.status === 'running').length}
                </p>
              </div>
              <BeakerIcon className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">实验列表</h2>
        </div>

        {experiments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            暂无实验数据，点击"创建实验"开始第一个 A/B 测试
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {experiments.map((experiment) => {
              const statusConfig = STATUS_CONFIG[experiment.status] || STATUS_CONFIG.running;
              const StatusIcon = statusConfig.icon;

              return (
                <div key={experiment.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                        <BeakerIcon className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-gray-900 dark:text-white">{experiment.name}</h3>
                          <span className={`px-2 py-0.5 rounded text-xs ${statusConfig.color}`}>
                            {statusConfig.label}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          功能: {experiment.feature} · 开始: {formatDate(experiment.start_date)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleViewStats(experiment.id)}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                        title="查看统计"
                      >
                        <EyeIcon className="w-5 h-5" />
                      </button>

                      {experiment.status === 'running' && (
                        <button
                          onClick={() => handleUpdateStatus(experiment.id, 'paused')}
                          className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg"
                          title="暂停"
                        >
                          <PauseIcon className="w-5 h-5" />
                        </button>
                      )}

                      {experiment.status === 'paused' && (
                        <button
                          onClick={() => handleUpdateStatus(experiment.id, 'running')}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                          title="恢复"
                        >
                          <PlayIcon className="w-5 h-5" />
                        </button>
                      )}

                      {experiment.status !== 'completed' && (
                        <button
                          onClick={() => handleUpdateStatus(experiment.id, 'completed')}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                          title="完成"
                        >
                          <CheckCircleIcon className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {selectedExperiment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/30" onClick={() => setSelectedExperiment(null)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                实验统计: {selectedExperiment.experiment.name}
              </h3>
              <button
                onClick={() => setSelectedExperiment(null)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <h4 className="font-medium text-blue-800 dark:text-blue-300 mb-4">对照组</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">用户数</span>
                      <span className="font-medium">{selectedExperiment.control.users || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">任务数</span>
                      <span className="font-medium">{selectedExperiment.control.tasks_created || 0}</span>
                    </div>
                    {selectedExperiment.control.feedback && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">反馈数</span>
                          <span className="font-medium">{selectedExperiment.control.feedback.count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">平均评分</span>
                          <span className="font-medium">
                            {selectedExperiment.control.feedback.avg_rating?.toFixed(2) || '-'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">不满意率</span>
                          <span className="font-medium text-red-600">
                            {selectedExperiment.control.feedback.count > 0
                              ? `${((selectedExperiment.control.feedback.negative / selectedExperiment.control.feedback.count) * 100).toFixed(1)}%`
                              : '-'}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                  <h4 className="font-medium text-green-800 dark:text-green-300 mb-4">实验组</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">用户数</span>
                      <span className="font-medium">{selectedExperiment.treatment.users || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">任务数</span>
                      <span className="font-medium">{selectedExperiment.treatment.tasks_created || 0}</span>
                    </div>
                    {selectedExperiment.treatment.feedback && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">反馈数</span>
                          <span className="font-medium">{selectedExperiment.treatment.feedback.count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">平均评分</span>
                          <span className="font-medium">
                            {selectedExperiment.treatment.feedback.avg_rating?.toFixed(2) || '-'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">不满意率</span>
                          <span className="font-medium text-red-600">
                            {selectedExperiment.treatment.feedback.count > 0
                              ? `${((selectedExperiment.treatment.feedback.negative / selectedExperiment.treatment.feedback.count) * 100).toFixed(1)}%`
                              : '-'}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {selectedExperiment.control.feedback && selectedExperiment.treatment.feedback && (
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 dark:text-white mb-4">对比分析</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">满意度变化</p>
                      {(() => {
                        const controlRate = selectedExperiment.control.feedback.count > 0
                          ? selectedExperiment.control.feedback.positive / selectedExperiment.control.feedback.count
                          : 0;
                        const treatmentRate = selectedExperiment.treatment.feedback.count > 0
                          ? selectedExperiment.treatment.feedback.positive / selectedExperiment.treatment.feedback.count
                          : 0;
                        const improvement = calculateImprovement(controlRate * 100, treatmentRate * 100);
                        return (
                          <div className={`flex items-center justify-center gap-1 ${improvement.positive ? 'text-green-600' : 'text-red-600'}`}>
                            {improvement.positive ? (
                              <ArrowTrendingUpIcon className="w-5 h-5" />
                            ) : (
                              <ArrowTrendingDownIcon className="w-5 h-5" />
                            )}
                            <span className="text-xl font-bold">{improvement.value}%</span>
                          </div>
                        );
                      })()}
                    </div>

                    <div className="text-center">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">任务创建变化</p>
                      {(() => {
                        const improvement = calculateImprovement(
                          selectedExperiment.control.tasks_created || 0,
                          selectedExperiment.treatment.tasks_created || 0
                        );
                        return (
                          <div className={`flex items-center justify-center gap-1 ${improvement.positive ? 'text-green-600' : 'text-red-600'}`}>
                            {improvement.positive ? (
                              <ArrowTrendingUpIcon className="w-5 h-5" />
                            ) : (
                              <ArrowTrendingDownIcon className="w-5 h-5" />
                            )}
                            <span className="text-xl font-bold">{improvement.value}%</span>
                          </div>
                        );
                      })()}
                    </div>

                    <div className="text-center">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">反馈率变化</p>
                      {(() => {
                        const controlRate = (selectedExperiment.control.feedback?.count || 0) / (selectedExperiment.control.users || 1);
                        const treatmentRate = (selectedExperiment.treatment.feedback?.count || 0) / (selectedExperiment.treatment.users || 1);
                        const improvement = calculateImprovement(controlRate * 100, treatmentRate * 100);
                        return (
                          <div className={`flex items-center justify-center gap-1 ${improvement.positive ? 'text-green-600' : 'text-red-600'}`}>
                            {improvement.positive ? (
                              <ArrowTrendingUpIcon className="w-5 h-5" />
                            ) : (
                              <ArrowTrendingDownIcon className="w-5 h-5" />
                            )}
                            <span className="text-xl font-bold">{improvement.value}%</span>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/30" onClick={() => setShowCreateModal(false)} />
          <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">创建新实验</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  实验名称
                </label>
                <input
                  type="text"
                  value={newExperiment.name}
                  onChange={(e) => setNewExperiment({ ...newExperiment, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                  placeholder="例如: 查询解析算法优化"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  测试功能
                </label>
                <select
                  value={newExperiment.feature}
                  onChange={(e) => setNewExperiment({ ...newExperiment, feature: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                >
                  <option value="query_parsing">查询解析</option>
                  <option value="price_estimation">价格估算</option>
                  <option value="recommendation">推荐算法</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  描述
                </label>
                <textarea
                  value={newExperiment.description}
                  onChange={(e) => setNewExperiment({ ...newExperiment, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                  rows={3}
                  placeholder="实验目的和预期效果..."
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300"
              >
                取消
              </button>
              <button
                onClick={handleCreateExperiment}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import { XMarkIcon } from '@heroicons/react/24/outline';

export default ABTestPage;
