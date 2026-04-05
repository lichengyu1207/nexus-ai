import React, { useState, useEffect, useCallback } from 'react';

interface Message {
  id: string;
  sender: 'user' | 'agent';
  content: string;
  timestamp: Date;
  agentName?: string;
}

interface AgentStatus {
  id: string;
  name: string;
  nameCn: string;
  status: 'idle' | 'working' | 'completed';
  description: string;
}

interface DemoExperienceProps {
  isOpen: boolean;
  onClose: () => void;
}

const AGENTS: AgentStatus[] = [
  { id: 'zhongshu', name: 'Zhongshu', nameCn: '中书省', status: 'idle', description: '决策中枢' },
  { id: 'menshang', name: 'Menshang', nameCn: '门下省', status: 'idle', description: '审核监督' },
  { id: 'gongbu', name: 'Gongbu', nameCn: '工部', status: 'idle', description: '估值分析' },
  { id: 'libu', name: 'Libu', nameCn: '礼部', status: 'idle', description: '对话服务' },
  { id: 'bingbu', name: 'Bingbu', nameCn: '兵部', status: 'idle', description: '数据采集' },
  { id: 'xingbu', name: 'Xingbu', nameCn: '刑部', status: 'idle', description: '风险控制' },
];

const DEMO_SCENARIO = {
  userQuery: '我想在深圳南山区买一套100平米左右的学区房，预算1000万，帮我分析一下。',
  steps: [
    {
      agent: 'zhongshu',
      message: '周瑜：收到您的需求。让我来分析一下——深圳南山区，学区房，100平米，预算1000万。这是一个典型的学区房置业决策，我将协调各部为您进行全面分析。',
      delay: 1500,
    },
    {
      agent: 'bingbu',
      message: '【兵部】正在采集南山区学区房数据...\n✓ 已获取南山区12个学区信息\n✓ 已采集近3个月成交数据\n✓ 已获取学区划分及对口学校信息',
      delay: 2000,
    },
    {
      agent: 'gongbu',
      message: '【工部】正在进行估值分析...\n\n📊 南山区学区房市场分析：\n• 均价区间：9-15万/㎡\n• 100㎡预算匹配度：中等\n• 推荐学区：南二外、南山实验、育才\n\n💰 估值结果：\n• 南二外学区：约1100-1300万\n• 南山实验学区：约950-1150万\n• 育才学区：约850-1000万',
      delay: 3000,
    },
    {
      agent: 'xingbu',
      message: '【刑部】风险评估报告：\n\n⚠️ 注意事项：\n• 深圳限购政策：需深圳户口或连续5年社保\n• 学区政策变动风险：中等\n• 价格波动风险：需关注政策调控\n\n✅ 风险等级：可控',
      delay: 2000,
    },
    {
      agent: 'menshang',
      message: '【门下省】审核通过\n\n经核查，以上分析数据来源可靠，估值方法科学，风险提示充分。建议重点关注南山实验学区的房源，性价比较高。',
      delay: 1500,
    },
    {
      agent: 'libu',
      message: '周瑜：综合各部分析，我为您整理了以下建议：\n\n🏠 推荐方案：\n1. 首选南山实验学区，预算匹配度高\n2. 关注育才学区作为备选\n3. 建议实地考察3-5套房源后再做决定\n\n📋 下一步行动：\n• 准备购房资格证明\n• 关注近期新上房源\n• 联系中介实地看房\n\n如需更详细的分析报告，我可以为您生成专属报告。',
      delay: 2500,
    },
  ],
};

const REPORT_DATA = {
  title: '深圳南山区学区房分析报告',
  summary: '基于您的需求和预算，我们为您分析了南山区的学区房市场',
  recommendations: [
    { area: '南山实验学区', price: '9.5-11.5万/㎡', match: 95, reason: '预算匹配度高，学区优质' },
    { area: '育才学区', price: '8.5-10万/㎡', match: 90, reason: '性价比高，学区稳定' },
    { area: '南二外学区', price: '11-13万/㎡', match: 75, reason: '顶级学区，略超预算' },
  ],
  priceTrend: [
    { month: '7月', price: 10.2 },
    { month: '8月', price: 10.5 },
    { month: '9月', price: 10.3 },
    { month: '10月', price: 10.8 },
    { month: '11月', price: 10.6 },
    { month: '12月', price: 10.9 },
  ],
  risks: ['限购政策', '学区划分变动', '价格波动'],
};

