import React, { useState, useEffect, useRef } from 'react';
import AnalysisProgress from '../components/Analysis/AnalysisProgress';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  persona?: string;
  timestamp: Date;
}

interface AnalysisTask {
  id: string;
  status: 'pending' | 'processing' | 'completed';
  progress: number;
  step: string;
  reportSummary?: string;
}

const UnifiedAssistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [analysisTasks, setAnalysisTasks] = useState<Record<string, AnalysisTask>>({});
  const [currentMode, setCurrentMode] = useState<'auto' | 'consult' | 'analyze'>('auto');
  const [sessionId] = useState<string>(() => generateSessionId());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  function generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId]);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(`ws://localhost:8000/api/cabinet/ws/${sessionId}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  };

  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'analysis_progress') {
      setAnalysisTasks(prev => ({
        ...prev,
        [data.task_id]: {
          id: data.task_id,
          status: data.status,
          progress: data.progress,
          step: data.step,
        }
      }));
    } else if (data.type === 'analysis_complete') {
      setAnalysisTasks(prev => ({
        ...prev,
        [data.task_id]: {
          id: data.task_id,
          status: 'completed',
          progress: 100,
          step: '分析完成',
          reportSummary: data.report_summary,
        }
      }));
      
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.report_summary || '分析已完成！',
        timestamp: new Date(),
      }]);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/cabinet/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: sessionId,
          text: userMessage.content,
          mode: currentMode,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        if (data.type === 'consult') {
          const assistantMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: data.content,
            persona: data.emotion,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, assistantMessage]);
        } else if (data.type === 'analyze') {
          setAnalysisTasks(prev => ({
            ...prev,
            [data.task_id]: {
              id: data.task_id,
              status: 'processing',
              progress: 0,
              step: '分析已启动',
            },
          }));
          
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: '🔍 正在为您进行深度分析，请稍候...',
            timestamp: new Date(),
          }]);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (timestamp: Date) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return date.toLocaleDateString('zh-CN');
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user';
    
    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`flex items-start gap-3 max-w-2xl ${isUser ? 'flex-row-reverse' : ''}`}>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white shadow-fluent-sm ${
            isUser 
              ? 'bg-gradient-to-br from-fluent-deepOcean-400 to-fluent-deepOcean-600' 
              : 'bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600'
          }`}>
            <span className="text-xl">{isUser ? '👤' : (message.persona === 'friendly' ? '🤖' : '🤖')}</span>
          </div>
          <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
            <div className={`acrylic rounded-2xl p-4 ${isUser ? 'bg-fluent-deepOcean-100' : 'bg-fluent-gold-50'}`}>
              <p className="text-fluent-deepOcean-500 whitespace-pre-wrap">{message.content}</p>
            </div>
            <p className="text-xs text-fluent-deepOcean-300 mt-1">{formatTime(message.timestamp)}</p>
          </div>
        </div>
      </div>
    );
  };

  const renderAnalysisProgress = (taskId: string, task: AnalysisTask) => {
    const getAnalysisStatus = () => {
      switch (task.status) {
        case 'pending': return 'initializing';
        case 'processing': return 'analyzing';
        case 'completed': return 'completed';
        default: return 'idle';
      }
    };

    return (
      <div key={taskId} className="mb-4">
        <AnalysisProgress
          status={getAnalysisStatus() as any}
          progress={task.progress}
          result={task.status === 'completed' && task.reportSummary ? {
            summary: task.reportSummary
          } : undefined}
          onViewReport={() => {
            window.open(`/virtual-office/${taskId}`, '_blank');
          }}
          showAgents={true}
        />
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-fluent-deepOcean-500 to-fluent-deepOcean-600">
      <div className="acrylic border-b border-white/20 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 flex items-center justify-center text-white shadow-fluent-md">
              <span className="text-xl">🏛️</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">内阁智能中枢</h1>
              <p className="text-sm text-fluent-deepOcean-200">统一咨询与分析入口</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-fluent-deepOcean-200">会话ID: {sessionId.slice(-8)}</span>
          </div>
        </div>
      </div>

      <div ref={messagesEndRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 flex items-center justify-center text-4xl shadow-gold-glow">
              🏛️
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">欢迎使用内阁智能中枢</h2>
            <p className="text-fluent-deepOcean-200 mb-4">我是您的智能助手，可以为您解答房产问题或进行深度分析</p>
            <div className="flex justify-center gap-4">
              <button
                onClick={() => setCurrentMode('consult')}
                className="px-4 py-2 bg-fluent-deepOcean-400/50 text-white rounded-xl hover:bg-fluent-deepOcean-400 transition-colors"
              >
                💬 开始咨询
              </button>
              <button
                onClick={() => setCurrentMode('analyze')}
                className="px-4 py-2 bg-fluent-gold-500 text-fluent-deepOcean-500 rounded-xl hover:bg-fluent-gold-400 transition-colors"
              >
                🔍 深度分析
              </button>
            </div>
          </div>
        )}
        
        {messages.map(message => renderMessage(message))}
        
        {Object.entries(analysisTasks).map(([taskId, task]) => renderAnalysisProgress(taskId, task))}
        
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-fluent-gold-400 to-fluent-gold-600 flex items-center justify-center text-white">
                <span className="text-xl">🤖</span>
              </div>
              <div className="acrylic rounded-2xl p-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-fluent-gold-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-fluent-gold-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-fluent-gold-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-white/20 bg-fluent-deepOcean-400/50">
        <div className="flex gap-2 mb-3">
          <button
            onClick={() => setCurrentMode('auto')}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              currentMode === 'auto' 
                ? 'bg-fluent-gold-500 text-fluent-deepOcean-500' 
                : 'bg-fluent-deepOcean-300/30 text-white hover:bg-fluent-deepOcean-300/50'
            }`}
          >
            🤖 自动模式
          </button>
          <button
            onClick={() => setCurrentMode('consult')}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              currentMode === 'consult' 
                ? 'bg-fluent-gold-500 text-fluent-deepOcean-500' 
                : 'bg-fluent-deepOcean-300/30 text-white hover:bg-fluent-deepOcean-300/50'
            }`}
          >
            💬 智能咨询
          </button>
          <button
            onClick={() => setCurrentMode('analyze')}
            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
              currentMode === 'analyze' 
                ? 'bg-fluent-gold-500 text-fluent-deepOcean-500' 
                : 'bg-fluent-deepOcean-300/30 text-white hover:bg-fluent-deepOcean-300/50'
            }`}
          >
            🔍 深度分析
          </button>
        </div>
        
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                sendMessage();
              }
            }}
            placeholder={
              currentMode === 'consult' 
                ? '输入您的问题，我将为您解答...' 
                : currentMode === 'analyze'
                ? '输入房产地址或小区名称，我将为您深度分析...'
                : '输入您的问题，或点击深度分析按钮触发深度分析...'
            }
            className="flex-1 border-2 border-white/20 rounded-xl px-4 py-3 bg-white/10 text-white placeholder-fluent-deepOcean-200 focus:outline-none focus:border-fluent-gold-400 transition-colors"
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 rounded-xl font-medium hover:shadow-gold-glow transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
};

export default UnifiedAssistant;
