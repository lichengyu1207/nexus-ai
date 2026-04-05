import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Agent {
  id: string;
  name: string;
  avatar: string;
  department: string;
  status: 'idle' | 'busy' | 'auto' | 'offline';
  level: number;
  skills: string[];
  recommendationScore: number;
}

interface TaskAssignmentPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (taskType: string, input: string, agentIds: string[]) => void;
}

const taskTypes = [
  { id: 'analysis', label: '房产分析', icon: '🏠', description: '深度分析房产价值、市场趋势' },
  { id: 'consult', label: '智能咨询', icon: '💬', description: '与智能体对话，获取专业建议' },
  { id: 'batch', label: '批量分析', icon: '📊', description: '同时分析多个房产地址' },
  { id: 'compare', label: '房源对比', icon: '⚖️', description: '对比多个房源的优劣势' },
];

const analysisStyles = [
  { id: 'zhouyu', name: '周瑜', icon: '🔥', style: '激进', desc: '火眼金睛，快速发现价值' },
  { id: 'luxun', name: '陆逊', icon: '⚖️', style: '稳健', desc: '稳扎稳打，全面评估' },
  { id: 'zhugeliang', name: '诸葛亮', icon: '🧠', style: '深度', desc: '运筹帷幄，深度分析' },
  { id: 'simayi', name: '司马懿', icon: '📊', style: '数据', desc: '精打细算，数据驱动' },
];

const steps = [
  { id: 1, icon: '📝', title: '输入地址', description: '输入房产信息' },
  { id: 2, icon: '🤖', title: 'AI分析', description: '选择分析风格' },
  { id: 3, icon: '📊', title: '生成报告', description: '选择智能体' },
  { id: 4, icon: '💡', title: '决策参考', description: '确认并开始' },
];

