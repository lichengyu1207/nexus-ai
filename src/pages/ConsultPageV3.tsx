import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  PlusIcon,
  DocumentTextIcon,
  UserCircleIcon,
  SparklesIcon,
  LightBulbIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import api from '@/services/api';
import toast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';
import CharacterAvatar from '@/components/CharacterAvatar';
import Dudu from '@/components/Dudu';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
  persona?: string;
  emotion?: string;
}

interface Session {
  id: string;
  persona: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

interface PersonaInfo {
  persona: string;
  name: string;
  title: string;
  style: string;
  color_primary: string;
  color_secondary: string;
}

interface ThinkingGene {
  decision_speed: number;
  risk_preference: number;
  expression_style: number;
  inquiry_depth: number;
  report_style: number;
  emotional_resonance: number;
  logic_rigor: number;
  knowledge_preference: number;
}

interface DetectedIssue {
  type: 'info_missing' | 'logic_conflict' | 'implicit_need' | 'emotion_abnormal';
  description: string;
  suggestion: string;
}

const DEFAULT_GENES: Record<'zhouyu' | 'luxun', ThinkingGene> = {
  zhouyu: {
    decision_speed: 85,
    risk_preference: 80,
    expression_style: 85,
    inquiry_depth: 60,
    report_style: 70,
    emotional_resonance: 65,
    logic_rigor: 75,
    knowledge_preference: 80,
  },
  luxun: {
    decision_speed: 40,
    risk_preference: 30,
    expression_style: 35,
    inquiry_depth: 80,
    report_style: 50,
    emotional_resonance: 85,
    logic_rigor: 90,
    knowledge_preference: 60,
  },
};

const GENE_LABELS: Record<keyof ThinkingGene, string> = {
  decision_speed: '决策速度',
  risk_preference: '风险偏好',
  expression_style: '表达风格',
  inquiry_depth: '追问深度',
  report_style: '报告风格',
  emotional_resonance: '情感共鸣',
  logic_rigor: '逻辑严谨',
  knowledge_preference: '知识调用',
};

const ConsultPageV3: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [personaInfo, setPersonaInfo] = useState<PersonaInfo | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<'zhouyu' | 'luxun'>('zhouyu');
  const [thinkingGene, setThinkingGene] = useState<ThinkingGene>(DEFAULT_GENES.zhouyu);
  const [showGenePanel, setShowGenePanel] = useState(false);
  const [detectedIssues, setDetectedIssues] = useState<DetectedIssue[]>([]);
  const [consultationPath, setConsultationPath] = useState<string[]>(['问题分析', '信息收集', '方案生成', '报告优化']);
  const [currentPathIndex, setCurrentPathIndex] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/consult/sessions');
      setSessions(response.data.sessions || []);
    } catch {
      toast.error('加载会话列表失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    setThinkingGene(DEFAULT_GENES[selectedPersona]);
  }, [selectedPersona]);

  const loadSessionHistory = async (sessionId: string) => {
    try {
      const response = await api.get(`/consult/history/${sessionId}`);
      setMessages(response.data || []);
      setCurrentSessionId(sessionId);
    } catch {
      toast.error('加载会话历史失败');
    }
  };

  const startNewSession = async () => {
    try {
      const response = await api.post('/consult/start');
      const data = response.data;
      setCurrentSessionId(data.session_id);
      setPersonaInfo({
        persona: data.persona,
        name: data.persona_info?.name || data.persona,
        title: data.persona_info?.title || '',
        style: data.persona_info?.style || '',
        color_primary: data.persona_info?.color_primary || '#1E3A5F',
        color_secondary: data.persona_info?.color_secondary || '#D4AF37',
      });
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: data.welcome_message,
        created_at: new Date().toISOString(),
        persona: data.persona,
      }]);
      setCurrentPathIndex(0);
      setDetectedIssues([]);
    } catch (error) {
      console.error('开始咨询失败:', error);
      toast.error('开始咨询失败');
    }
  };

  const detectIssues = (input: string): DetectedIssue[] => {
    const issues: DetectedIssue[] = [];
    
    if (input.length < 10) {
      issues.push({
        type: 'info_missing',
        description: '问题描述过于简短',
        suggestion: '请详细描述您的问题，例如：预算范围、目标城市、购房目的等',
      });
    }
    
    const budgetMatch = input.match(/(\d+)万|预算/);
    if (budgetMatch) {
      const budget = parseInt(budgetMatch[1]);
      if (budget < 50) {
        issues.push({
          type: 'logic_conflict',
          description: `预算${budget}万可能偏低`,
          suggestion: '当前预算可能难以在目标城市购买理想房源，是否考虑调整预算或选择其他城市？',
        });
      }
    }
    
    const emotionKeywords = ['焦虑', '担心', '着急', '紧张', '害怕'];
    const hasEmotion = emotionKeywords.some(k => input.includes(k));
    if (hasEmotion) {
      issues.push({
        type: 'emotion_abnormal',
        description: '检测到情绪波动',
        suggestion: '我注意到您可能有些担忧，需要先聊聊您的感受吗？',
      });
    }
    
    return issues;
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isSending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      created_at: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsSending(true);
    
    const issues = detectIssues(inputValue);
    setDetectedIssues(issues);

    try {
    const response = await api.post('/consult/message', {
      session_id: currentSessionId,
      message: userMessage.content,
    });
    const data = response.data;
    
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'assistant',
      content: data.reply,
      persona: data.persona,
      emotion: data.emotion,
      created_at: new Date().toISOString(),
    }]);
    
    if (currentPathIndex < consultationPath.length - 1) {
      setCurrentPathIndex(prev => prev + 1);
    }
    } catch (error) {
      console.error('发送消息失败:', error);
      toast.error('发送消息失败');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!currentSessionId) {
        startNewSession();
      }
      sendMessage();
    }
  };

  const generateReport = async () => {
    toast.success('正在生成咨询报告...');
    try {
      const response = await api.post('/consult/report', {
        session_id: currentSessionId,
      });
      toast.success('报告生成成功！');
      console.log('Report:', response.data);
    } catch {
      toast.error('生成报告失败');
    }
  };

  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'info_missing':
        return <ExclamationTriangleIcon className="w-4 h-4 text-yellow-500" />;
      case 'logic_conflict':
        return <ExclamationTriangleIcon className="w-4 h-4 text-orange-500" />;
      case 'implicit_need':
        return <LightBulbIcon className="w-4 h-4 text-blue-500" />;
      case 'emotion_abnormal':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />;
      default:
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
    }
  };

  const getIssueLabel = (type: string) => {
    switch (type) {
      case 'info_missing':
        return '信息缺失';
      case 'logic_conflict':
        return '逻辑冲突';
      case 'implicit_need':
        return '隐性需求';
      case 'emotion_abnormal':
        return '情绪异常';
      default:
        return '其他';
    }
  };

  const renderGeneBar = (value: number, max: number = 100) => {
    const percentage = (value / max) * 100;
    const color = percentage > 70 ? 'bg-primary-500' : percentage > 40 ? 'bg-blue-500' : 'bg-gray-300';
    return (
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    );
  };

  return (
    <div className="h-full flex bg-gray-50 dark:bg-gray-900">
      <div className="w-80 lg:w-96 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <SparklesIcon className="w-5 h-5 text-primary-500" />
            智能咨询 V3
          </h2>
          
          <div className="mt-3">
            <p className="text-xs text-gray-500 mb-2">选择人格</p>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedPersona('zhouyu')}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-color ${
                  selectedPersona === 'zhouyu'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                周瑜
              </button>
              <button
                onClick={() => setSelectedPersona('luxun')}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-color ${
                  selectedPersona === 'luxun'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                陆逊
              </button>
            </div>
          </div>

          <div className="mt-4">
            <button
              onClick={() => setShowGenePanel(!showGenePanel)}
              className="flex items-center justify-between w-full p-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
            >
              <span className="flex items-center gap-1">
                <CogIcon className="w-4 h-4" />
                思维基因
              </span>
              <span className="text-xs text-gray-400">
                {showGenePanel ? '收起' : '展开'}
              </span>
            </button>
            
            <AnimatePresence>
              {showGenePanel && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-2 space-y-2 overflow-hidden"
                >
                  {(Object.keys(GENE_LABELS) as (keyof ThinkingGene)[]).map((key) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-xs text-gray-500 dark:text-gray-400 w-20">
                        {GENE_LABELS[key]}
                      </span>
                      <div className="flex-1 mx-2">
                        {renderGeneBar(thinkingGene[key])}
                      </div>
                      <span className="text-xs text-gray-400 w-8 text-right">
                        {thinkingGene[key]}
                      </span>
                    </div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-2">咨询路径</p>
            <div className="space-y-1">
              {consultationPath.map((step, index) => (
                <div
                  key={step}
                  className={`flex items-center gap-2 text-xs ${
                    index < currentPathIndex
                      ? 'text-green-600 dark:text-green-400'
                      : index === currentPathIndex
                      ? 'text-primary-600 dark:text-primary-400 font-medium'
                      : 'text-gray-400 dark:text-gray-500'
                  }`}
                >
                  {index < currentPathIndex ? (
                    <CheckCircleIcon className="w-4 h-4" />
                  ) : index === currentPathIndex ? (
                    <div className="w-4 h-4 rounded-full border-2 border-primary-500" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-gray-300" />
                  )}
                  {step}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 flex-1">
            <p className="text-xs text-gray-500 mb-2">历史会话</p>
            <div className="space-y-2 overflow-y-auto max-h-40">
              {isLoading ? (
                <div className="text-center py-2 text-gray-400 text-xs">加载中...</div>
              ) : sessions.length === 0 ? (
                <div className="text-center py-2 text-gray-400 text-xs">暂无历史</div>
              ) : (
                sessions.slice(0, 5).map((session) => (
                  <button
                    key={session.id}
                    onClick={() => loadSessionHistory(session.id)}
                    className={`w-full p-2 text-left rounded-lg text-xs hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${
                      currentSessionId === session.id
                        ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800'
                        : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-700 dark:text-gray-300 truncate">
                        {session.persona === 'zhouyu' ? '周瑜' : '陆逊'}
                      </span>
                      <span className="text-gray-400 text-xs">
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          <div className="mt-4">
            <button
              onClick={startNewSession}
              className="w-full flex items-center justify-center gap-2 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
            >
              <PlusIcon className="w-4 h-4" />
              新对话
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          {!currentSessionId ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <CharacterAvatar persona={selectedPersona} size="xl" emotion="neutral" />
              <h3 className="mt-4 text-xl font-bold text-gray-900 dark:text-white">
                {selectedPersona === 'zhouyu' ? '周瑜都督' : '陆逊都督'}
              </h3>
              <p className="mt-2 text-gray-500 dark:text-gray-400 max-w-md">
                {selectedPersona === 'zhouyu'
                  ? '豪迈智谋，善于快速决策，助您破局制胜'
                  : '沉稳隐忍，善于深度分析，助您稳中求胜'}
              </p>
              <div className="mt-6 grid grid-cols-2 gap-3 max-w-lg">
                {['深圳买房建议', '房产投资分析', '政策解读', '市场趋势'].map((example) => (
                  <button
                    key={example}
                    onClick={() => {
                      setInputValue(example);
                      startNewSession();
                    }}
                    className="p-3 bg-white dark:bg-gray-800 rounded-lg text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl p-4 ${
                      message.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-white dark:bg-gray-800 shadow-md'
                    }`}
                  >
                    <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none">
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </motion.div>
              ))}
              
              {isSending && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-md">
                    <div className="flex items-center gap-2 text-gray-500">
                      <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      <span className="text-sm ml-2">
                        {selectedPersona === 'zhouyu' ? '瑜正在思考...' : '逊正在推演...'}
                      </span>
                    </div>
                  </div>
                </motion.div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}

          {detectedIssues.length > 0 && currentSessionId && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              className="bg-yellow-50 dark:bg-yellow-900/20 border-t border-yellow-200 dark:border-yellow-800 p-3"
            >
              <div className="flex items-start gap-2">
                <LightBulbIcon className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                    系统发现以下问题需要关注:
                  </p>
                  <div className="mt-2 space-y-1">
                    {detectedIssues.map((issue, index) => (
                      <div key={index} className="flex items-start gap-2 text-sm">
                        {getIssueIcon(issue.type)}
                        <div>
                          <span className="font-medium text-gray-700 dark:text-gray-300">
                            [{getIssueLabel(issue.type)}]
                          </span>
                          <span className="text-gray-600 dark:text-gray-400 ml-1">
                            {issue.description}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          {currentSessionId && messages.length > 0 && (
            <div className="mb-2 flex justify-end">
              <button
                onClick={generateReport}
                className="flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700"
              >
                <DocumentTextIcon className="w-4 h-4" />
                生成咨询报告
              </button>
            </div>
          )}

          <div className="flex gap-2">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入您的问题..."
              rows={1}
              className="flex-1 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={isSending}
            />
            <button
              onClick={() => {
                if (!currentSessionId) {
                  startNewSession();
                }
                sendMessage();
              }}
              disabled={!inputValue.trim() || isSending}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <Dudu
        action={isSending ? 'think' : 'wave'}
        position="bottom-left"
        size="sm"
        message={isSending ? '都督正在推演中...' : '有疑问随时问我哦~'}
      />
    </div>
  );
};

export default ConsultPageV3;
