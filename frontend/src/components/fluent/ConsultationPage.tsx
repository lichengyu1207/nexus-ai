import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Paperclip, Image, Mic, MoreVertical, User, Bot, Copy, ThumbsUp, ThumbsDown } from 'lucide-react';
import FluentCard from './FluentCard';
import FluentButton from './FluentButton';
import AcrylicContainer from './AcrylicContainer';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  avatar?: string;
  step?: number;
}

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messages: Message[];
}

const sampleConversations: Conversation[] = [
  {
    id: '1',
    title: '深圳房产投资咨询',
    lastMessage: '根据当前市场趋势...',
    timestamp: new Date(Date.now() - 3600000),
    messages: [
      {
        id: '1',
        role: 'assistant',
        content: '您好！我是房都督智能助手，有什么可以帮助您的吗？',
        timestamp: new Date(Date.now() - 7200000),
        avatar: '/agents/zhouyu.png',
      },
    ],
  },
  {
    id: '2',
    title: '广州小区对比分析',
    lastMessage: '珠江新城和天河公园...',
    timestamp: new Date(Date.now() - 86400000),
    messages: [],
  },
];

const analysisStyles = [
  { id: 'zhouyu', name: '周瑜', icon: '🔥', style: '激进', desc: '火眼金睛，快速发现价值' },
  { id: 'luxun', name: '陆逊', icon: '⚖️', style: '稳健', desc: '稳扎稳打，全面评估' },
  { id: 'zhugeliang', name: '诸葛亮', icon: '🧠', style: '深度', desc: '运筹帷幄，深度分析' },
  { id: 'simayi', name: '司马懿', icon: '📊', style: '数据', desc: '精打细算，数据驱动' },
];

const steps = [
  { id: 1, icon: '📝', title: '输入地址', description: '输入您的问题' },
  { id: 2, icon: '🤖', title: 'AI分析', description: '选择分析风格' },
  { id: 3, icon: '📊', title: '生成报告', description: '智能体处理中' },
  { id: 4, icon: '💡', title: '决策参考', description: '获取专业建议' },
];

