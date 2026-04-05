import React, { useState, useEffect, useCallback } from 'react';
import {
  AcademicCapIcon,
  LightBulbIcon,
  ChartBarIcon,
  BoltIcon,
  TrophyIcon,
  ArrowPathIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  StarIcon,
  ClockIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';
import toast from '@/utils/toast';

interface ThinkingStep {
  order: number;
  name: string;
  description: string;
  prompt: string;
  result?: string;
}

interface ThinkingFramework {
  id: string;
  name: string;
  description: string;
  steps: ThinkingStep[];
  applicable_scenarios: string[];
  usage_count: number;
  success_rate: number;
}

interface ValueProposition {
  id: string;
  name: string;
  type: string;
  statement: string;
  explanation: string;
  priority: number;
  weight: number;
}

interface CognitiveBias {
  time_preference: Record<string, number>;
  risk_preference: string;
  detail_preference: string;
  info_source_preference: string;
  decision_style: string;
}

interface GrowthEvent {
  id: string;
  event_type: string;
  description: string;
  experience_gained: number;
  frameworks_unlocked: string[];
  values_refined: Record<string, number>;
  created_at: string;
}

interface DecisionLog {
  id: string;
  agent_id: string;
  problem: string;
  decision: string;
  confidence: number;
  framework_used: string;
  thinking_process: ThinkingStep[];
  evaluation: Record<string, any>;
  feedback?: string;
  feedback_score?: number;
  created_at: string;
}

interface AgentCognition {
  agent_id: string;
  frameworks: string[];
  values: Record<string, number>;
  cognitive_bias: CognitiveBias;
  experience_points: number;
  level: number;
  decision_quality: number;
  growth_history: GrowthEvent[];
}

type TabType = 'overview' | 'frameworks' | 'values' | 'growth' | 'decisions';

const AgentCognitionPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [frameworks, setFrameworks] = useState<ThinkingFramework[]>([]);
  const [values, setValues] = useState<ValueProposition[]>([]);
  const [cognition, setCognition] = useState<AgentCognition | null>(null);
  const [decisions, setDecisions] = useState<DecisionLog[]>([]);
  const [growthEvents, setGrowthEvents] = useState<GrowthEvent[]>([]);
  const [selectedDecision, setSelectedDecision] = useState<DecisionLog | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string>('agent_001');
  const [isApplying, setIsApplying] = useState(false);
  const [thinkingResult, setThinkingResult] = useState<any>(null);
  const [problemInput, setProblemInput] = useState('');

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [fwRes, vRes, cogRes, decRes, growthRes] = await Promise.all([
        api.get('/cognition/frameworks'),
        api.get('/cognition/values'),
        api.get(`/cognition/agent/${selectedAgentId}`),
        api.get(`/cognition/agent/${selectedAgentId}/decisions?limit=10`),
        api.get(`/cognition/agent/${selectedAgentId}/growth`),
      ]);

      setFrameworks(fwRes.data.frameworks || []);
      setValues(vRes.data.values || []);
      setCognition(cogRes.data);
      setDecisions(decRes.data.decisions || []);
      setGrowthEvents(growthRes.data.growth_events || []);
    } catch (error) {
      console.error('Failed to load cognition data:', error);
      toast.error('加载认知数据失败');
    } finally {
      setIsLoading(false);
    }
  }, [selectedAgentId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const applyFramework = async (frameworkId: string) => {
    if (!problemInput.trim()) {
      toast.error('请输入问题描述');
      return;
    }
    setIsApplying(true);
    try {
      const response = await api.post('/cognition/frameworks/apply', {
        framework_id: frameworkId,
        problem: problemInput,
        context: {},
      });
      setThinkingResult(response.data);
      toast.success('框架应用完成');
    } catch (error) {
      toast.error('应用框架失败');
    } finally {
      setIsApplying(false);
    }
  };

  const makeDecision = async () => {
    if (!problemInput.trim()) {
      toast.error('请输入问题描述');
      return;
    }
    setIsApplying(true);
    try {
      const response = await api.post('/cognition/decide', {
        problem: problemInput,
        context: {},
        agent_id: selectedAgentId,
      });
      toast.success('决策已生成');
      loadData();
    } catch (error) {
      toast.error('决策失败');
    } finally {
      setIsApplying(false);
    }
  };

  const provideFeedback = async (decisionId: string, score: number, feedback: string) => {
    try {
      await api.post(`/cognition/agent/${selectedAgentId}/feedback/${decisionId}`, {
        feedback,
        score,
      });
      toast.success('反馈已提交');
      loadData();
    } catch (error) {
      toast.error('提交反馈失败');
    }
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      core_value: 'bg-purple-100 text-purple-700',
      judgment_standard: 'bg-blue-100 text-blue-700',
      priority: 'bg-green-100 text-green-700',
      bottom_line: 'bg-red-100 text-red-700',
    };
    return colors[type] || 'bg-gray-100 text-gray-700';
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <AcademicCapIcon className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">思维框架</p>
              <p className="text-2xl font-bold text-gray-900">{frameworks.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <StarIcon className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">价值主张</p>
              <p className="text-2xl font-bold text-gray-900">{values.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <TrophyIcon className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">经验值</p>
              <p className="text-2xl font-bold text-gray-900">{cognition?.experience_points || 0} XP</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">决策质量</p>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round((cognition?.decision_quality || 0.5) * 100)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">快速决策</h2>
        <div className="space-y-4">
          <textarea
            value={problemInput}
            onChange={(e) => setProblemInput(e.target.value)}
            placeholder="输入需要决策的问题..."
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            rows={3}
          />
          <div className="flex gap-3">
            <button
              onClick={makeDecision}
              disabled={isApplying}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isApplying ? (
                <ArrowPathIcon className="w-4 h-4 animate-spin" />
              ) : (
                <SparklesIcon className="w-4 h-4" />
              )}
              生成决策
            </button>
          </div>
        </div>
      </div>

      {thinkingResult && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">思考过程</h2>
          <div className="space-y-3">
            {thinkingResult.steps?.map((step: any, idx: number) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-sm font-medium">
                    {step.order}
                  </span>
                  <span className="font-medium text-gray-900">{step.step}</span>
                </div>
                <p className="text-sm text-gray-600 ml-8">{step.description}</p>
              </div>
            ))}
          </div>
          {thinkingResult.conclusion && (
            <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="font-medium text-green-800">结论</p>
              <p className="text-sm text-green-700 mt-1">{thinkingResult.conclusion}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderFrameworks = () => (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">思维框架库</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {frameworks.map((fw) => (
            <motion.div
              key={fw.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-50 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => applyFramework(fw.id)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <LightBulbIcon className="w-5 h-5 text-yellow-500" />
                  <h3 className="font-medium text-gray-900">{fw.name}</h3>
                </div>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                  {Math.round(fw.success_rate * 100)}% 成功率
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{fw.description}</p>
              <div className="flex flex-wrap gap-1">
                {fw.applicable_scenarios.map((scenario, idx) => (
                  <span key={idx} className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded">
                    {scenario}
                  </span>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                <span>{fw.steps.length} 步骤</span>
                <span>使用 {fw.usage_count} 次</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderValues = () => (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">价值体系</h2>
        <div className="space-y-3">
          {values.map((v) => (
            <motion.div
              key={v.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-gray-50 rounded-lg p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <StarIcon className="w-4 h-4 text-yellow-500" />
                    <span className="font-medium text-gray-900">{v.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${getTypeColor(v.type)}`}>
                      {v.type}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 font-medium">{v.statement}</p>
                  <p className="text-sm text-gray-500 mt-1">{v.explanation}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-400">权重</p>
                  <p className="text-lg font-bold text-gray-700">{v.weight.toFixed(2)}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderGrowth = () => (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">成长记录</h2>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">等级</span>
            <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full font-bold">
              Lv.{cognition?.level || 1}
            </span>
          </div>
        </div>
        
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-500">经验值</span>
            <span className="text-gray-700">{cognition?.experience_points || 0} / {(cognition?.level || 1) * 100}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-purple-600 h-2 rounded-full transition-all"
              style={{ width: `${((cognition?.experience_points || 0) % 100)}%` }}
            />
          </div>
        </div>

        <div className="space-y-3">
          {growthEvents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <TrophyIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>暂无成长记录</p>
            </div>
          ) : (
            growthEvents.map((event) => (
              <div key={event.id} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">{event.event_type}</span>
                      {event.experience_gained > 0 && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                          +{event.experience_gained} XP
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">{event.description}</p>
                    {event.frameworks_unlocked && event.frameworks_unlocked.length > 0 && (
                      <p className="text-xs text-blue-600 mt-1">
                        解锁框架: {event.frameworks_unlocked.join(', ')}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(event.created_at).toLocaleDateString('zh-CN')}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );

  const renderDecisions = () => (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">决策历史</h2>
        {decisions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <ExclamationCircleIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>暂无决策历史</p>
          </div>
        ) : (
          <div className="space-y-3">
            {decisions.map((decision) => (
              <div
                key={decision.id}
                onClick={() => setSelectedDecision(decision)}
                className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 cursor-pointer transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{decision.problem}</p>
                    <p className="text-sm text-gray-600 mt-1">{decision.decision}</p>
                    <div className="flex items-center gap-2 mt-2">
                      {decision.framework_used && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                          {decision.framework_used}
                        </span>
                      )}
                      <span className="text-xs text-gray-400">
                        {new Date(decision.created_at).toLocaleString('zh-CN')}
                      </span>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    decision.confidence >= 0.7 ? 'bg-green-100 text-green-700' :
                    decision.confidence >= 0.5 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {Math.round(decision.confidence * 100)}% 置信度
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <ArrowPathIcon className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <AcademicCapIcon className="w-8 h-8 text-purple-600" />
            智能体认知中心
          </h1>
          <p className="text-gray-500 mt-1">思维框架 · 价值体系 · 决策引擎</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
          <div className="flex border-b border-gray-200 overflow-x-auto">
            {[
              { key: 'overview', label: '概览', icon: ChartBarIcon },
              { key: 'frameworks', label: '思维框架', icon: LightBulbIcon },
              { key: 'values', label: '价值体系', icon: StarIcon },
              { key: 'growth', label: '成长记录', icon: TrophyIcon },
              { key: 'decisions', label: '决策历史', icon: ClockIcon },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as TabType)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium whitespace-nowrap ${
                  activeTab === tab.key
                    ? 'text-purple-600 border-b-2 border-purple-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
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
            {activeTab === 'overview' && renderOverview()}
            {activeTab === 'frameworks' && renderFrameworks()}
            {activeTab === 'values' && renderValues()}
            {activeTab === 'growth' && renderGrowth()}
            {activeTab === 'decisions' && renderDecisions()}
          </motion.div>
        </AnimatePresence>

        <AnimatePresence>
          {selectedDecision && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
              onClick={() => setSelectedDecision(null)}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-bold text-gray-900">决策详情</h3>
                  <button
                    onClick={() => setSelectedDecision(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <span className="text-sm text-gray-500">问题</span>
                    <p className="text-gray-900 font-medium">{selectedDecision.problem}</p>
                  </div>

                  <div>
                    <span className="text-sm text-gray-500">决策结果</span>
                    <p className="text-gray-900">{selectedDecision.decision}</p>
                  </div>

                  <div>
                    <span className="text-sm text-gray-500 mb-2 block">思考过程</span>
                    <div className="space-y-2">
                      {selectedDecision.thinking_process?.map((step, idx) => (
                        <div key={idx} className="bg-gray-50 p-3 rounded-lg">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="w-5 h-5 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-xs">
                              {step.order}
                            </span>
                            <span className="font-medium text-gray-700">{step.name}</span>
                          </div>
                          <p className="text-sm text-gray-600 ml-7">{step.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-4 pt-4 border-t">
                    <div>
                      <span className="text-sm text-gray-500">置信度</span>
                      <p className={`font-bold ${
                        selectedDecision.confidence >= 0.7 ? 'text-green-600' :
                        selectedDecision.confidence >= 0.5 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {Math.round(selectedDecision.confidence * 100)}%
                      </p>
                    </div>
                    {selectedDecision.framework_used && (
                      <div>
                        <span className="text-sm text-gray-500">使用框架</span>
                        <p className="text-blue-600">{selectedDecision.framework_used}</p>
                      </div>
                    )}
                  </div>

                  {selectedDecision.feedback_score !== undefined && (
                    <div className="bg-green-50 p-3 rounded-lg">
                      <p className="text-sm text-green-700">
                        反馈评分: {Math.round(selectedDecision.feedback_score * 100)}%
                      </p>
                      {selectedDecision.feedback && (
                        <p className="text-sm text-green-600 mt-1">{selectedDecision.feedback}</p>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                  <button
                    onClick={() => setSelectedDecision(null)}
                    className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200"
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

export default AgentCognitionPanel;
