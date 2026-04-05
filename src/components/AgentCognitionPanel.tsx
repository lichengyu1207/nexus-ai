import React, { useState, useEffect, useCallback } from 'react';
import {
  BrainIcon,
  LightBulbIcon,
  ChartBarIcon,
  ClockIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  StarIcon,
  BeakerIcon,
  ScaleIcon,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';
import api from '@/services/api';
import toast from '@/utils/toast';

interface Framework {
  id: string;
  name: string;
  description: string;
  steps: Array<{ order: number; name: string; description: string }>;
  applicable_scenarios: string[];
  usage_count: number;
  success_rate: number;
}

interface Value {
  id: string;
  name: string;
  type: string;
  statement: string;
  explanation: string;
  priority: number;
  weight: number;
}

interface CognitionState {
  agent_id: string;
  frameworks: string[];
  values: Record<string, number>;
  cognitive_bias: {
    time_preference: Record<string, number>;
    risk_preference: string;
    detail_preference: string;
  };
  experience_points: number;
  level: number;
  decision_quality: number;
  growth_history: Array<{ type: string; level?: number; timestamp: string }>;
}

interface Decision {
  id: string;
  problem: string;
  decision: string;
  framework_used: string;
  confidence: number;
  feedback?: string;
  feedback_score?: number;
  created_at: string;
}

type TabType = 'overview' | 'frameworks' | 'values' | 'decisions';

interface AgentCognitionPanelProps {
  agentId: string;
  agentName?: string;
}

const AgentCognitionPanel: React.FC<AgentCognitionPanelProps> = ({ agentId, agentName }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isLoading, setIsLoading] = useState(true);
  const [cognition, setCognition] = useState<CognitionState | null>(null);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [values, setValues] = useState<Value[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [selectedFramework, setSelectedFramework] = useState<Framework | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [cognitionRes, frameworksRes, valuesRes, decisionsRes] = await Promise.all([
        api.get(`/cognition/agent/${agentId}`),
        api.get('/cognition/frameworks'),
        api.get('/cognition/values'),
        api.get(`/cognition/agent/${agentId}/decisions?limit=20`),
      ]);

      setCognition(cognitionRes.data);
      setFrameworks(frameworksRes.data.frameworks || []);
      setValues(valuesRes.data.values || []);
      setDecisions(decisionsRes.data.decisions || []);
    } catch (error) {
      console.error('Failed to load cognition data:', error);
    } finally {
      setIsLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const getValueTypeColor = (type: string) => {
    switch (type) {
      case 'core_value': return 'bg-purple-100 text-purple-700';
      case 'judgment_standard': return 'bg-blue-100 text-blue-700';
      case 'priority': return 'bg-green-100 text-green-700';
      case 'bottom_line': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getValueTypeLabel = (type: string) => {
    switch (type) {
      case 'core_value': return '核心价值观';
      case 'judgment_standard': return '判断标准';
      case 'priority': return '优先级';
      case 'bottom_line': return '底线';
      default: return type;
    }
  };

  const renderOverview = () => {
    const radarData = cognition?.cognitive_bias?.time_preference
      ? [
          { subject: '过去', value: (cognition.cognitive_bias.time_preference.past || 0.2) * 100 },
          { subject: '现在', value: (cognition.cognitive_bias.time_preference.present || 0.3) * 100 },
          { subject: '未来', value: (cognition.cognitive_bias.time_preference.future || 0.5) * 100 },
        ]
      : [];

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <StarIcon className="w-5 h-5 text-yellow-500" />
              <span className="text-gray-500">等级</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">Lv.{cognition?.level || 1}</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <ChartBarIcon className="w-5 h-5 text-blue-500" />
              <span className="text-gray-500">经验值</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{cognition?.experience_points || 0}</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <BeakerIcon className="w-5 h-5 text-purple-500" />
              <span className="text-gray-500">框架掌握</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{cognition?.frameworks?.length || 0}</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircleIcon className="w-5 h-5 text-green-500" />
              <span className="text-gray-500">决策质量</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {Math.round((cognition?.decision_quality || 0.5) * 100)}%
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">认知偏好雷达图</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} />
                  <Radar
                    name="时间偏好"
                    dataKey="value"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">认知属性</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-500">风险偏好</span>
                <span className="font-medium">
                  {cognition?.cognitive_bias?.risk_preference === 'conservative' ? '保守型' :
                   cognition?.cognitive_bias?.risk_preference === 'aggressive' ? '进取型' : '稳健型'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-500">细节偏好</span>
                <span className="font-medium">
                  {cognition?.cognitive_bias?.detail_preference === 'macro_first' ? '宏观优先' :
                   cognition?.cognitive_bias?.detail_preference === 'micro_first' ? '微观优先' : '平衡型'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-500">决策风格</span>
                <span className="font-medium">
                  {cognition?.cognitive_bias?.decision_style || '理性决策'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderFrameworks = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">思维框架库</h3>
      
      {frameworks.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <BeakerIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>暂无思维框架</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {frameworks.map((fw) => (
            <div
              key={fw.id}
              onClick={() => setSelectedFramework(fw)}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-medium text-gray-900">{fw.name}</h4>
                <div className="flex items-center gap-1">
                  <ChartBarIcon className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-green-600">{Math.round(fw.success_rate * 100)}%</span>
                </div>
              </div>
              <p className="text-sm text-gray-500 mb-3">{fw.description}</p>
              <div className="flex flex-wrap gap-1">
                {fw.applicable_scenarios.slice(0, 3).map((scenario, idx) => (
                  <span key={idx} className="px-2 py-1 bg-blue-50 text-blue-600 text-xs rounded-full">
                    {scenario}
                  </span>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs text-gray-400">
                <ClockIcon className="w-3 h-3" />
                使用次数: {fw.usage_count}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderValues = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">价值体系</h3>
      
      {values.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <ScaleIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>暂无价值主张</p>
        </div>
      ) : (
        <div className="space-y-3">
          {values.map((v) => (
            <div key={v.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-gray-900">{v.name}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${getValueTypeColor(v.type)}`}>
                    {getValueTypeLabel(v.type)}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <StarIcon className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium">{Math.round(v.weight * 100)}%</span>
                </div>
              </div>
              <p className="text-sm text-gray-700 font-medium mb-1">"{v.statement}"</p>
              <p className="text-sm text-gray-500">{v.explanation}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderDecisions = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">决策历史</h3>
      
      {decisions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <BrainIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>暂无决策记录</p>
        </div>
      ) : (
        <div className="space-y-3">
          {decisions.map((d) => (
            <div key={d.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-medium text-gray-900">{d.problem}</p>
                  <p className="text-sm text-gray-500">决策: {d.decision}</p>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    d.confidence >= 0.7 ? 'bg-green-100 text-green-700' :
                    d.confidence >= 0.4 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    置信度 {Math.round(d.confidence * 100)}%
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>框架: {d.framework_used}</span>
                <span>{new Date(d.created_at).toLocaleString('zh-CN')}</span>
              </div>
              {d.feedback && (
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <p className="text-xs text-gray-500">反馈: {d.feedback}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <ArrowPathIcon className="w-6 h-6 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-gray-50 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BrainIcon className="w-6 h-6 text-purple-600" />
          <h2 className="text-lg font-semibold text-gray-900">
            认知面板 - {agentName || agentId}
          </h2>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-1 px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          <ArrowPathIcon className="w-4 h-4" />
          刷新
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-4">
        <div className="flex border-b border-gray-200">
          {[
            { key: 'overview', label: '概览', icon: <ChartBarIcon className="w-4 h-4" /> },
            { key: 'frameworks', label: '思维框架', icon: <BeakerIcon className="w-4 h-4" /> },
            { key: 'values', label: '价值体系', icon: <ScaleIcon className="w-4 h-4" /> },
            { key: 'decisions', label: '决策历史', icon: <BrainIcon className="w-4 h-4" /> },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as TabType)}
              className={`flex items-center gap-1 px-4 py-3 text-sm font-medium ${
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
          transition={{ duration: 0.2 }}
        >
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'frameworks' && renderFrameworks()}
          {activeTab === 'values' && renderValues()}
          {activeTab === 'decisions' && renderDecisions()}
        </motion.div>
      </AnimatePresence>

      <AnimatePresence>
        {selectedFramework && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setSelectedFramework(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold text-gray-900 mb-2">{selectedFramework.name}</h3>
              <p className="text-gray-600 mb-4">{selectedFramework.description}</p>
              
              <h4 className="font-medium text-gray-900 mb-2">思考步骤</h4>
              <div className="space-y-2 mb-4">
                {selectedFramework.steps.map((step, idx) => (
                  <div key={idx} className="flex items-start gap-2 p-2 bg-gray-50 rounded">
                    <span className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center">
                      {step.order}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900">{step.name}</p>
                      <p className="text-sm text-gray-500">{step.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              
              <button
                onClick={() => setSelectedFramework(null)}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                关闭
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AgentCognitionPanel;
