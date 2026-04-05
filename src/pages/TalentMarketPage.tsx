import React, { useState, useEffect, useCallback } from 'react';
import {
  SparklesIcon,
  UserGroupIcon,
  StarIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  PlusIcon,
  XMarkIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';
import toast from '@/utils/toast';

interface Agent {
  id: string;
  name: string;
  rarity: 'N' | 'R' | 'SR' | 'SSR' | 'UR';
  department: string;
  level: number;
  max_level: number;
  skills: AgentSkill[];
  base_salary: number;
  recruit_cost: number;
  description: string;
  avatar?: string;
  efficiency: number;
}

interface AgentSkill {
  name: string;
  description: string;
  type: 'active' | 'passive';
  effect: string;
}

interface UserAgent extends Agent {
  user_agent_id: string;
  experience: number;
  assigned_department?: string;
  status: 'idle' | 'busy' | 'training';
}

interface RecruitResult {
  success: boolean;
  agent?: Agent;
  is_new: boolean;
  cost: number;
  guarantee_info?: {
    sr_guarantee_count: number;
    ssr_guarantee_count: number;
  };
}

interface Bond {
  id: string;
  name: string;
  description: string;
  required_agents: string[];
  effect: string;
  active: boolean;
}

const rarityConfig = {
  N: { color: 'bg-gray-500', textColor: 'text-gray-700', label: '普通', glow: '' },
  R: { color: 'bg-blue-500', textColor: 'text-blue-700', label: '稀有', glow: '' },
  SR: { color: 'bg-purple-500', textColor: 'text-purple-700', label: '史诗', glow: 'shadow-purple-300/50' },
  SSR: { color: 'bg-orange-500', textColor: 'text-orange-700', label: '传说', glow: 'shadow-orange-300/50' },
  UR: { color: 'bg-gradient-to-r from-yellow-400 to-red-500', textColor: 'text-yellow-700', label: '神话', glow: 'shadow-yellow-300/50 animate-pulse' },
};

const departmentConfig: Record<string, { icon: string; label: string }> = {
  li: { icon: '👤', label: '吏部' },
  hu: { icon: '💰', label: '户部' },
  li_guan: { icon: '📝', label: '礼部' },
  bing: { icon: '⚔️', label: '兵部' },
  xing: { icon: '⚖️', label: '刑部' },
  gong: { icon: '🔧', label: '工部' },
};

type TabType = 'recruit' | 'collection' | 'cabinet';

const TalentMarketPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('recruit');
  const [isLoading, setIsLoading] = useState(true);
  const [userPoints, setUserPoints] = useState(0);
  const [recruitType, setRecruitType] = useState<'basic' | 'premium'>('basic');
  const [isRecruiting, setIsRecruiting] = useState(false);
  const [recruitResult, setRecruitResult] = useState<RecruitResult | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [myAgents, setMyAgents] = useState<UserAgent[]>([]);
  const [allAgents, setAllAgents] = useState<Agent[]>([]);
  const [bonds, setBonds] = useState<Bond[]>([]);
  const [guaranteeInfo, setGuaranteeInfo] = useState({
    sr_guarantee_count: 0,
    ssr_guarantee_count: 0,
    sr_guarantee_max: 10,
    ssr_guarantee_max: 50,
  });
  const [selectedAgent, setSelectedAgent] = useState<UserAgent | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [pointsRes, agentsRes, bondsRes, allAgentsRes] = await Promise.all([
        api.get('/integral/balance'),
        api.get('/recruit/my-agents'),
        api.get('/recruit/bonds'),
        api.get('/recruit/agents'),
      ]);

      setUserPoints(pointsRes.data.balance || 0);
      setMyAgents(agentsRes.data.agents || []);
      setBonds(bondsRes.data.bonds || []);
      setAllAgents(allAgentsRes.data.agents || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRecruit = async () => {
    const cost = recruitType === 'basic' ? 100 : 1000;
    if (userPoints < cost) {
      toast.error('积分不足');
      return;
    }

    setIsRecruiting(true);
    setShowResult(false);

    try {
      const response = await api.post('/recruit/recruit', {
        recruit_type: recruitType,
      });

      setRecruitResult(response.data);
      setShowResult(true);
      setUserPoints(prev => prev - cost);
      
      if (response.data.guarantee_info) {
        setGuaranteeInfo(prev => ({
          ...prev,
          ...response.data.guarantee_info,
        }));
      }

      if (response.data.agent) {
        loadData();
      }
    } catch (error) {
      toast.error('招募失败');
    } finally {
      setIsRecruiting(false);
    }
  };

  const getRarityBadge = (rarity: string) => {
    const config = rarityConfig[rarity as keyof typeof rarityConfig] || rarityConfig.N;
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${config.color} text-white ${config.glow}`}>
        {config.label}
      </span>
    );
  };

  const renderRecruitTab = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">人才招募</h2>
            <p className="text-blue-100">招募强力智能体，组建你的内阁团队</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-100">当前积分</p>
            <p className="text-3xl font-bold">{userPoints.toLocaleString()}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setRecruitType('basic')}
            className={`p-4 rounded-lg border-2 transition-all ${
              recruitType === 'basic'
                ? 'bg-white/20 border-white'
                : 'bg-white/10 border-white/30 hover:bg-white/20'
            }`}
          >
            <h3 className="font-bold text-lg">基础招募</h3>
            <p className="text-2xl font-bold">100 积分</p>
            <p className="text-xs text-blue-100 mt-1">N 60% | R 30% | SR 8%</p>
          </button>

          <button
            onClick={() => setRecruitType('premium')}
            className={`p-4 rounded-lg border-2 transition-all ${
              recruitType === 'premium'
                ? 'bg-white/20 border-white'
                : 'bg-white/10 border-white/30 hover:bg-white/20'
            }`}
          >
            <h3 className="font-bold text-lg">高级招募</h3>
            <p className="text-2xl font-bold">1000 积分</p>
            <p className="text-xs text-blue-100 mt-1">SR 20% | SSR 8% | UR 2%</p>
          </button>
        </div>

        <div className="mt-4 flex items-center justify-between text-sm">
          <div>
            <span className="text-blue-100">SR保底: {guaranteeInfo.sr_guarantee_count}/{guaranteeInfo.sr_guarantee_max}</span>
            <span className="mx-2">|</span>
            <span className="text-blue-100">SSR保底: {guaranteeInfo.ssr_guarantee_count}/{guaranteeInfo.ssr_guarantee_max}</span>
          </div>
        </div>
      </div>

      <div className="flex justify-center">
        <motion.button
          onClick={handleRecruit}
          disabled={isRecruiting}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="px-12 py-4 bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-xl font-bold rounded-xl shadow-lg disabled:opacity-50"
        >
          {isRecruiting ? (
            <ArrowPathIcon className="w-6 h-6 animate-spin inline mr-2" />
          ) : (
            <SparklesIcon className="w-6 h-6 inline mr-2" />
          )}
          {isRecruiting ? '招募中...' : '立即招募'}
        </motion.button>
      </div>

      <AnimatePresence>
        {showResult && recruitResult && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowResult(false)}
          >
            <motion.div
              className="bg-white rounded-2xl p-8 max-w-md w-full text-center"
              onClick={e => e.stopPropagation()}
            >
              {recruitResult.agent && (
                <>
                  <div className={`w-24 h-24 mx-auto rounded-full ${rarityConfig[recruitResult.agent.rarity].color} flex items-center justify-center text-4xl mb-4 ${rarityConfig[recruitResult.agent.rarity].glow}`}>
                    {departmentConfig[recruitResult.agent.department]?.icon || '🤖'}
                  </div>
                  <h3 className="text-2xl font-bold mb-2">{recruitResult.agent.name}</h3>
                  <div className="flex justify-center gap-2 mb-4">
                    {getRarityBadge(recruitResult.agent.rarity)}
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                      Lv.{recruitResult.agent.level}
                    </span>
                  </div>
                  <p className="text-gray-600 mb-4">{recruitResult.agent.description}</p>
                  
                  {recruitResult.agent.skills.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-3 mb-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">技能</p>
                      {recruitResult.agent.skills.map((skill, idx) => (
                        <div key={idx} className="text-sm text-gray-600">
                          <span className="font-medium">{skill.name}</span>: {skill.description}
                        </div>
                      ))}
                    </div>
                  )}

                  {recruitResult.is_new ? (
                    <p className="text-green-600 font-medium">🎉 新智能体加入内阁!</p>
                  ) : (
                    <p className="text-blue-600">智能体等级提升!</p>
                  )}
                </>
              )}
              
              <button
                onClick={() => setShowResult(false)}
                className="mt-4 px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                关闭
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  const renderCollectionTab = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">智能体图鉴</h2>
        <p className="text-sm text-gray-500">
          已收集: {myAgents.length} / {allAgents.length}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {allAgents.map(agent => {
          const owned = myAgents.some(a => a.id === agent.id);
          return (
            <div
              key={agent.id}
              className={`bg-white rounded-xl p-4 border-2 transition-all cursor-pointer ${
                owned ? 'border-blue-300 hover:border-blue-500' : 'border-gray-200 opacity-60'
              }`}
              onClick={() => owned && setSelectedAgent(myAgents.find(a => a.id === agent.id) || null)}
            >
              <div className={`w-16 h-16 mx-auto rounded-full ${rarityConfig[agent.rarity].color} flex items-center justify-center text-2xl mb-3 ${owned ? '' : 'grayscale'}`}>
                {departmentConfig[agent.department]?.icon || '🤖'}
              </div>
              <h3 className="font-medium text-center text-gray-900 truncate">{owned ? agent.name : '???'}</h3>
              <div className="flex justify-center mt-2">
                {getRarityBadge(agent.rarity)}
              </div>
              {!owned && (
                <p className="text-xs text-center text-gray-400 mt-2">未收集</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderCabinetTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-900 mb-4">已激活羁绊</h2>
        {bonds.filter(b => b.active).length === 0 ? (
          <p className="text-gray-500 text-center py-4">暂无激活的羁绊</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {bonds.filter(b => b.active).map(bond => (
              <div key={bond.id} className="bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg p-4 border border-yellow-200">
                <div className="flex items-center gap-2 mb-2">
                  <StarIcon className="w-5 h-5 text-yellow-500" />
                  <h3 className="font-bold text-gray-900">{bond.name}</h3>
                </div>
                <p className="text-sm text-gray-600 mb-2">{bond.description}</p>
                <p className="text-sm font-medium text-orange-600">{bond.effect}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">我的智能体 ({myAgents.length})</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {myAgents.map(agent => (
            <div
              key={agent.user_agent_id}
              onClick={() => setSelectedAgent(agent)}
              className="bg-white rounded-xl p-4 border border-gray-200 cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full ${rarityConfig[agent.rarity].color} flex items-center justify-center text-xl`}>
                    {departmentConfig[agent.department]?.icon || '🤖'}
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">{agent.name}</h3>
                    <div className="flex items-center gap-2">
                      {getRarityBadge(agent.rarity)}
                      <span className="text-xs text-gray-500">Lv.{agent.level}</span>
                    </div>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  agent.status === 'busy' ? 'bg-yellow-100 text-yellow-700' :
                  agent.status === 'training' ? 'bg-blue-100 text-blue-700' :
                  'bg-green-100 text-green-700'
                }`}>
                  {agent.status === 'busy' ? '工作中' : agent.status === 'training' ? '训练中' : '空闲'}
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">效率</span>
                  <span className="font-medium">{Math.round(agent.efficiency * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${agent.efficiency * 100}%` }}
                  />
                </div>
              </div>

              {agent.assigned_department && (
                <div className="mt-3 flex items-center gap-2 text-sm text-gray-500">
                  <UserGroupIcon className="w-4 h-4" />
                  <span>派遣至: {departmentConfig[agent.assigned_department]?.label || agent.assigned_department}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
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
            <UserGroupIcon className="w-8 h-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">人才市场</h1>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
          <div className="flex border-b border-gray-200">
            {[
              { key: 'recruit', label: '招募', icon: <SparklesIcon className="w-4 h-4" /> },
              { key: 'collection', label: '图鉴', icon: <StarIcon className="w-4 h-4" /> },
              { key: 'cabinet', label: '我的内阁', icon: <UserGroupIcon className="w-4 h-4" /> },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as TabType)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium ${
                  activeTab === tab.key
                    ? 'text-blue-600 border-b-2 border-blue-600'
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
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'recruit' && renderRecruitTab()}
            {activeTab === 'collection' && renderCollectionTab()}
            {activeTab === 'cabinet' && renderCabinetTab()}
          </motion.div>
        </AnimatePresence>

      </div>
    </div>
  );
};

export default TalentMarketPage;