const DemoExperience: React.FC<DemoExperienceProps> = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>(AGENTS);
  const [currentStep, setCurrentStep] = useState(-1);
  const [isTyping, setIsTyping] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  const updateAgentStatus = useCallback((agentId: string, status: AgentStatus['status']) => {
    setAgentStatuses(prev =>
      prev.map(agent =>
        agent.id === agentId ? { ...agent, status } : agent
      )
    );
  }, []);

  const addMessage = useCallback((sender: Message['sender'], content: string, agentName?: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      sender,
      content,
      timestamp: new Date(),
      agentName,
    };
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const typewriterEffect = useCallback(async (text: string, callback: () => void) => {
    setIsTyping(true);
    await new Promise(resolve => setTimeout(resolve, text.length * 10));
    setIsTyping(false);
    callback();
  }, []);

  const runDemo = useCallback(async () => {
    if (isPaused) return;

    setMessages([]);
    setAgentStatuses(AGENTS);
    setShowReport(false);
    setIsComplete(false);
    setCurrentStep(-1);

    await new Promise(resolve => setTimeout(resolve, 500));

    addMessage('user', DEMO_SCENARIO.userQuery);

    await new Promise(resolve => setTimeout(resolve, 800));

    for (let i = 0; i < DEMO_SCENARIO.steps.length; i++) {
      if (isPaused) break;

      const step = DEMO_SCENARIO.steps[i];
      setCurrentStep(i);

      updateAgentStatus(step.agent, 'working');

      await new Promise(resolve => setTimeout(resolve, step.delay));

      const agent = AGENTS.find(a => a.id === step.agent);
      addMessage('agent', step.message, agent?.nameCn);

      updateAgentStatus(step.agent, 'completed');

      await new Promise(resolve => setTimeout(resolve, 500));
    }

    if (!isPaused) {
      setIsComplete(true);
      await new Promise(resolve => setTimeout(resolve, 1000));
      setShowReport(true);
    }
  }, [isPaused, addMessage, updateAgentStatus]);

  useEffect(() => {
    if (isOpen && !isPaused) {
      runDemo();
    }
  }, [isOpen]);

  const handlePause = () => {
    setIsPaused(true);
  };

  const handleResume = () => {
    setIsPaused(false);
    if (!isComplete) {
      runDemo();
    }
  };

  const handleRestart = () => {
    setIsPaused(false);
    runDemo();
  };

  const handleSkip = () => {
    setIsComplete(true);
    setShowReport(true);
    setAgentStatuses(prev => prev.map(a => ({ ...a, status: 'completed' })));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="relative w-full max-w-6xl h-[90vh] bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl shadow-2xl overflow-hidden border border-slate-700">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center">
              <span className="text-xl">🏠</span>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">住房决策一键体验</h2>
              <p className="text-sm text-slate-400">体验周瑜如何帮您分析房产</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isPaused ? (
              <button
                onClick={handleResume}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                继续
              </button>
            ) : (
              <button
                onClick={handlePause}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors"
              >
                暂停
              </button>
            )}
            <button
              onClick={handleRestart}
              className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors"
            >
              重播
            </button>
            <button
              onClick={handleSkip}
              className="px-4 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors"
            >
              跳过
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex h-[calc(90vh-72px)]">
          {/* Chat Area */}
          <div className="flex-1 flex flex-col border-r border-slate-700">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-100'
                    }`}
                  >
                    {msg.agentName && (
                      <div className="text-xs text-amber-400 mb-1 font-medium">{msg.agentName}</div>
                    )}
                    <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-slate-700 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Progress Bar */}
            <div className="px-4 py-3 border-t border-slate-700 bg-slate-800/50">
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400">进度</span>
                <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-500"
                    style={{ width: `${((currentStep + 1) / DEMO_SCENARIO.steps.length) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-slate-400">{currentStep + 1}/{DEMO_SCENARIO.steps.length}</span>
              </div>
            </div>
          </div>

          {/* Agent Visualization */}
          <div className="w-80 p-4 bg-slate-800/30">
            <h3 className="text-sm font-medium text-slate-300 mb-4">六部智能体协同</h3>
            <div className="space-y-3">
              {agentStatuses.map((agent) => (
                <div
                  key={agent.id}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-300 ${
                    agent.status === 'working'
                      ? 'bg-amber-500/20 border border-amber-500/50'
                      : agent.status === 'completed'
                      ? 'bg-green-500/20 border border-green-500/50'
                      : 'bg-slate-700/50 border border-slate-600'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      agent.status === 'working'
                        ? 'bg-amber-500 text-white animate-pulse'
                        : agent.status === 'completed'
                        ? 'bg-green-500 text-white'
                        : 'bg-slate-600 text-slate-300'
                    }`}
                  >
                    {agent.nameCn.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-white">{agent.nameCn}</div>
                    <div className="text-xs text-slate-400">{agent.description}</div>
                  </div>
                  <div className="text-lg">
                    {agent.status === 'working' && '⚡'}
                    {agent.status === 'completed' && '✅'}
                    {agent.status === 'idle' && '○'}
                  </div>
                </div>
              ))}
            </div>

            {/* Report Preview */}
            {showReport && (
              <div className="mt-4 p-4 bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-lg border border-amber-500/30">
                <h4 className="text-sm font-medium text-amber-400 mb-2">📊 分析报告已生成</h4>
                <div className="space-y-2 text-xs text-slate-300">
                  <div>• 推荐学区：南山实验</div>
                  <div>• 预算匹配度：95%</div>
                  <div>• 风险等级：可控</div>
                </div>
                <button className="w-full mt-3 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-medium transition-colors">
                  查看完整报告
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Complete Overlay */}
        {isComplete && showReport && (
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-slate-900 to-transparent">
            <div className="flex items-center justify-center gap-4">
              <p className="text-slate-300">演示完成！如果您有真实需求，欢迎立即咨询。</p>
              <button className="px-6 py-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white rounded-lg font-medium transition-all">
                立即咨询
              </button>
              <button className="px-6 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors">
                注册账号
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DemoExperience;
