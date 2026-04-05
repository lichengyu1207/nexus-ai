import React, { useState, useEffect, useCallback } from 'react';
import {
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  ChartBarIcon,
  CpuChipIcon,
  BeakerIcon,
  TrophyIcon,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';
import toast from '@/utils/toast';

interface TrainingSession {
  id: string;
  status: 'idle' | 'running' | 'paused' | 'completed';
  current_episode: number;
  total_episodes: number;
  best_reward: number;
  win_rate: number;
}

interface AgentStats {
  attacker_wins: number;
  defender_wins: number;
  total_games: number;
  best_attacker: string;
  best_defender: string;
}

interface ModelCheckpoint {
  id: string;
  name: string;
  created_at: string;
  win_rate: number;
  is_active: boolean;
}

type TabType = 'training' | 'stats' | 'models';

const SelfPlayPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('training');
  const [isLoading, setIsLoading] = useState(true);
  const [session, setSession] = useState<TrainingSession | null>(null);
  const [stats, setStats] = useState<AgentStats | null>(null);
  const [models, setModels] = useState<ModelCheckpoint[]>([]);
  const [isStarting, setIsStarting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [sessionRes, statsRes, modelsRes] = await Promise.all([
        api.get('/selfplay/session'),
        api.get('/selfplay/stats'),
        api.get('/selfplay/models'),
      ]);
      setSession(sessionRes.data);
      setStats(statsRes.data);
      setModels(modelsRes.data.models || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const startTraining = async () => {
    setIsStarting(true);
    try {
      const response = await api.post('/selfplay/start', { episodes: 1000 });
      if (response.data.success) {
        toast.success('训练已启动');
        loadData();
      }
    } catch (error) {
      toast.error('启动训练失败');
    } finally {
      setIsStarting(false);
    }
  };

  const stopTraining = async () => {
    try {
      await api.post('/selfplay/stop');
      toast.success('训练已停止');
      loadData();
    } catch (error) {
      toast.error('停止训练失败');
    }
  };

  const activateModel = async (modelId: string) => {
    try {
      await api.post(`/selfplay/models/${modelId}/activate`);
      toast.success('模型已激活');
      loadData();
    } catch (error) {
      toast.error('激活模型失败');
    }
  };

  const renderTrainingTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">训练控制台</h2>
          <div className="flex gap-2">
            {session?.status === 'running' ? (
              <button
                onClick={stopTraining}
                className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                <PauseIcon className="w-4 h-4" />
                停止训练
              </button>
            ) : (
              <button
                onClick={startTraining}
                disabled={isStarting}
                className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
              >
                <PlayIcon className="w-4 h-4" />
                {isStarting ? '启动中...' : '开始训练'}
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <BeakerIcon className="w-5 h-5 text-purple-500" />
              <span className="text-gray-500">当前轮次</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {session?.current_episode || 0} / {session?.total_episodes || 0}
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrophyIcon className="w-5 h-5 text-yellow-500" />
              <span className="text-gray-500">最佳奖励</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {session?.best_reward?.toFixed(2) || 0}
            </p>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <ChartBarIcon className="w-5 h-5 text-blue-500" />
              <span className="text-gray-500">胜率</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {((session?.win_rate || 0) * 100).toFixed(1)}%
            </p>
          </div>
        </div>

        {session?.status === 'running' && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-gradient-to-r from-green-400 to-blue-500 h-4 rounded-full transition-all"
                style={{ width: `${((session?.current_episode || 0) / (session?.total_episodes || 1)) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderStatsTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrophyIcon className="w-5 h-5 text-green-500" />
            <span className="text-gray-500">攻击方胜</span>
          </div>
          <p className="text-2xl font-bold text-green-600">{stats?.attacker_wins || 0}</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrophyIcon className="w-5 h-5 text-blue-500" />
            <span className="text-gray-500">防御方胜</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">{stats?.defender_wins || 0}</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-2">
            <CpuChipIcon className="w-5 h-5 text-purple-500" />
            <span className="text-gray-500">总对局</span>
          </div>
          <p className="text-2xl font-bold text-purple-600">{stats?.total_games || 0}</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">最佳智能体</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <p className="text-sm text-gray-500 mb-1">最佳攻击者</p>
            <p className="font-bold text-green-700">{stats?.best_attacker || '暂无'}</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <p className="text-sm text-gray-500 mb-1">最佳防御者</p>
            <p className="font-bold text-blue-700">{stats?.best_defender || '暂无'}</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderModelsTab = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">模型版本</h3>
      {models.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <CpuChipIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>暂无保存的模型</p>
        </div>
      ) : (
        <div className="space-y-3">
          {models.map((model) => (
            <div
              key={model.id}
              className={`flex items-center justify-between p-4 rounded-lg border-2 ${
                model.is_active ? 'border-green-300 bg-green-50' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full ${model.is_active ? 'bg-green-500' : 'bg-gray-400'} flex items-center justify-center`}>
                  <CpuChipIcon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{model.name}</h4>
                  <p className="text-sm text-gray-500">{new Date(model.created_at).toLocaleString('zh-CN')}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-sm text-gray-500">胜率</p>
                  <p className="font-bold text-blue-600">{(model.win_rate * 100).toFixed(1)}%</p>
                </div>
                {!model.is_active && (
                  <button
                    onClick={() => activateModel(model.id)}
                    className="px-3 py-1 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600"
                  >
                    激活
                  </button>
                )}
                {model.is_active && (
                  <span className="px-3 py-1 bg-green-500 text-white text-sm rounded-lg">当前</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <ArrowPathIcon className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <BeakerIcon className="w-8 h-8 text-purple-600" />
            <h1 className="text-2xl font-bold text-gray-900">自博弈训练系统</h1>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
          >
            <ArrowPathIcon className="w-4 h-4" />
            刷新
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
          <div className="flex border-b border-gray-200">
            {[
              { key: 'training', label: '训练控制', icon: <PlayIcon className="w-4 h-4" /> },
              { key: 'stats', label: '对战统计', icon: <ChartBarIcon className="w-4 h-4" /> },
              { key: 'models', label: '模型版本', icon: <CpuChipIcon className="w-4 h-4" /> },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as TabType)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium ${
                  activeTab === tab.key
                    ? 'text-purple-600 border-b-2 border-purple-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {activeTab === 'training' && renderTrainingTab()}
            {activeTab === 'stats' && renderStatsTab()}
            {activeTab === 'models' && renderModelsTab()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default SelfPlayPage;
