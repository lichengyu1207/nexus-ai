import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  PlusIcon,
  DocumentTextIcon,
  UserCircleIcon,
  SparklesIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import api from '@/services/api';
import toast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';
import CharacterAvatar from '@/components/CharacterAvatar';
import { motion, AnimatePresence } from 'framer-motion';
import GovernanceFlow from '@/components/workflow/GovernanceFlow';
import DepartmentStatus from '@/components/workflow/DepartmentStatus';
import RealtimeStatus from '@/components/realtime/RealtimeStatus';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
  entities?: Record<string, any>;
  created_at: string;
  persona?: 'zhouyu' | 'luxun';
  emotion?: 'default' | 'thinking' | 'happy' | 'serious' | 'surprised';
}

interface Session {
  id: string;
  persona?: string;
  status?: string;
  created_at: string;
  updated_at?: string;
}

interface PersonaInfo {
  persona: 'zhouyu' | 'luxun';
  name: string;
  title: string;
  style: string;
  color_primary: string;
  color_secondary: string;
}

interface GovernanceTask {
  task_id: string;
  status: 'queued' | 'planning' | 'reviewing' | 'executing' | 'completed' | 'failed';
  progress: number;
  current_province?: 'zhongshu' | 'menxia' | 'shangshu';
  current_department?: string;
  workflow_steps?: any[];
  result?: any;
}

