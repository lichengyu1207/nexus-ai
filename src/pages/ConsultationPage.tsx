import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import CharacterAvatar from '../components/CharacterAvatar';
import MessageBubble from '../components/MessageBubble';
import Dudu from '../components/Dudu';
import { api } from '../services/api';

type PersonaType = 'zhouyu' | 'luxun';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  persona?: PersonaType;
  emotion?: 'default' | 'thinking' | 'happy' | 'serious' | 'surprised';
  timestamp: string;
}

interface ConsultationPageProps {
  sessionId?: string;
}

const PERSONA_CONFIGS = {
  zhouyu: {
    name: '周瑜',
    title: '公瑾',
    style: '儒雅智谋，风度翩翩',
    welcomeMessage: '主公远道而来，瑜备感荣幸。房产之事，虽有千头万绪，但吾已有良策。请卿直言心中所想。',
    colorPrimary: '#1E3A5F',
    colorSecondary: '#D4AF37',
  },
  luxun: {
    name: '陆逊',
    title: '伯言',
    style: '沉稳隐忍，后发制人',
    welcomeMessage: '主公请坐。逊虽不善言辞，但于房市之变，略有心得。愿听主公细说，共商大计。',
    colorPrimary: '#2C5F2D',
    colorSecondary: '#B08D57',
  },
};

export const ConsultationPage: React.FC<ConsultationPageProps> = ({ sessionId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [persona, setPersona] = useState<PersonaType>('zhouyu');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionId || null);
  const [showWelcome, setShowWelcome] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!currentSessionId) {
      startConsultation();
    }
  }, [currentSessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const startConsultation = async () => {
    try {
      setIsLoading(true);
      const response = await api.post('/consult/start');
      const { session_id, persona: assignedPersona, welcome_message } = response.data;
      
      setCurrentSessionId(session_id);
      setPersona(assignedPersona);
      
      if (welcome_message) {
        setMessages([{
          id: 'welcome',
          role: 'assistant',
          content: welcome_message,
          persona: assignedPersona,
          emotion: 'default',
          timestamp: new Date().toLocaleTimeString(),
        }]);
      }
    } catch (error) {
      console.error('Failed to start consultation:', error);
      setPersona(Math.random() > 0.5 ? 'zhouyu' : 'luxun');
      const config = PERSONA_CONFIGS[persona];
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: config.welcomeMessage,
        persona: persona,
        emotion: 'default',
        timestamp: new Date().toLocaleTimeString(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setShowWelcome(false);

    try {
      const response = await api.post('/consult/message', {
        session_id: currentSessionId,
        message: userMessage.content,
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.reply,
        persona: persona,
        emotion: response.data.emotion || 'default',
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，网络有些波动。请稍后再试。',
        persona: persona,
        emotion: 'serious',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const config = PERSONA_CONFIGS[persona];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <motion.div
        className="bg-white shadow-sm border-b px-4 py-3"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        style={{
          background: `linear-gradient(135deg, ${config.colorPrimary}, ${config.colorPrimary}dd)`,
        }}
      >
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CharacterAvatar persona={persona} emotion={isLoading ? 'thinking' : 'default'} size="md" />
            <div className="text-white">
              <h1 className="font-bold text-lg">{config.name} · {config.title}</h1>
              <p className="text-xs opacity-80">{config.style}</p>
            </div>
          </div>
          <div className="text-white text-sm">
            房都督 · 您的AI房产指挥官
          </div>
        </div>
      </motion.div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                role={message.role}
                content={message.content}
                persona={message.persona}
                emotion={message.emotion}
                timestamp={message.timestamp}
              />
            ))}
          </AnimatePresence>
          
          {isLoading && (
            <motion.div
              className="flex items-center space-x-2 text-gray-500 text-sm px-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <CharacterAvatar persona={persona} emotion="thinking" size="sm" />
              <span>{config.name}正在思考...</span>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <motion.div
        className="bg-white border-t px-4 py-4"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="请描述您的房产问题..."
                className="w-full px-4 py-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows={2}
                disabled={isLoading}
              />
            </div>
            <motion.button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="px-6 py-3 bg-primary-600 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              style={{
                background: `linear-gradient(135deg, ${config.colorPrimary}, ${config.colorSecondary})`,
              }}
            >
              发送
            </motion.button>
          </div>
          
          <div className="mt-2 text-xs text-gray-400 text-center">
            按 Enter 发送，Shift + Enter 换行
          </div>
        </div>
      </motion.div>

      {/* Dudu Mascot */}
      <Dudu
        action={isLoading ? 'think' : 'wave'}
        position="bottom-left"
        size="sm"
        message={isLoading ? '都督正在推演中...' : '有嘟嘟，不迷路！'}
      />
    </div>
  );
};

export default ConsultationPage;