const ConsultationPage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>(sampleConversations);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedStyle, setSelectedStyle] = useState('zhugeliang');
  const [showStyleSelector, setShowStyleSelector] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    setCurrentStep(2);
    setShowStyleSelector(true);
  };

  const handleStyleSelect = (styleId: string) => {
    setSelectedStyle(styleId);
  };

  const handleConfirmStyle = () => {
    setShowStyleSelector(false);
    setCurrentStep(3);
    processMessage();
  };

  const processMessage = async () => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
      step: 1,
    };

    if (activeConversation) {
      const updatedConversation = {
        ...activeConversation,
        messages: [...activeConversation.messages, userMessage],
        lastMessage: inputValue.slice(0, 30) + '...',
        timestamp: new Date(),
      };
      setActiveConversation(updatedConversation);
      setConversations(
        conversations.map((c) => (c.id === updatedConversation.id ? updatedConversation : c))
      );
    } else {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: inputValue.slice(0, 20) + '...',
        lastMessage: inputValue.slice(0, 30) + '...',
        timestamp: new Date(),
        messages: [userMessage],
      };
      setActiveConversation(newConversation);
      setConversations([newConversation, ...conversations]);
    }

    setInputValue('');
    setIsTyping(true);

    setTimeout(() => {
      const styleInfo = analysisStyles.find(s => s.id === selectedStyle);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateResponse(inputValue, selectedStyle),
        timestamp: new Date(),
        avatar: '/agents/zhouyu.png',
        step: 4,
      };

      if (activeConversation) {
        const updatedConversation = {
          ...activeConversation,
          messages: [...activeConversation.messages, assistantMessage],
          lastMessage: assistantMessage.content.slice(0, 30) + '...',
          timestamp: new Date(),
        };
        setActiveConversation(updatedConversation);
        setConversations(
          conversations.map((c) => (c.id === updatedConversation.id ? updatedConversation : c))
        );
      } else {
        const newConv = conversations[0];
        if (newConv) {
          const updatedConversation = {
            ...newConv,
            messages: [...newConv.messages, assistantMessage],
            lastMessage: assistantMessage.content.slice(0, 30) + '...',
            timestamp: new Date(),
          };
          setActiveConversation(updatedConversation);
          setConversations(
            conversations.map((c) => (c.id === updatedConversation.id ? updatedConversation : c))
          );
        }
      }
      setIsTyping(false);
      setCurrentStep(4);
    }, 2000);
  };

  const generateResponse = (input: string, style: string): string => {
    const styleInfo = analysisStyles.find(s => s.id === style);
    const responses = [
      `【${styleInfo?.name}风格分析】\n\n根据我的分析，深圳南山区的房价目前处于稳定上涨趋势。华润城周边配套完善，交通便利，是不错的投资选择。\n\n📊 数据来源：链家、贝壳、安居客\n📈 置信度：92%`,
      `【${styleInfo?.name}风格分析】\n\n从数据来看，广州珠江新城的均价在9-12万/㎡之间，具体要看楼盘品质和楼层朝向。建议您实地考察后再做决定。\n\n📊 数据来源：中原地产、合富置业\n📈 置信度：88%`,
      `【${styleInfo?.name}风格分析】\n\n关于您提到的学区房问题，我建议关注南山外国语学校周边的小区，这些区域的房产保值性较好。\n\n📊 数据来源：教育局、链家\n📈 置信度：95%`,
      `【${styleInfo?.name}风格分析】\n\n根据最新的市场数据，该区域的租金回报率约为2.5%-3%，对于长期投资来说是比较稳健的选择。\n\n📊 数据来源：58同城、安居客\n📈 置信度：90%`,
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return `${days}天前`;
  };

  const resetToNewConversation = () => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: '新对话',
      lastMessage: '',
      timestamp: new Date(),
      messages: [
        {
          id: '1',
          role: 'assistant',
          content: '您好！我是房都督智能助手，有什么可以帮助您的吗？我可以为您分析房产市场趋势、评估小区价值、提供投资建议等。',
          timestamp: new Date(),
          avatar: '/agents/zhouyu.png',
        },
      ],
    };
    setActiveConversation(newConv);
    setConversations([newConv, ...conversations]);
    setCurrentStep(1);
    setShowStyleSelector(false);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-4">
      <motion.div
        className="w-72 flex-shrink-0"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <FluentCard className="h-full flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-fluent-deepOcean-500">会话历史</h2>
            <FluentButton variant="ghost" size="sm" onClick={resetToNewConversation}>
              新建
            </FluentButton>
          </div>
          <div className="flex-1 overflow-y-auto space-y-2">
            <AnimatePresence>
              {conversations.map((conv) => (
                <motion.div
                  key={conv.id}
                  className={`p-3 rounded-xl cursor-pointer transition-all ${
                    activeConversation?.id === conv.id
                      ? 'bg-fluent-gold-100 border border-fluent-gold-300'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                  onClick={() => {
                    setActiveConversation(conv);
                    setCurrentStep(1);
                    setShowStyleSelector(false);
                  }}
                  whileHover={{ x: 4 }}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <h3 className="font-medium text-sm text-fluent-deepOcean-500 truncate">
                    {conv.title}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1 truncate">{conv.lastMessage}</p>
                  <p className="text-xs text-gray-400 mt-1">{formatTime(conv.timestamp)}</p>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </FluentCard>
      </motion.div>

      <motion.div
        className="flex-1 flex flex-col"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {activeConversation ? (
          <>
            <FluentCard className="mb-4 p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-fluent-deepOcean-500 to-fluent-deepOcean-700 flex items-center justify-center">
                    <span className="text-fluent-gold-400 font-bold">督</span>
                  </div>
                  <div>
                    <h2 className="font-semibold text-fluent-deepOcean-500">
                      {activeConversation.title}
                    </h2>
                    <p className="text-xs text-gray-500">
                      {activeConversation.messages.length} 条消息
                    </p>
                  </div>
                </div>
                <button className="p-2 rounded-lg hover:bg-gray-100">
                  <MoreVertical className="w-5 h-5 text-gray-400" />
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                {steps.map((step, index) => (
                  <React.Fragment key={step.id}>
                    <div className="flex flex-col items-center">
                      <motion.div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all duration-300 ${
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
                      <div className="flex-1 h-0.5 mx-1 rounded-full bg-fluent-deepOcean-100 overflow-hidden">
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
            </FluentCard>

            <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
              <AnimatePresence>
                {activeConversation.messages.map((message) => (
                  <motion.div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.role === 'user' ? 'flex-row-reverse' : ''
                    }`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex-shrink-0">
                        <img
                          src={message.avatar || '/agents/zhouyu.png'}
                          alt="Assistant"
                          className="w-8 h-8 rounded-full border-2 border-fluent-gold-300"
                        />
                      </div>
                    )}
                    <div
                      className={`max-w-[70%] ${
                        message.role === 'user'
                          ? 'bg-fluent-deepOcean-500 text-white rounded-2xl rounded-tr-sm'
                          : 'bg-white border border-gray-100 rounded-2xl rounded-tl-sm'
                      } p-4 shadow-sm`}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-line">{message.content}</p>
                      <div
                        className={`flex items-center gap-2 mt-2 text-xs ${
                          message.role === 'user' ? 'text-white/70' : 'text-gray-400'
                        }`}
                      >
                        <span>{formatTime(message.timestamp)}</span>
                        {message.role === 'assistant' && (
                          <div className="flex gap-1 ml-auto">
                            <button className="p-1 rounded hover:bg-gray-100">
                              <Copy className="w-3 h-3" />
                            </button>
                            <button className="p-1 rounded hover:bg-gray-100">
                              <ThumbsUp className="w-3 h-3" />
                            </button>
                            <button className="p-1 rounded hover:bg-gray-100">
                              <ThumbsDown className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    {message.role === 'user' && (
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-fluent-gold-500 flex items-center justify-center">
                          <User className="w-4 h-4 text-white" />
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>

              {isTyping && (
                <motion.div
                  className="flex gap-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <img
                    src="/agents/zhouyu.png"
                    alt="Assistant"
                    className="w-8 h-8 rounded-full border-2 border-fluent-gold-300"
                  />
                  <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm p-4">
                    <div className="flex gap-1">
                      <motion.div
                        className="w-2 h-2 bg-fluent-gold-500 rounded-full"
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity, delay: 0 }}
                      />
                      <motion.div
                        className="w-2 h-2 bg-fluent-gold-500 rounded-full"
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity, delay: 0.15 }}
                      />
                      <motion.div
                        className="w-2 h-2 bg-fluent-gold-500 rounded-full"
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity, delay: 0.3 }}
                      />
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {showStyleSelector ? (
              <AcrylicContainer blur="lg" opacity={0.9} className="p-4">
                <div className="mb-3">
                  <p className="text-sm font-medium text-fluent-deepOcean-500 mb-2">
                    🤖 第二步：选择分析风格
                  </p>
                  <div className="grid grid-cols-4 gap-2">
                    {analysisStyles.map(style => (
                      <button
                        key={style.id}
                        onClick={() => handleStyleSelect(style.id)}
                        className={`p-2 rounded-xl border-2 text-center transition-all ${
                          selectedStyle === style.id
                            ? 'border-fluent-gold-500 bg-fluent-gold-50'
                            : 'border-fluent-deepOcean-200 hover:border-fluent-gold-300'
                        }`}
                      >
                        <span className="text-xl">{style.icon}</span>
                        <p className="text-xs font-medium mt-1">{style.name}</p>
                        <p className="text-xs text-fluent-deepOcean-300">{style.style}</p>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <FluentButton
                    variant="ghost"
                    onClick={() => {
                      setShowStyleSelector(false);
                      setCurrentStep(1);
                    }}
                  >
                    取消
                  </FluentButton>
                  <FluentButton variant="gold" onClick={handleConfirmStyle}>
                    确认并分析
                  </FluentButton>
                </div>
              </AcrylicContainer>
            ) : (
              <AcrylicContainer blur="lg" opacity={0.9} className="p-4">
                <div className="flex items-end gap-3">
                  <div className="flex gap-2">
                    <button className="p-2 rounded-lg hover:bg-white/50 text-gray-500">
                      <Paperclip className="w-5 h-5" />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-white/50 text-gray-500">
                      <Image className="w-5 h-5" />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-white/50 text-gray-500">
                      <Mic className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="flex-1 relative">
                    <textarea
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="📝 第一步：输入您的问题..."
                      className="w-full px-4 py-3 rounded-xl bg-white/50 border border-white/30 focus:border-fluent-gold-500 focus:ring-2 focus:ring-fluent-gold-500/20 outline-none transition-all resize-none"
                      rows={1}
                    />
                  </div>
                  <FluentButton
                    variant="gold"
                    onClick={handleSend}
                    disabled={!inputValue.trim()}
                  >
                    <Send className="w-5 h-5" />
                  </FluentButton>
                </div>
              </AcrylicContainer>
            )}
          </>
        ) : (
          <FluentCard className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-fluent-deepOcean-500 to-fluent-deepOcean-700 flex items-center justify-center">
                <Bot className="w-10 h-10 text-fluent-gold-400" />
              </div>
              <h2 className="text-xl font-semibold text-fluent-deepOcean-500 mb-2">
                智能咨询服务
              </h2>
              <p className="text-gray-500 mb-6 max-w-md">
                与房都督智能助手对话，获取专业的房产投资建议、市场分析和小区评估服务
              </p>
              
              <div className="flex justify-center gap-2 mb-6">
                {steps.map((step, index) => (
                  <React.Fragment key={step.id}>
                    <div className="flex flex-col items-center">
                      <div className="w-10 h-10 rounded-full bg-fluent-deepOcean-100 flex items-center justify-center text-lg">
                        {step.icon}
                      </div>
                      <p className="text-xs mt-1 text-fluent-deepOcean-300">{step.title}</p>
                    </div>
                    {index < steps.length - 1 && (
                      <div className="w-8 h-0.5 self-center mt-4 bg-fluent-deepOcean-100" />
                    )}
                  </React.Fragment>
                ))}
              </div>
              
              <FluentButton variant="gold" onClick={resetToNewConversation}>
                开始新对话
              </FluentButton>
            </div>
          </FluentCard>
        )}
      </motion.div>
    </div>
  );
};

export default ConsultationPage;
