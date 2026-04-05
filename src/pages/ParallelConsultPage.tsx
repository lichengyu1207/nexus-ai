import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  PlusIcon,
  TrashIcon,
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  XMarkIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../contexts/AuthContext';

interface ParallelSession {
  id: string;
  title: string;
  topic?: string;
  status: string;
  created_at: string;
  last_message_at: string;
  message_count: number;
  preview?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: string;
  created_at: string;
}

interface SessionDetail {
  id: string;
  title: string;
  status: string;
  messages: Message[];
  profile?: Record<string, any>;
}

const API_BASE = '/api/consult/parallel';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const ParallelConsultPage: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [inputValues, setInputValues] = useState<Record<string, string>>({});
  const [isCreating, setIsCreating] = useState(false);
  const messagesEndRefs = useRef<Record<string, HTMLDivElement>>({});

  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ['parallel-sessions'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/sessions`, {
        headers: getAuthHeaders(),
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to fetch sessions');
      return res.json();
    },
    refetchInterval: 5000,
  });

  const { data: activeSession, isLoading: sessionLoading } = useQuery({
    queryKey: ['parallel-session', activeSessionId],
    queryFn: async () => {
      if (!activeSessionId) return null;
      const res = await fetch(`${API_BASE}/sessions/${activeSessionId}`, {
        headers: getAuthHeaders(),
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to fetch session');
      return res.json();
    },
    enabled: !!activeSessionId,
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/sessions`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({ title: `新对话 ${new Date().toLocaleTimeString()}` }),
      });
      if (!res.ok) throw new Error('Failed to create session');
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['parallel-sessions'] });
      setActiveSessionId(data.id);
      setIsCreating(false);
    },
  });

  const sendMessage = async (sessionId: string, content: string) => {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify({ content, session_id: sessionId }),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to send message');
    }
    return res.json();
  };

  const deleteMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to delete session');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['parallel-sessions'] });
      if (activeSessionId) {
        setActiveSessionId(null);
      }
    },
  });

  const handleSend = async (sessionId: string) => {
    const content = inputValues[sessionId]?.trim();
    if (!content) return;

    setInputValues((prev) => ({ ...prev, [sessionId]: '' }));
    
    queryClient.setQueryData(['parallel-session', sessionId], (old: SessionDetail | undefined) => {
      if (!old) return old;
      return {
        ...old,
        messages: [
          ...old.messages,
          { id: 'temp', role: 'user' as const, content, created_at: new Date().toISOString() },
        ],
      };
    });

    try {
      await sendMessage(sessionId, content);
      queryClient.invalidateQueries({ queryKey: ['parallel-session', sessionId] });
      queryClient.invalidateQueries({ queryKey: ['parallel-sessions'] });
    } catch (error: any) {
      console.error('Send message error:', error);
      alert(error.message || '发送失败');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(sessionId);
    }
  };

  const scrollToBottom = (sessionId: string) => {
    messagesEndRefs.current[sessionId]?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeSessionId) {
      scrollToBottom(activeSessionId);
    }
  }, [activeSession, activeSessionId]);

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      <div className="flex justify-between items-center px-6 py-4 bg-white dark:bg-gray-800 border-b dark:border-gray-700">
        <div className="flex items-center gap-2">
          <ChatBubbleLeftRightIcon className="w-6 h-6 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">并行对话</h1>
        </div>
        <button
          onClick={() => createMutation.mutate()}
          disabled={isCreating || createMutation.isPending}
          className="flex items-center gap-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <PlusIcon className="w-4 h-4" />
          新建对话
        </button>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-64 bg-white dark:bg-gray-800 border-r dark:border-gray-700 overflow-y-auto">
          <div className="p-3">
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
              对话列表 ({sessions?.length || 0})
            </h2>
            {sessionsLoading ? (
              <div className="text-center py-4 text-gray-500">加载中...</div>
            ) : sessions && sessions.length > 0 ? (
              <div className="space-y-1">
                {sessions.map((session: ParallelSession) => (
                  <div
                    key={session.id}
                    onClick={() => setActiveSessionId(session.id)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      activeSessionId === session.id
                        ? 'bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {session.title}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {session.message_count} 条消息
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm('确定删除此对话？')) {
                            deleteMutation.mutate(session.id);
                          }
                        }}
                        className="p-1 text-gray-400 hover:text-red-500"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                    {session.preview && (
                      <p className="text-xs text-gray-400 mt-1 truncate">{session.preview}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p>暂无对话</p>
                <p className="text-sm mt-1">点击上方按钮创建新对话</p>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 flex flex-col">
          {activeSession ? (
            <>
              <div className="px-4 py-3 bg-white dark:bg-gray-800 border-b dark:border-gray-700 flex justify-between items-center">
                <h2 className="font-medium text-gray-900 dark:text-white">{activeSession.title}</h2>
                <span className="text-xs text-gray-500">
                  {activeSession.messages?.length || 0} 条消息
                </span>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {activeSession.messages?.map((message: Message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2 ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border dark:border-gray-700'
                      }`}
                    >
                      {message.role === 'assistant' ? (
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={(el) => { if (el) messagesEndRefs.current[activeSession.id] = el; }} />
              </div>

              <div className="p-4 bg-white dark:bg-gray-800 border-t dark:border-gray-700">
                <div className="flex gap-2">
                  <textarea
                    value={inputValues[activeSession.id] || ''}
                    onChange={(e) =>
                      setInputValues((prev) => ({
                        ...prev,
                        [activeSession.id]: e.target.value,
                      }))
                    }
                    onKeyDown={(e) => handleKeyDown(e, activeSession.id)}
                    placeholder="输入消息... (Enter发送, Shift+Enter换行)"
                    className="flex-1 px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white resize-none"
                    rows={2}
                  />
                  <button
                    onClick={() => handleSend(activeSession.id)}
                    disabled={!inputValues[activeSession.id]?.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PaperAirplaneIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <SparklesIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500 dark:text-gray-400">选择或创建一个对话开始咨询</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ParallelConsultPage;