const TaskAssignmentPanel: React.FC<TaskAssignmentPanelProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [taskType, setTaskType] = useState('analysis');
  const [input, setInput] = useState('');
  const [analysisStyle, setAnalysisStyle] = useState('zhugeliang');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoAssign, setAutoAssign] = useState(true);

  useEffect(() => {
    if (isOpen) {
      setCurrentStep(1);
      setInput('');
      setSelectedAgents([]);
      fetchAvailableAgents();
    }
  }, [isOpen, taskType]);

  const fetchAvailableAgents = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:8000/api/dashboard/task-assignment-options?task_type=${taskType}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setAgents(data.options || []);
        if (data.options && data.options.length > 0) {
          const recommended = data.options
            .filter((a: Agent) => a.is_available)
            .slice(0, 3)
            .map((a: Agent) => a.id);
          setSelectedAgents(recommended);
        }
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      setAgents(getMockAgents());
    } finally {
      setLoading(false);
    }
  };

  const getMockAgents = (): Agent[] => [
    { id: '1', name: '需求分析师', avatar: '📊', department: '吏部', status: 'idle', level: 5, skills: ['需求分析', '市场调研'], recommendationScore: 95 },
    { id: '2', name: '数据采集师', avatar: '🔍', department: '兵部', status: 'idle', level: 4, skills: ['数据采集', '爬虫'], recommendationScore: 90 },
    { id: '3', name: '市场分析师', avatar: '📈', department: '户部', status: 'idle', level: 6, skills: ['市场分析', '趋势预测'], recommendationScore: 88 },
    { id: '4', name: '风险评估师', avatar: '⚖️', department: '刑部', status: 'busy', level: 5, skills: ['风险评估', '合规检查'], recommendationScore: 85 },
    { id: '5', name: '报告撰写师', avatar: '📝', department: '礼部', status: 'idle', level: 4, skills: ['报告撰写', '文档生成'], recommendationScore: 82 },
  ];

  const handleAgentToggle = (agentId: string) => {
    setSelectedAgents(prev =>
      prev.includes(agentId)
        ? prev.filter(id => id !== agentId)
        : [...prev, agentId]
    );
    setAutoAssign(false);
  };

  const handleAutoAssign = () => {
    const recommended = agents
      .filter(a => a.status === 'idle')
      .sort((a, b) => b.recommendationScore - a.recommendationScore)
      .slice(0, 3)
      .map(a => a.id);
    setSelectedAgents(recommended);
    setAutoAssign(true);
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return input.trim().length > 0;
      case 2:
        return true;
      case 3:
        return selectedAgents.length > 0;
      case 4:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    } else {
      onSubmit(taskType, input, selectedAgents);
      onClose();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="acrylic rounded-2xl shadow-fluent-xl max-w-2xl w-full max-h-[90vh] overflow-hidden border border-white/30">
        <div className="p-6 border-b border-fluent-deepOcean-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-fluent-deepOcean-500">
              🚀 启动新任务
            </h2>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full hover:bg-fluent-deepOcean-100 flex items-center justify-center text-fluent-deepOcean-400 transition-colors"
            >
              ✕
            </button>
          </div>
          
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className="flex flex-col items-center">
                  <motion.div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all duration-300 ${
                      currentStep === step.id
                        ? 'bg-fluent-gold-500 text-fluent-deepOcean-500 shadow-gold-glow'
                        : currentStep > step.id
                        ? 'bg-fluent-jade-500 text-white'
                        : 'bg-fluent-deepOcean-100 text-fluent-deepOcean-300'
                    }`}
                    animate={currentStep === step.id ? { scale: [1, 1.1, 1] } : {}}
                    transition={{ duration: 0.5 }}
                  >
                    {currentStep > step.id ? '✓' : step.icon}
                  </motion.div>
                  <p className={`text-xs mt-1 ${
                    currentStep === step.id
                      ? 'text-fluent-gold-600 font-medium'
                      : 'text-fluent-deepOcean-300'
                  }`}>
                    {step.title}
                  </p>
                </div>
                {index < steps.length - 1 && (
                  <div className="flex-1 h-1 mx-2 rounded-full bg-fluent-deepOcean-100 overflow-hidden">
                    <motion.div
                      className="h-full bg-fluent-gold-500"
                      initial={{ width: '0%' }}
                      animate={{ width: currentStep > step.id ? '100%' : '0%' }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          <AnimatePresence mode="wait">
            {currentStep === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="mb-6">
                  <label className="block text-sm font-medium text-fluent-deepOcean-500 mb-3">
                    📝 第一步：输入房产信息
                  </label>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {taskTypes.map(type => (
                      <button
                        key={type.id}
                        onClick={() => setTaskType(type.id)}
                        className={`p-3 rounded-xl border-2 text-left transition-all duration-300 ${
                          taskType === type.id
                            ? 'border-fluent-gold-500 bg-fluent-gold-50'
                            : 'border-fluent-deepOcean-200 hover:border-fluent-gold-300'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{type.icon}</span>
                          <div>
                            <p className="font-medium text-fluent-deepOcean-500">{type.label}</p>
                            <p className="text-xs text-fluent-deepOcean-300">{type.description}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                  <textarea
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    placeholder={
                      taskType === 'analysis'
                        ? '请输入房产地址，如：深圳市南山区科技园1000万学区房'
                        : taskType === 'consult'
                        ? '请输入您想咨询的问题...'
                        : taskType === 'batch'
                        ? '请输入多个房产地址，每行一个...'
                        : '请输入对比内容...'
                    }
                    className="w-full border-2 border-fluent-deepOcean-200 rounded-xl px-4 py-3 h-32 focus:outline-none focus:border-fluent-gold-400 focus:ring-2 focus:ring-fluent-gold-400/20 bg-white/50"
                  />
                </div>
              </motion.div>
            )}

            {currentStep === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="mb-6">
                  <label className="block text-sm font-medium text-fluent-deepOcean-500 mb-3">
                    🤖 第二步：选择分析风格
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {analysisStyles.map(style => (
                      <button
                        key={style.id}
                        onClick={() => setAnalysisStyle(style.id)}
                        className={`p-4 rounded-xl border-2 text-left transition-all duration-300 ${
                          analysisStyle === style.id
                            ? 'border-fluent-gold-500 bg-fluent-gold-50'
                            : 'border-fluent-deepOcean-200 hover:border-fluent-gold-300'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-3xl">{style.icon}</span>
                          <div>
                            <p className="font-medium text-fluent-deepOcean-500">
                              {style.name}
                              <span className="ml-2 text-xs px-2 py-0.5 rounded bg-fluent-gold-100 text-fluent-gold-700">
                                {style.style}
                              </span>
                            </p>
                            <p className="text-xs text-fluent-deepOcean-300 mt-1">{style.desc}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {currentStep === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-sm font-medium text-fluent-deepOcean-500">
                      📊 第三步：分配智能体
                    </label>
                    <button
                      onClick={handleAutoAssign}
                      className={`text-sm px-3 py-1 rounded-lg transition-colors ${
                        autoAssign
                          ? 'bg-fluent-gold-100 text-fluent-gold-700'
                          : 'bg-fluent-deepOcean-100 text-fluent-deepOcean-500 hover:bg-fluent-deepOcean-200'
                      }`}
                    >
                      🤖 自动推荐
                    </button>
                  </div>
                  <div className="space-y-2">
                    {loading ? (
                      <div className="text-center py-4 text-fluent-deepOcean-300">
                        加载中...
                      </div>
                    ) : (
                      agents.map(agent => (
                        <div
                          key={agent.id}
                          onClick={() => handleAgentToggle(agent.id)}
                          className={`p-3 rounded-xl border-2 cursor-pointer transition-all duration-300 ${
                            selectedAgents.includes(agent.id)
                              ? 'border-fluent-gold-500 bg-fluent-gold-50'
                              : 'border-fluent-deepOcean-100 hover:border-fluent-deepOcean-200'
                          } ${agent.status !== 'idle' ? 'opacity-50' : ''}`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-fluent-deepOcean-400 to-fluent-deepOcean-600 flex items-center justify-center text-xl">
                                {agent.avatar}
                              </div>
                              <div>
                                <p className="font-medium text-fluent-deepOcean-500">
                                  {agent.name}
                                  <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-fluent-gold-100 text-fluent-gold-700">
                                    Lv.{agent.level}
                                  </span>
                                </p>
                                <p className="text-xs text-fluent-deepOcean-300">
                                  {agent.department} · {agent.skills.join(' · ')}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {agent.status !== 'idle' && (
                                <span className="text-xs text-fluent-deepOcean-300">
                                  {agent.status === 'busy' ? '忙碌中' : '离线'}
                                </span>
                              )}
                              <div className="flex items-center gap-1">
                                <span className="text-xs text-fluent-gold-500">推荐</span>
                                <span className="text-sm font-semibold text-fluent-gold-600">
                                  {agent.recommendationScore}%
                                </span>
                              </div>
                              <div
                                className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                                  selectedAgents.includes(agent.id)
                                    ? 'border-fluent-gold-500 bg-fluent-gold-500'
                                    : 'border-fluent-deepOcean-300'
                                }`}
                              >
                                {selectedAgents.includes(agent.id) && (
                                  <span className="text-white text-xs">✓</span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {currentStep === 4 && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="mb-6">
                  <label className="block text-sm font-medium text-fluent-deepOcean-500 mb-3">
                    💡 第四步：确认任务信息
                  </label>
                  <div className="bg-fluent-deepOcean-50 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between py-2 border-b border-fluent-deepOcean-100">
                      <span className="text-fluent-deepOcean-400">任务类型</span>
                      <span className="font-medium text-fluent-deepOcean-500">
                        {taskTypes.find(t => t.id === taskType)?.icon} {taskTypes.find(t => t.id === taskType)?.label}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-fluent-deepOcean-100">
                      <span className="text-fluent-deepOcean-400">分析风格</span>
                      <span className="font-medium text-fluent-deepOcean-500">
                        {analysisStyles.find(s => s.id === analysisStyle)?.icon} {analysisStyles.find(s => s.id === analysisStyle)?.name}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-fluent-deepOcean-100">
                      <span className="text-fluent-deepOcean-400">分配智能体</span>
                      <span className="font-medium text-fluent-deepOcean-500">
                        {selectedAgents.length} 个
                      </span>
                    </div>
                    <div className="py-2">
                      <span className="text-fluent-deepOcean-400">任务内容</span>
                      <p className="mt-1 text-fluent-deepOcean-500 bg-white rounded-lg p-2 text-sm">
                        {input}
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-4 p-4 bg-fluent-gold-50 rounded-xl border border-fluent-gold-200">
                    <div className="flex items-center gap-2 text-fluent-gold-700">
                      <span className="text-xl">💡</span>
                      <span className="font-medium">预计消耗: 50 积分</span>
                    </div>
                    <p className="text-sm text-fluent-gold-600 mt-1">
                      任务完成后将生成详细的分析报告，为您的决策提供专业参考
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="p-6 border-t border-fluent-deepOcean-100 bg-fluent-deepOcean-50/50">
          <div className="flex items-center justify-between">
            <p className="text-sm text-fluent-deepOcean-300">
              步骤 {currentStep} / 4
            </p>
            <div className="flex gap-3">
              {currentStep > 1 && (
                <button
                  onClick={handleBack}
                  className="px-4 py-2 rounded-xl border-2 border-fluent-deepOcean-200 text-fluent-deepOcean-500 hover:bg-fluent-deepOcean-100 transition-colors"
                >
                  上一步
                </button>
              )}
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className={`px-6 py-2 rounded-xl font-medium transition-all duration-300 ${
                  canProceed()
                    ? 'bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 hover:shadow-gold-glow'
                    : 'bg-fluent-deepOcean-200 text-fluent-deepOcean-400 cursor-not-allowed'
                }`}
              >
                {currentStep === 4 ? '🚀 开始分析' : '下一步'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskAssignmentPanel;
