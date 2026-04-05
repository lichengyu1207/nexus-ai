import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
  PaperAirplaneIcon,
  ArrowDownIcon,
  TrashIcon,
  SparklesIcon,
  UserIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';

export type AgentPersona = 'zhouyu' | 'luxun';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  isTyping?: boolean;
  agentUsed?: AgentPersona;
}

interface ChatContainerProps {
  messages: Message[];
  currentAgent: AgentPersona;
  isTyping: boolean;
  onSendMessage: (content: string) => void;
  onClearHistory: () => void;
  onSwitchAgent: (agent: AgentPersona) => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  enableTypewriter?: boolean;
}

const agentConfigs = {
  zhouyu: {
    name: '周瑜',
    title: '战略顾问',
    avatar: '🎭',
    color: 'from-amber-500 to-orange-500',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    borderColor: 'border-amber-200 dark:border-amber-800',
    textColor: 'text-amber-600 dark:text-amber-400',
    description: '擅长战略分析与决策建议',
  },
  luxun: {
    name: '陆逊',
    title: '数据专家',
    avatar: '📊',
    color: 'from-blue-500 to-indigo-500',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-800',
    textColor: 'text-blue-600 dark:text-blue-400',
    description: '擅长数据分析与风险评估',
  },
};

const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  currentAgent,
  isTyping,
  onSendMessage,
  onClearHistory,
  onSwitchAgent,
  onLoadMore,
  hasMore = false,
  enableTypewriter = true,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [showAgentSelector, setShowAgentSelector] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const agentConfig = agentConfigs[currentAgent];

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);

      if (scrollTop === 0 && hasMore) {
        onLoadMore?.();
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [hasMore, onLoadMore]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isTyping) {
      onSendMessage(inputValue.trim());
      setInputValue('');
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const TypewriterContent: React.FC<{ content: string }> = ({ content }) => {
    const [displayedContent, setDisplayedContent] = useState('');
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
      if (!enableTypewriter) {
        setDisplayedContent(content);
        setIsComplete(true);
        return;
      }

      let index = 0;
      const interval = setInterval(() => {
        if (index < content.length) {
          setDisplayedContent(content.slice(0, index + 1));
          index++;
        } else {
          setIsComplete(true);
          clearInterval(interval);
        }
      }, 20);

      return () => clearInterval(interval);
    }, [content, enableTypewriter]);

    return (
      <span>
        {displayedContent}
        {!isComplete && (
          <motion.span
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.5, repeat: Infinity }}
            className="inline-block w-0.5 h-4 bg-current ml-0.5"
          />
        )}
      </span>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      <div className={`flex items-center justify-between p-4 ${agentConfig.bgColor} border-b ${agentConfig.borderColor}`}>
        <div className="flex items-center gap-3">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className={`w-12 h-12 rounded-xl bg-gradient-to-r ${agentConfig.color} flex items-center justify-center text-2xl shadow-lg`}
          >
            {agentConfig.avatar}
          </motion.div>
          <div>
            <h2 className={`font-semibold ${agentConfig.textColor}`}>
              {agentConfig.name}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {agentConfig.description}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowAgentSelector(!showAgentSelector)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${agentConfig.bgColor} border ${agentConfig.borderColor} ${agentConfig.textColor} text-sm`}
            >
              <SparklesIcon className="w-4 h-4" />
              切换智能体
              <ChevronDownIcon className={`w-4 h-4 transition-transform ${showAgentSelector ? 'rotate-180' : ''}`} />
            </motion.button>

            <AnimatePresence>
              {showAgentSelector && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-10"
                >
                  {(Object.keys(agentConfigs) as AgentPersona[]).map((agent) => {
                    const config = agentConfigs[agent];
                    return (
                      <button
                        key={agent}
                        onClick={() => {
                          onSwitchAgent(agent);
                          setShowAgentSelector(false);
                        }}
                        className={`w-full flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                          currentAgent === agent ? 'bg-gray-50 dark:bg-gray-700' : ''
                        }`}
                      >
                        <span className="text-xl">{config.avatar}</span>
                        <div className="text-left">
                          <div className={`font-medium ${config.textColor}`}>{config.name}</div>
                          <div className="text-xs text-gray-500">{config.title}</div>
                        </div>
                      </button>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onClearHistory}
            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            title="清空对话"
          >
            <TrashIcon className="w-5 h-5" />
          </motion.button>
        </div>
      </div>

      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className={`w-20 h-20 rounded-2xl bg-gradient-to-r ${agentConfig.color} flex items-center justify-center text-4xl mb-4 shadow-lg`}
            >
              {agentConfig.avatar}
            </motion.div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              您好，我是{agentConfig.name}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 max-w-md">
              {agentConfig.description}。请输入您想咨询的房产问题，我将为您提供专业的分析建议。
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
                  message.role === 'user'
                    ? 'bg-green-500 text-white'
                    : `bg-gradient-to-r ${agentConfigs[message.agentUsed || currentAgent].color} text-white`
                }`}
              >
                {message.role === 'user' ? (
                  <UserIcon className="w-5 h-5" />
                ) : (
                  <span className="text-lg">{agentConfigs[message.agentUsed || currentAgent].avatar}</span>
                )}
              </div>

              <div
                className={`flex-1 max-w-[80%] ${
                  message.role === 'user' ? 'text-right' : ''
                }`}
              >
                <div
                  className={`inline-block p-4 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-green-500 text-white rounded-tr-none'
                      : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-tl-none shadow-sm border border-gray-100 dark:border-gray-700'
                  }`}
                >
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {message.isTyping ? (
                        <TypewriterContent content={message.content} />
                      ) : (
                        <ReactMarkdown
                          components={{
                            code({ node, inline, className, children, ...props }) {
                              const match = /language-(\w+)/.exec(className || '');
                              return !inline && match ? (
                                <SyntaxHighlighter
                                  style={vscDarkPlus}
                                  language={match[1]}
                                  PreTag="div"
                                  {...props}
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              ) : (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              );
                            },
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      )}
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(message.timestamp).toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </motion.div>
          ))
        )}

        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center bg-gradient-to-r ${agentConfig.color} text-white`}
            >
              <span className="text-lg">{agentConfig.avatar}</span>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-none p-4 shadow-sm border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2">
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="w-2 h-2 rounded-full bg-gray-400"
                />
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                  className="w-2 h-2 rounded-full bg-gray-400"
                />
                <motion.div
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                  className="w-2 h-2 rounded-full bg-gray-400"
                />
                <span className="text-sm text-gray-500 ml-2">正在思考...</span>
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <AnimatePresence>
        {showScrollButton && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={scrollToBottom}
            className="absolute bottom-24 right-6 p-2 bg-white dark:bg-gray-800 rounded-full shadow-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <ArrowDownIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </motion.button>
        )}
      </AnimatePresence>

      <form onSubmit={handleSubmit} className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入您的问题... (Enter发送, Shift+Enter换行)"
              rows={1}
              className="w-full px-4 py-3 bg-gray-100 dark:bg-gray-700 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 dark:text-white placeholder-gray-400"
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            className={`p-3 rounded-xl transition-all ${
              inputValue.trim() && !isTyping
                ? `bg-gradient-to-r ${agentConfig.color} text-white shadow-lg`
                : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
            }`}
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </motion.button>
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          按 Ctrl + K 快速聚焦输入框
        </p>
      </form>
    </div>
  );
};

export default ChatContainer;