const ConsultPageNew: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [personaInfo, setPersonaInfo] = useState<PersonaInfo | null>(null);
  const [activeTask, setActiveTask] = useState<GovernanceTask | null>(null);
  const [showGovernanceFlow, setShowGovernanceFlow] = useState(false);
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

  const loadSessionHistory = async (sessionId: string) => {
    try {
      const response = await api.get(`/consult/history/${sessionId}`);
      setMessages(response.data || []);
      setCurrentSessionId(sessionId);
    } catch {
      toast.error('加载会话历史失败');
    }
  };

  const startNewSession = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setActiveTask(null);
    setShowGovernanceFlow(false);
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isSending) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: inputValue,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsSending(true);

    try {
      // 检测是否需要启动三省六部制分析
      const needsAnalysis = detectAnalysisNeed(inputValue);
      
      if (needsAnalysis) {
        // 启动三省六部制分析
        const taskResponse = await api.post('/tasks', {
          query: inputValue,
          style: 'balanced',
        });

        if (taskResponse.data.id) {
          setActiveTask({
            task_id: taskResponse.data.id,
            status: 'queued',
            progress: 0,
          });
          setShowGovernanceFlow(true);

          // 添加系统消息
          const systemMessage: Message = {
            id: `system-${Date.now()}`,
            role: 'assistant',
            content: '已启动三省六部制分析系统，正在为您进行专业分析...\n\n**中书省** 正在制定分析方案\n**门下省** 将进行方案审核\n**尚书省** 将协调六部执行分析',
            created_at: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, systemMessage]);
        }
      } else {
        // 普通咨询
        const response = await api.post('/consult', {
          message: inputValue,
          session_id: currentSessionId,
        });

        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.data.reply,
          intent: response.data.intent,
          entities: response.data.entities,
          created_at: new Date().toISOString(),
          persona: 'zhouyu',
        };

        setMessages((prev) => [...prev, assistantMessage]);

        if (response.data.session_id && !currentSessionId) {
          setCurrentSessionId(response.data.session_id);
        }
      }
    } catch (error) {
      toast.error('发送消息失败');
    } finally {
      setIsSending(false);
    }
  };

  const detectAnalysisNeed = (message: string): boolean => {
    const analysisKeywords = [
      '分析', '评估', '推荐', '比较', '学区房', '房价', '投资',
      '预算', '平米', '万', '区域', '地段', '升值', '租金',
      '深圳', '北京', '上海', '广州', '杭州', '南京', '成都',
    ];
    return analysisKeywords.some(keyword => message.includes(keyword));
  };

  const handleTaskComplete = (result: any) => {
    const resultMessage: Message = {
      id: `result-${Date.now()}`,
      role: 'assistant',
      content: `## 分析报告\n\n${result.summary || '分析已完成'}\n\n### 关键发现\n${result.findings?.map((f: string, i: number) => `${i + 1}. ${f}`).join('\n') || ''}\n\n### 建议\n${result.recommendations?.map((r: string, i: number) => `${i + 1}. ${r}`).join('\n') || ''}`,
      created_at: new Date().toISOString(),
      persona: 'zhouyu',
    };
    setMessages((prev) => [...prev, resultMessage]);
    setShowGovernanceFlow(false);
  };

  const handleTaskError = (error: string) => {
    toast.error(`分析失败: ${error}`);
    setShowGovernanceFlow(false);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* 左侧会话列表 */}
      <div className="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={startNewSession}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
          >
            <PlusIcon className="w-5 h-5" />
            新建会话
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
          {isLoading ? (
            <LoadingCard />
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => loadSessionHistory(session.id)}
                className={`w-full text-left p-3 rounded-lg mb-1 transition-colors ${
                  currentSessionId === session.id
                    ? 'bg-primary-100 dark:bg-primary-900/30'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                <div className="flex items-center gap-2">
                  <ChatBubbleLeftRightIcon className="w-4 h-4 text-gray-400" />
                  <span className="text-sm truncate">
                    {session.id.slice(0, 8)}...
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {new Date(session.created_at).toLocaleDateString()}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col">
        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && !showGovernanceFlow && (
            <div className="text-center py-12">
              <SparklesIcon className="w-12 h-12 text-primary-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                智能房产咨询
              </h2>
              <p className="text-gray-500 mb-4">
                输入您的房产需求，三省六部制系统将为您提供专业分析
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {['深圳南山区学区房', '预算1000万买房', '投资房产推荐'].map((q) => (
                  <button
                    key={q}
                    onClick={() => setInputValue(q)}
                    className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full text-sm hover:bg-gray-200 dark:hover:bg-gray-700"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <CharacterAvatar
                  persona={message.persona || 'zhouyu'}
                  emotion={message.emotion || 'default'}
                  size="sm"
                />
              )}
              <div
                className={`max-w-[70%] rounded-xl p-4 ${
                  message.role === 'user'
                    ? 'bg-primary-500 text-white'
                    : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                }`}
              >
                <ReactMarkdown
                  className={`prose ${
                    message.role === 'user' ? 'prose-invert' : 'dark:prose-invert'
                  } max-w-none`}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
              {message.role === 'user' && (
                <UserCircleIcon className="w-8 h-8 text-gray-400" />
              )}
            </motion.div>
          ))}

          {/* 三省六部制工作流展示 */}
          {showGovernanceFlow && activeTask && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <GovernanceFlow
                currentProvince={activeTask.current_province}
                steps={activeTask.workflow_steps || [
                  { name: 'zhongshu', status: 'pending', progress: 0 },
                  { name: 'menxia', status: 'pending', progress: 0 },
                  { name: 'shangshu', status: 'pending', progress: 0 },
                ]}
                overallProgress={activeTask.progress || 0}
              />
              
              {activeTask.status === 'executing' && (
                <DepartmentStatus
                  departments={activeTask.departments || [
                    { name: 'LIBU', status: 'pending', progress: 0 },
                    { name: 'HUBU', status: 'pending', progress: 0 },
                    { name: 'LIBU_LI', status: 'pending', progress: 0 },
                    { name: 'BINGBU', status: 'pending', progress: 0 },
                    { name: 'XINGBU', status: 'pending', progress: 0 },
                    { name: 'GONGBU', status: 'pending', progress: 0 },
                  ]}
                  activeDepartment={activeTask.current_department}
                />
              )}

              <RealtimeStatus
                taskId={activeTask.task_id}
                onStatusChange={(newStatus) => setActiveTask(prev => ({
                  ...prev!,
                  status: newStatus.status,
                  progress: newStatus.progress,
                  current_province: newStatus.current_province,
                  current_department: newStatus.current_department,
                  workflow_steps: newStatus.workflow_steps
                }))}
                onComplete={handleTaskComplete}
                onError={handleTaskError}
              />
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="输入您的房产问题..."
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
              disabled={isSending}
            />
            <button
              onClick={sendMessage}
              disabled={isSending || !inputValue.trim()}
              className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSending ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                />
              ) : (
                <PaperAirplaneIcon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsultPageNew;
