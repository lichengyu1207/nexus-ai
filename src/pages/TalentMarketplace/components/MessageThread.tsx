import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaperAirplaneIcon, PaperClipIcon } from '@heroicons/react/24/outline';
import type { Message, Conversation } from '../types';

interface MessageThreadProps {
  conversation: Conversation;
  messages: Message[];
  currentUserId: string;
  onSendMessage: (content: string, type?: 'text' | 'file') => void;
  onMarkAsRead?: (messageIds: string[]) => void;
  loading?: boolean;
}

export function MessageThread({
  conversation,
  messages,
  currentUserId,
  onSendMessage,
  onMarkAsRead,
  loading = false,
}: MessageThreadProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    const unreadMessages = messages
      .filter((m) => !m.read && m.senderId !== currentUserId)
      .map((m) => m.id);
    if (unreadMessages.length > 0 && onMarkAsRead) {
      onMarkAsRead(unreadMessages);
    }
  }, [messages, currentUserId, onMarkAsRead]);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    onSendMessage(inputValue.trim());
    setInputValue('');
    inputRef.current?.focus();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
      return '昨天';
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    }
  };

  const groupMessagesByDate = (msgs: Message[]) => {
    const groups: { date: string; messages: Message[] }[] = [];
    let currentDate = '';

    msgs.forEach((msg) => {
      const msgDate = new Date(msg.createdAt).toLocaleDateString('zh-CN');
      if (msgDate !== currentDate) {
        currentDate = msgDate;
        groups.push({ date: msgDate, messages: [msg] });
      } else {
        groups[groups.length - 1].messages.push(msg);
      }
    });

    return groups;
  };

  const messageGroups = groupMessagesByDate(messages);

  return (
    <div className="flex flex-col h-full bg-slate-900/50 backdrop-blur-sm rounded-xl border border-slate-700/50">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white font-bold">
            {conversation.participants.length}
          </div>
          <div>
            <h3 className="text-white font-medium">对话</h3>
            <p className="text-xs text-slate-400">
              {conversation.participants.length} 位参与者
            </p>
          </div>
        </div>
        {conversation.unreadCount > 0 && (
          <span className="px-2 py-1 text-xs bg-amber-500 text-slate-900 rounded-full font-medium">
            {conversation.unreadCount} 条未读
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
          </div>
        ) : (
          <AnimatePresence>
            {messageGroups.map((group) => (
              <div key={group.date}>
                <div className="flex items-center justify-center my-4">
                  <span className="px-3 py-1 text-xs text-slate-500 bg-slate-800/50 rounded-full">
                    {group.date}
                  </span>
                </div>
                
                {group.messages.map((message, index) => {
                  const isOwn = message.senderId === currentUserId;
                  const showAvatar = index === 0 || 
                    group.messages[index - 1].senderId !== message.senderId;

                  return (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-2 mb-2 ${isOwn ? 'flex-row-reverse' : 'flex-row'}`}
                    >
                      {showAvatar ? (
                        <div className={`
                          w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white text-xs font-bold
                          ${isOwn 
                            ? 'bg-gradient-to-br from-amber-500 to-orange-600' 
                            : 'bg-gradient-to-br from-slate-600 to-slate-700'
                          }
                        `}>
                          {message.senderName.slice(0, 2)}
                        </div>
                      ) : (
                        <div className="w-8 flex-shrink-0" />
                      )}
                      
                      <div className={`max-w-[70%] ${isOwn ? 'items-end' : 'items-start'}`}>
                        {showAvatar && (
                          <p className={`text-xs text-slate-400 mb-1 ${isOwn ? 'text-right' : 'text-left'}`}>
                            {isOwn ? '你' : message.senderName}
                          </p>
                        )}
                        <div
                          className={`
                            px-3 py-2 rounded-2xl text-sm
                            ${isOwn
                              ? 'bg-amber-500 text-slate-900 rounded-tr-sm'
                              : 'bg-slate-700/50 text-slate-200 rounded-tl-sm'
                            }
                          `}
                        >
                          {message.type === 'system' ? (
                            <span className="text-slate-400 italic">{message.content}</span>
                          ) : (
                            message.content
                          )}
                        </div>
                        <p className={`text-xs text-slate-500 mt-1 ${isOwn ? 'text-right' : 'text-left'}`}>
                          {formatTime(message.createdAt)}
                        </p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            ))}
          </AnimatePresence>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-slate-700/50">
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="p-2 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-700/50 transition-colors"
            title="添加附件"
          >
            <PaperClipIcon className="w-5 h-5" />
          </motion.button>
          
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入消息..."
              className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 transition-colors"
            />
          </div>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="p-2 rounded-xl bg-amber-500 text-slate-900 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </motion.button>
        </div>
      </div>
    </div>
  );
}
